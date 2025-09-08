"""
Upload and file processing routes for ReceiptVision application
Handles single and batch file uploads with OCR processing
"""

import os
import uuid
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from models import Receipt, ExtractedData, BatchJob, db
from services.file_processor import FileProcessor
from services.batch_processor import BatchProcessor
from .utils import allowed_file, get_db, ALLOWED_EXTENSIONS

logger = logging.getLogger(__name__)

# Create upload blueprint
upload_bp = Blueprint('upload', __name__)


@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Upload and process a single file
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({
                'error': f'File type not allowed. Supported types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"

        # Save file
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(upload_path)

        # Get file info
        file_size = os.path.getsize(upload_path)

        # Create receipt record
        receipt = Receipt(
            filename=unique_filename,
            original_filename=original_filename,
            file_type=file_extension,
            file_size=file_size,
            processing_status='pending'
        )

        db = get_db()
        db.session.add(receipt)
        db.session.commit()

        # Process file
        file_processor = FileProcessor()
        processing_result = file_processor.process_file(upload_path, receipt.id)

        # Update receipt with results
        receipt.processing_status = 'completed' if processing_result['success'] else 'failed'
        receipt.confidence_score = processing_result.get('confidence_score', 0.0)
        receipt.processing_time = processing_result.get('processing_time', 0.0)

        if not processing_result['success']:
            receipt.error_message = processing_result.get('error', 'Unknown error')
            get_db().session.commit()
            return jsonify({
                'error': 'Processing failed',
                'message': receipt.error_message,
                'receipt_id': receipt.id
            }), 500

        # Save extracted data
        extracted_data = processing_result['data']
        data_record = ExtractedData(
            receipt_id=receipt.id,
            merchant_name=extracted_data.get('merchant_name'),
            merchant_address=extracted_data.get('merchant_address'),
            merchant_phone=extracted_data.get('merchant_phone'),
            transaction_date=extracted_data.get('transaction_date'),
            transaction_time=extracted_data.get('transaction_time'),
            subtotal=extracted_data.get('subtotal'),
            tax_amount=extracted_data.get('tax_amount'),
            total_amount=extracted_data.get('total_amount'),
            currency=extracted_data.get('currency', 'USD'),
            items=extracted_data.get('items', []),
            raw_text=extracted_data.get('raw_text', ''),
            confidence_scores=extracted_data.get('confidence_scores', {})
        )

        db = get_db()
        db.session.add(data_record)
        db.session.commit()

        # Clean up uploaded file
        try:
            os.remove(upload_path)
        except:
            pass

        return jsonify({
            'success': True,
            'receipt_id': receipt.id,
            'confidence_score': receipt.confidence_score,
            'processing_time': receipt.processing_time,
            'data': data_record.to_dict()
        })

    except RequestEntityTooLarge:
        return jsonify({'error': 'File too large'}), 413
    except Exception as e:
        logger.error(f"Error in file upload: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@upload_bp.route('/batch-upload', methods=['POST'])
def batch_upload():
    """
    Upload and process multiple files
    """
    try:
        # Check if files are present
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400

        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400

        # Validate all files
        valid_files = []
        for file in files:
            if file.filename and allowed_file(file.filename):
                valid_files.append(file)

        if not valid_files:
            return jsonify({
                'error': f'No valid files. Supported types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Create batch job
        job_name = request.form.get('job_name', f'Batch_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}')
        batch_job = BatchJob(
            job_name=job_name,
            total_files=len(valid_files),
            status='pending'
        )

        db = get_db()
        db.session.add(batch_job)
        db.session.commit()

        # Save files and create receipt records
        file_paths = []
        receipt_ids = []

        for file in valid_files:
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            file_extension = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"

            # Save file
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(upload_path)
            file_paths.append(upload_path)

            # Create receipt record
            receipt = Receipt(
                filename=unique_filename,
                original_filename=original_filename,
                file_type=file_extension,
                file_size=os.path.getsize(upload_path),
                processing_status='pending'
            )

            db.session.add(receipt)
            receipt_ids.append(receipt)

        db.session.commit()

        # Start batch processing
        batch_processor = BatchProcessor()
        batch_processor.process_batch_async(
            batch_job.id,
            [(path, receipt.id) for path, receipt in zip(file_paths, receipt_ids)]
        )

        return jsonify({
            'success': True,
            'batch_job_id': batch_job.id,
            'total_files': len(valid_files),
            'message': 'Batch processing started'
        })

    except RequestEntityTooLarge:
        return jsonify({'error': 'Files too large'}), 413
    except Exception as e:
        logger.error(f"Error in batch upload: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

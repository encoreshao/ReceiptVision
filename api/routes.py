"""
API routes for ReceiptVision application
Handles file uploads, OCR processing, and data retrieval
"""

import os
import time
import uuid
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from models import Receipt, ExtractedData, BatchJob, db
from services.file_processor import FileProcessor
from services.batch_processor import BatchProcessor

logger = logging.getLogger(__name__)

def get_db():
    """Get the database instance from the current app"""
    return current_app.extensions['sqlalchemy']

# Create API blueprint
api_bp = Blueprint('api', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })


@api_bp.route('/upload', methods=['POST'])
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


@api_bp.route('/batch-upload', methods=['POST'])
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


@api_bp.route('/receipt/<int:receipt_id>', methods=['GET'])
def get_receipt(receipt_id):
    """Get receipt and extracted data by ID"""
    try:
        receipt = Receipt.query.get_or_404(receipt_id)
        return jsonify(receipt.to_dict())

    except Exception as e:
        logger.error(f"Error getting receipt: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/receipts', methods=['GET'])
def get_receipts():
    """Get all receipts with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        status = request.args.get('status')

        # Debug logging
        logger.info(f"Getting receipts: page={page}, per_page={per_page}, status={status}")

        # Get database instance
        db = get_db()

        query = db.session.query(Receipt)

        if status:
            query = query.filter(Receipt.processing_status == status)

        receipts = query.order_by(Receipt.upload_timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        logger.info(f"Found {receipts.total} receipts, {len(receipts.items)} on this page")

        # Convert to dict with error handling
        receipt_dicts = []
        for receipt in receipts.items:
            try:
                receipt_dict = receipt.to_dict()
                receipt_dicts.append(receipt_dict)
            except Exception as e:
                logger.error(f"Error converting receipt {receipt.id} to dict: {str(e)}")
                # Skip this receipt but continue with others
                continue

        result = {
            'receipts': receipt_dicts,
            'total': receipts.total,
            'pages': receipts.pages,
            'current_page': receipts.page,
            'per_page': receipts.per_page,
            'has_next': receipts.has_next,
            'has_prev': receipts.has_prev
        }

        logger.info(f"Returning {len(receipt_dicts)} receipts")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error getting receipts: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@api_bp.route('/batch-job/<int:job_id>', methods=['GET'])
def get_batch_job(job_id):
    """Get batch job status"""
    try:
        batch_job = BatchJob.query.get_or_404(job_id)
        return jsonify(batch_job.to_dict())

    except Exception as e:
        logger.error(f"Error getting batch job: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/batch-jobs', methods=['GET'])
def get_batch_jobs():
    """Get all batch jobs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)

        batch_jobs = BatchJob.query.order_by(BatchJob.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'batch_jobs': [job.to_dict() for job in batch_jobs.items],
            'total': batch_jobs.total,
            'pages': batch_jobs.pages,
            'current_page': batch_jobs.page,
            'per_page': batch_jobs.per_page,
            'has_next': batch_jobs.has_next,
            'has_prev': batch_jobs.has_prev
        })

    except Exception as e:
        logger.error(f"Error getting batch jobs: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/receipts/<int:receipt_id>', methods=['GET'])
def get_receipt_details(receipt_id):
    """Get detailed information about a specific receipt"""
    try:
        # Get database instance
        db = get_db()

        # Get receipt from database
        receipt = db.session.query(Receipt).get(receipt_id)
        if not receipt:
            return jsonify({'error': 'Receipt not found'}), 404

        # Get extracted data for this receipt
        extracted_data = db.session.query(ExtractedData).filter_by(receipt_id=receipt_id).first()

        # Convert receipt to dict
        receipt_data = receipt.to_dict()

        # Convert extracted data to dict if it exists
        extracted_data_dict = None
        if extracted_data:
            extracted_data_dict = extracted_data.to_dict()
            # Clean up the dict to match frontend expectations
            extracted_data_dict['address'] = extracted_data_dict.get('merchant_address')
            extracted_data_dict['phone_number'] = extracted_data_dict.get('merchant_phone')

        return jsonify({
            'receipt': receipt_data,
            'extracted_data': extracted_data_dict
        })

    except Exception as e:
        logger.error(f"Error getting receipt details: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/receipts/<int:receipt_id>/file', methods=['GET'])
def get_receipt_file(receipt_id):
    """Serve the original receipt file for preview/download"""
    try:
        from flask import send_file

        # Get database instance
        db = get_db()

        # Get receipt from database
        receipt = db.session.query(Receipt).get(receipt_id)
        if not receipt:
            return jsonify({'error': 'Receipt not found'}), 404

        # Build file path
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], receipt.filename)

        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return jsonify({'error': 'File not found'}), 404

        # Determine MIME type based on file extension
        file_extension = receipt.file_type.lower()
        mime_types = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'bmp': 'image/bmp',
            'tiff': 'image/tiff',
            'tif': 'image/tiff'
        }

        mime_type = mime_types.get(file_extension, 'application/octet-stream')

        return send_file(
            file_path,
            mimetype=mime_type,
            as_attachment=False,
            download_name=receipt.original_filename
        )

    except Exception as e:
        logger.error(f"Error serving receipt file: {str(e)}")
        return jsonify({'error': 'File not found'}), 404


@api_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get application statistics"""
    try:
        # Get database instance
        db = get_db()

        # Get receipt statistics
        total_receipts = db.session.query(Receipt).count()
        completed_receipts = db.session.query(Receipt).filter(Receipt.processing_status == 'completed').count()
        failed_receipts = db.session.query(Receipt).filter(Receipt.processing_status == 'failed').count()
        pending_receipts = db.session.query(Receipt).filter(Receipt.processing_status == 'pending').count()

        # Get batch job statistics
        total_batch_jobs = db.session.query(BatchJob).count()

        # Calculate average confidence score (only for completed receipts)
        completed_receipts_query = db.session.query(Receipt).filter(
            Receipt.processing_status == 'completed',
            Receipt.confidence_score.isnot(None)
        )

        confidence_scores = [r.confidence_score for r in completed_receipts_query.all() if r.confidence_score is not None]
        average_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        # Calculate average processing time (only for completed receipts)
        processing_times = [r.processing_time for r in completed_receipts_query.all() if r.processing_time is not None]
        average_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0

        # Get file type distribution
        file_types = {}
        file_type_results = db.session.query(Receipt.file_type, db.func.count(Receipt.id)).group_by(Receipt.file_type).all()
        for file_type, count in file_type_results:
            file_types[file_type.upper()] = count

        # Get recent activity (receipts uploaded in last 7 days)
        from datetime import datetime, timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_receipts = db.session.query(Receipt).filter(Receipt.upload_timestamp >= seven_days_ago).count()

        # Get total file size processed
        total_file_size = db.session.query(db.func.sum(Receipt.file_size)).scalar() or 0

        # Get success rate
        success_rate = (completed_receipts / total_receipts * 100) if total_receipts > 0 else 0

        # Get most common merchant (from extracted data)
        merchant_stats = db.session.query(
            ExtractedData.merchant_name,
            db.func.count(ExtractedData.id)
        ).filter(
            ExtractedData.merchant_name.isnot(None),
            ExtractedData.merchant_name != ''
        ).group_by(ExtractedData.merchant_name).order_by(
            db.func.count(ExtractedData.id).desc()
        ).first()

        top_merchant = merchant_stats[0] if merchant_stats else None

        stats = {
            'total_receipts': total_receipts,
            'completed_receipts': completed_receipts,
            'failed_receipts': failed_receipts,
            'pending_receipts': pending_receipts,
            'total_batch_jobs': total_batch_jobs,
            'average_confidence': round(average_confidence, 3),
            'average_processing_time': round(average_processing_time, 3),
            'file_types': file_types,
            'recent_receipts': recent_receipts,
            'total_file_size': total_file_size,
            'success_rate': round(success_rate, 1),
            'top_merchant': top_merchant
        }

        logger.info(f"Statistics calculated: {stats}")
        return jsonify(stats)

    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Resource not found'}), 404


@api_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

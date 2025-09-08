"""
Receipt management routes for ReceiptVision application
Handles receipt retrieval, details, and file serving
"""

import os
import logging
from flask import Blueprint, request, jsonify, current_app, send_file

from models import Receipt, ExtractedData, db
from .utils import get_db

logger = logging.getLogger(__name__)

# Create receipt blueprint
receipt_bp = Blueprint('receipts', __name__)


@receipt_bp.route('/receipt/<int:receipt_id>', methods=['GET'])
def get_receipt(receipt_id):
    """Get receipt and extracted data by ID"""
    try:
        receipt = Receipt.query.get_or_404(receipt_id)
        return jsonify(receipt.to_dict())

    except Exception as e:
        logger.error(f"Error getting receipt: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@receipt_bp.route('/receipts', methods=['GET'])
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


@receipt_bp.route('/receipts/<int:receipt_id>', methods=['GET'])
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


@receipt_bp.route('/receipts/<int:receipt_id>/file', methods=['GET'])
def get_receipt_file(receipt_id):
    """Serve the original receipt file for preview/download"""
    try:
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

"""
System and statistics routes for ReceiptVision application
Handles health checks and application statistics
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, jsonify

from models import Receipt, ExtractedData, BatchJob, db
from .utils import get_db

logger = logging.getLogger(__name__)

# Create system blueprint
system_bp = Blueprint('system', __name__)


@system_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })


@system_bp.route('/statistics', methods=['GET'])
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

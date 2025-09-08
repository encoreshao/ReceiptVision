"""
Batch job management routes for ReceiptVision application
Handles batch job status and listing
"""

import logging
from flask import Blueprint, request, jsonify

from models import BatchJob
from .utils import get_db

logger = logging.getLogger(__name__)

# Create batch blueprint
batch_bp = Blueprint('batch', __name__)


@batch_bp.route('/batch-job/<int:job_id>', methods=['GET'])
def get_batch_job(job_id):
    """Get batch job status"""
    try:
        batch_job = BatchJob.query.get_or_404(job_id)
        return jsonify(batch_job.to_dict())

    except Exception as e:
        logger.error(f"Error getting batch job: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@batch_bp.route('/batch-jobs', methods=['GET'])
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

"""
Web routes for serving the frontend application
"""

from flask import Blueprint, render_template, send_from_directory
import os

# Create web blueprint
web_bp = Blueprint('web', __name__)


@web_bp.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')


@web_bp.route('/upload')
def upload_page():
    """Serve the upload page"""
    return render_template('upload.html')


@web_bp.route('/batch')
def batch_page():
    """Serve the batch processing page"""
    return render_template('batch.html')


@web_bp.route('/receipts')
def receipts_page():
    """Serve the receipts list page"""
    return render_template('receipts.html')


@web_bp.route('/receipt/<int:receipt_id>')
def receipt_detail_page(receipt_id):
    """Serve the receipt detail page"""
    return render_template('receipt_detail.html', receipt_id=receipt_id)


@web_bp.route('/statistics')
def statistics_page():
    """Serve the statistics page"""
    return render_template('statistics.html')


# Static file serving
@web_bp.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

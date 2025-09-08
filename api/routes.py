"""
Main API routes module for ReceiptVision application
Imports and registers all resource-specific blueprints
"""

import logging
from flask import Blueprint, jsonify

# Import resource-specific blueprints from blueprints package
from .blueprints import upload_bp, receipt_bp, batch_bp, system_bp

logger = logging.getLogger(__name__)

# Create main API blueprint
api_bp = Blueprint('api', __name__)

# Register sub-blueprints
api_bp.register_blueprint(upload_bp)
api_bp.register_blueprint(receipt_bp)
api_bp.register_blueprint(batch_bp)
api_bp.register_blueprint(system_bp)


@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Resource not found'}), 404


@api_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

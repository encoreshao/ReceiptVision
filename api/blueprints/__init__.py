"""
Blueprints package for ReceiptVision API
Contains all route blueprints organized by resource
"""

from .upload_routes import upload_bp
from .receipt_routes import receipt_bp
from .batch_routes import batch_bp
from .system_routes import system_bp

__all__ = ['upload_bp', 'receipt_bp', 'batch_bp', 'system_bp']

"""
Database models for ReceiptVision application
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON, Boolean
from app import db

# Export db for use in other modules
__all__ = ['db', 'Receipt', 'ExtractedData', 'BatchJob']


class Receipt(db.Model):
    """Model for storing receipt/invoice metadata"""
    __tablename__ = 'receipts'

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, jpg, png, etc.
    file_size = Column(Integer, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    processing_status = Column(String(20), default='pending')  # pending, processing, completed, failed
    confidence_score = Column(Float, default=0.0)
    processing_time = Column(Float, default=0.0)  # in seconds
    error_message = Column(Text, nullable=True)

    # Relationship to extracted data
    extracted_data = db.relationship('ExtractedData', backref='receipt', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'upload_timestamp': self.upload_timestamp.isoformat() if self.upload_timestamp else None,
            'processing_status': self.processing_status,
            'confidence_score': self.confidence_score,
            'processing_time': self.processing_time,
            'error_message': self.error_message,
            'extracted_data': [data.to_dict() for data in self.extracted_data]
        }


class ExtractedData(db.Model):
    """Model for storing extracted OCR data"""
    __tablename__ = 'extracted_data'

    id = Column(Integer, primary_key=True)
    receipt_id = Column(Integer, db.ForeignKey('receipts.id'), nullable=False)

    # Merchant Information
    merchant_name = Column(String(255), nullable=True)
    merchant_address = Column(Text, nullable=True)
    merchant_phone = Column(String(50), nullable=True)

    # Transaction Information
    transaction_date = Column(DateTime, nullable=True)
    transaction_time = Column(String(20), nullable=True)

    # Financial Information
    subtotal = Column(Float, nullable=True)
    tax_amount = Column(Float, nullable=True)
    total_amount = Column(Float, nullable=True)
    currency = Column(String(10), default='USD')

    # Items (stored as JSON array)
    items = Column(JSON, nullable=True)  # [{"name": "item", "price": 10.99, "quantity": 1}]

    # Additional extracted text
    raw_text = Column(Text, nullable=True)

    # Confidence scores for different fields
    confidence_scores = Column(JSON, nullable=True)  # {"merchant_name": 0.95, "total": 0.88, ...}

    # Metadata
    extraction_timestamp = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'receipt_id': self.receipt_id,
            'merchant_name': self.merchant_name,
            'merchant_address': self.merchant_address,
            'merchant_phone': self.merchant_phone,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'transaction_time': self.transaction_time,
            'subtotal': self.subtotal,
            'tax_amount': self.tax_amount,
            'total_amount': self.total_amount,
            'currency': self.currency,
            'items': self.items,
            'raw_text': self.raw_text,
            'confidence_scores': self.confidence_scores,
            'extraction_timestamp': self.extraction_timestamp.isoformat() if self.extraction_timestamp else None
        }


class BatchJob(db.Model):
    """Model for tracking batch processing jobs"""
    __tablename__ = 'batch_jobs'

    id = Column(Integer, primary_key=True)
    job_name = Column(String(255), nullable=False)
    total_files = Column(Integer, nullable=False)
    processed_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    status = Column(String(20), default='pending')  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'job_name': self.job_name,
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'failed_files': self.failed_files,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress_percentage': (self.processed_files / self.total_files * 100) if self.total_files > 0 else 0
        }

"""
Tests for database models
"""
import pytest
from datetime import datetime
from models import db, Receipt, ExtractedData, BatchJob


def test_receipt_model_creation(app):
    """Test creating a Receipt model instance."""
    with app.app_context():
        receipt = Receipt(
            filename='test_receipt.jpg',
            file_type='jpg',
            file_size=1024,
            processing_status='pending'
        )

        db.session.add(receipt)
        db.session.commit()

        assert receipt.id is not None
        assert receipt.filename == 'test_receipt.jpg'
        assert receipt.file_type == 'jpg'
        assert receipt.file_size == 1024
        assert receipt.processing_status == 'pending'
        assert receipt.upload_timestamp is not None


def test_receipt_to_dict(app):
    """Test Receipt model to_dict method."""
    with app.app_context():
        receipt = Receipt(
            filename='test_receipt.jpg',
            file_type='jpg',
            file_size=1024,
            processing_status='completed',
            confidence_score=0.95,
            processing_time=2.5
        )

        db.session.add(receipt)
        db.session.commit()

        receipt_dict = receipt.to_dict()

        assert isinstance(receipt_dict, dict)
        assert receipt_dict['filename'] == 'test_receipt.jpg'
        assert receipt_dict['file_type'] == 'jpg'
        assert receipt_dict['file_size'] == 1024
        assert receipt_dict['processing_status'] == 'completed'
        assert receipt_dict['confidence_score'] == 0.95
        assert receipt_dict['processing_time'] == 2.5
        assert 'id' in receipt_dict
        assert 'upload_timestamp' in receipt_dict


def test_extracted_data_model_creation(app):
    """Test creating an ExtractedData model instance."""
    with app.app_context():
        # First create a receipt
        receipt = Receipt(
            filename='test_receipt.jpg',
            file_type='jpg',
            file_size=1024,
            processing_status='completed'
        )
        db.session.add(receipt)
        db.session.commit()

        # Then create extracted data
        extracted_data = ExtractedData(
            receipt_id=receipt.id,
            merchant_name='Test Store',
            total_amount=25.99,
            transaction_date=datetime.now().date(),
            raw_text='Test receipt content'
        )

        db.session.add(extracted_data)
        db.session.commit()

        assert extracted_data.id is not None
        assert extracted_data.receipt_id == receipt.id
        assert extracted_data.merchant_name == 'Test Store'
        assert extracted_data.total_amount == 25.99
        assert extracted_data.raw_text == 'Test receipt content'


def test_extracted_data_to_dict(app):
    """Test ExtractedData model to_dict method."""
    with app.app_context():
        # Create receipt first
        receipt = Receipt(
            filename='test_receipt.jpg',
            file_type='jpg',
            file_size=1024,
            processing_status='completed'
        )
        db.session.add(receipt)
        db.session.commit()

        # Create extracted data
        extracted_data = ExtractedData(
            receipt_id=receipt.id,
            merchant_name='Test Store',
            total_amount=25.99,
            subtotal=23.99,
            tax_amount=2.00,
            transaction_date=datetime.now().date(),
            phone_number='555-1234',
            address='123 Test St',
            raw_text='Test receipt content'
        )

        db.session.add(extracted_data)
        db.session.commit()

        data_dict = extracted_data.to_dict()

        assert isinstance(data_dict, dict)
        assert data_dict['merchant_name'] == 'Test Store'
        assert data_dict['total_amount'] == 25.99
        assert data_dict['subtotal'] == 23.99
        assert data_dict['tax_amount'] == 2.00
        assert data_dict['phone_number'] == '555-1234'
        assert data_dict['address'] == '123 Test St'
        assert 'id' in data_dict
        assert 'receipt_id' in data_dict


def test_batch_job_model_creation(app):
    """Test creating a BatchJob model instance."""
    with app.app_context():
        batch_job = BatchJob(
            job_name='Test Batch Job',
            status='pending',
            total_files=5
        )

        db.session.add(batch_job)
        db.session.commit()

        assert batch_job.id is not None
        assert batch_job.job_name == 'Test Batch Job'
        assert batch_job.status == 'pending'
        assert batch_job.total_files == 5
        assert batch_job.processed_files == 0
        assert batch_job.created_at is not None


def test_batch_job_to_dict(app):
    """Test BatchJob model to_dict method."""
    with app.app_context():
        batch_job = BatchJob(
            job_name='Test Batch Job',
            status='completed',
            total_files=5,
            processed_files=5,
            failed_files=0
        )

        db.session.add(batch_job)
        db.session.commit()

        job_dict = batch_job.to_dict()

        assert isinstance(job_dict, dict)
        assert job_dict['job_name'] == 'Test Batch Job'
        assert job_dict['status'] == 'completed'
        assert job_dict['total_files'] == 5
        assert job_dict['processed_files'] == 5
        assert job_dict['failed_files'] == 0
        assert 'id' in job_dict
        assert 'created_at' in job_dict


def test_receipt_relationship_with_extracted_data(app):
    """Test the relationship between Receipt and ExtractedData."""
    with app.app_context():
        # Create receipt
        receipt = Receipt(
            filename='test_receipt.jpg',
            file_type='jpg',
            file_size=1024,
            processing_status='completed'
        )
        db.session.add(receipt)
        db.session.commit()

        # Create extracted data
        extracted_data = ExtractedData(
            receipt_id=receipt.id,
            merchant_name='Test Store',
            total_amount=25.99
        )
        db.session.add(extracted_data)
        db.session.commit()

        # Test relationship
        assert len(receipt.extracted_data) == 1
        assert receipt.extracted_data[0].merchant_name == 'Test Store'
        assert extracted_data.receipt == receipt

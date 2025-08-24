"""
Tests for the main Flask application
"""
import pytest
from app import create_app


def test_app_creation():
    """Test that the app can be created successfully."""
    app = create_app()
    assert app is not None
    assert app.config['TESTING'] is False


def test_app_config():
    """Test app configuration."""
    app = create_app()
    assert 'SECRET_KEY' in app.config
    assert 'SQLALCHEMY_DATABASE_URI' in app.config


def test_home_page(client):
    """Test the home page loads successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'ReceiptVision' in response.data


def test_upload_page(client):
    """Test the upload page loads successfully."""
    response = client.get('/upload')
    assert response.status_code == 200
    assert b'upload' in response.data.lower()


def test_receipts_page(client):
    """Test the receipts page loads successfully."""
    response = client.get('/receipts')
    assert response.status_code == 200


def test_statistics_page(client):
    """Test the statistics page loads successfully."""
    response = client.get('/statistics')
    assert response.status_code == 200


def test_batch_page(client):
    """Test the batch processing page loads successfully."""
    response = client.get('/batch')
    assert response.status_code == 200


def test_404_error(client):
    """Test 404 error handling."""
    response = client.get('/nonexistent-page')
    assert response.status_code == 404

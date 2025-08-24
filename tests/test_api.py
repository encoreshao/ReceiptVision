"""
Tests for API endpoints
"""
import pytest
import json
import io
from models import Receipt, ExtractedData, db


def test_api_statistics(client):
    """Test the statistics API endpoint."""
    response = client.get('/api/v1/statistics')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert 'total_receipts' in data
    assert 'completed_receipts' in data
    assert 'failed_receipts' in data
    assert 'pending_receipts' in data
    assert 'average_confidence' in data
    assert 'file_types' in data

    # Check data types
    assert isinstance(data['total_receipts'], int)
    assert isinstance(data['completed_receipts'], int)
    assert isinstance(data['average_confidence'], (int, float))
    assert isinstance(data['file_types'], dict)


def test_api_receipts_list(client):
    """Test the receipts list API endpoint."""
    response = client.get('/api/v1/receipts')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert 'receipts' in data
    assert 'pagination' in data
    assert isinstance(data['receipts'], list)


def test_api_receipts_pagination(client):
    """Test receipts API pagination."""
    response = client.get('/api/v1/receipts?page=1&per_page=10')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert 'pagination' in data
    pagination = data['pagination']
    assert 'page' in pagination
    assert 'per_page' in pagination
    assert 'total' in pagination


def test_api_upload_no_file(client):
    """Test upload API without file."""
    response = client.post('/api/v1/upload')
    assert response.status_code == 400

    data = json.loads(response.data)
    assert 'error' in data


def test_api_upload_invalid_file_type(client):
    """Test upload API with invalid file type."""
    data = {
        'file': (io.BytesIO(b'test content'), 'test.txt')
    }
    response = client.post('/api/v1/upload', data=data)
    assert response.status_code == 400

    response_data = json.loads(response.data)
    assert 'error' in response_data


def test_api_receipt_not_found(client):
    """Test getting a non-existent receipt."""
    response = client.get('/api/v1/receipts/99999')
    assert response.status_code == 404

    data = json.loads(response.data)
    assert 'error' in data


def test_api_receipt_file_not_found(client):
    """Test getting file for non-existent receipt."""
    response = client.get('/api/v1/receipts/99999/file')
    assert response.status_code == 404

"""
Pytest configuration and fixtures for ReceiptVision tests
"""
import pytest
import tempfile
import os
from app import create_app
from models import db


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to serve as the database
    db_fd, db_path = tempfile.mkstemp()

    # Create app with test configuration
    app = create_app()
    app.config.update({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{db_path}",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key"
    })

    # Create the database and the database table
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

    # Clean up
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

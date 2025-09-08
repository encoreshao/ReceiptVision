"""
Shared utilities for API routes
Contains common helper functions and constants
"""

from flask import current_app

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    """Get the database instance from the current app"""
    return current_app.extensions['sqlalchemy']

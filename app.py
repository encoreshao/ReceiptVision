"""
ReceiptVision - OCR Application for Bank Invoices and Consumer Receipts
Main Flask application entry point
"""

import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

    # Try PostgreSQL first, fallback to SQLite for development
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        # Use SQLite as fallback for development
        database_url = 'sqlite:///receiptvision.db'
        print("📝 Using SQLite database for development (receiptvision.db)")

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Configure CORS
    cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    CORS(app, origins=cors_origins)

    # Register blueprints
    from api.routes import api_bp
    from web.routes import web_bp

    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(web_bp)

    # Import models to ensure they're registered
    from models import Receipt, ExtractedData

    return app


if __name__ == '__main__':
    app = create_app()

    # Initialize database tables
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created successfully")
        except Exception as e:
            print(f"⚠️  Database initialization warning: {e}")

    print(f"🚀 Starting ReceiptVision server at http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)

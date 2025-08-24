"""
Database initialization script for ReceiptVision
Creates all necessary tables and indexes
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import sys

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models import Receipt, ExtractedData, BatchJob


def init_database():
    """Initialize the database with all tables"""
    # Use the same database configuration as the main app
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        print(f"📝 Using configured database: {database_url.split('@')[0]}@***")
    else:
        print("📝 No DATABASE_URL found, using SQLite for development")
        os.environ['DATABASE_URL'] = 'sqlite:///receiptvision.db'

    app = create_app()

    with app.app_context():
        # Create all tables
        db.create_all()

        # Create indexes for better performance
        try:
            with db.engine.connect() as conn:
                # Index on receipt processing status
                conn.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_receipts_status
                    ON receipts(processing_status);
                """))

                # Index on receipt upload timestamp
                conn.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_receipts_timestamp
                    ON receipts(upload_timestamp DESC);
                """))

                # Index on receipt file type
                conn.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_receipts_file_type
                    ON receipts(file_type);
                """))

                # Index on extracted data receipt_id (foreign key)
                conn.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_extracted_data_receipt_id
                    ON extracted_data(receipt_id);
                """))

                # Index on extracted data merchant name for searching
                conn.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_extracted_data_merchant
                    ON extracted_data(merchant_name);
                """))

                # Index on extracted data transaction date
                conn.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_extracted_data_date
                    ON extracted_data(transaction_date);
                """))

                # Index on batch job status
                conn.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_batch_jobs_status
                    ON batch_jobs(status);
                """))

                # Index on batch job created_at
                conn.execute(db.text("""
                    CREATE INDEX IF NOT EXISTS idx_batch_jobs_created
                    ON batch_jobs(created_at DESC);
                """))

                conn.commit()

            print("✅ Database tables and indexes created successfully!")

        except Exception as e:
            print(f"⚠️  Warning: Could not create some indexes: {e}")
            print("This is normal if indexes already exist.")

        # Print table information
        print("\n📊 Database Schema:")
        print("=" * 50)

        # Get table info using SQLAlchemy inspector
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        with db.engine.connect() as conn:
            for table in tables:
                try:
                    result = conn.execute(db.text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    print(f"  {table}: {count} records")
                except Exception as e:
                    print(f"  {table}: Could not count records ({e})")

        print("\n🎉 Database initialization complete!")
        print("\nNext steps:")
        print("1. Start the Flask application: python app.py")
        print("2. Visit http://localhost:5001 to use the application")
        print("3. Upload receipts and test the OCR functionality")


if __name__ == "__main__":
    init_database()

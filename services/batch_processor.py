"""
Batch processing service for handling multiple files
"""

import os
import time
import logging
import threading
from typing import List, Tuple, Dict, Any
from datetime import datetime

from flask import current_app
from app import db
from models import Receipt, ExtractedData, BatchJob
from services.file_processor import FileProcessor

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Service for batch processing multiple files"""

    def __init__(self):
        self.file_processor = FileProcessor()
        self.active_jobs = {}  # Track active batch jobs

    def process_batch_async(self, batch_job_id: int, file_data: List[Tuple[str, int]]):
        """
        Start batch processing in a separate thread

        Args:
            batch_job_id (int): ID of the batch job
            file_data (List[Tuple[str, int]]): List of (file_path, receipt_id) tuples
        """
        thread = threading.Thread(
            target=self._process_batch_sync,
            args=(batch_job_id, file_data),
            daemon=True
        )
        thread.start()

        self.active_jobs[batch_job_id] = {
            'thread': thread,
            'start_time': time.time(),
            'status': 'processing'
        }

        logger.info(f"Started batch processing for job {batch_job_id} with {len(file_data)} files")

    def _process_batch_sync(self, batch_job_id: int, file_data: List[Tuple[str, int]]):
        """
        Process batch of files synchronously

        Args:
            batch_job_id (int): ID of the batch job
            file_data (List[Tuple[str, int]]): List of (file_path, receipt_id) tuples
        """
        try:
            # Update job status
            batch_job = BatchJob.query.get(batch_job_id)
            if not batch_job:
                logger.error(f"Batch job {batch_job_id} not found")
                return

            batch_job.status = 'processing'
            db.session.commit()

            processed_count = 0
            failed_count = 0

            for file_path, receipt_id in file_data:
                try:
                    # Process individual file
                    result = self.file_processor.process_file(file_path, receipt_id)

                    # Update receipt record
                    receipt = Receipt.query.get(receipt_id)
                    if receipt:
                        if result['success']:
                            receipt.processing_status = 'completed'
                            receipt.confidence_score = result.get('confidence_score', 0.0)
                            receipt.processing_time = result.get('processing_time', 0.0)

                            # Save extracted data
                            extracted_data = result['data']
                            data_record = ExtractedData(
                                receipt_id=receipt.id,
                                merchant_name=extracted_data.get('merchant_name'),
                                merchant_address=extracted_data.get('merchant_address'),
                                merchant_phone=extracted_data.get('merchant_phone'),
                                transaction_date=extracted_data.get('transaction_date'),
                                transaction_time=extracted_data.get('transaction_time'),
                                subtotal=extracted_data.get('subtotal'),
                                tax_amount=extracted_data.get('tax_amount'),
                                total_amount=extracted_data.get('total_amount'),
                                currency=extracted_data.get('currency', 'USD'),
                                items=extracted_data.get('items', []),
                                raw_text=extracted_data.get('raw_text', ''),
                                confidence_scores=extracted_data.get('confidence_scores', {})
                            )
                            db.session.add(data_record)
                            processed_count += 1

                        else:
                            receipt.processing_status = 'failed'
                            receipt.error_message = result.get('error', 'Unknown error')
                            failed_count += 1

                        db.session.commit()

                    # Clean up file
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except Exception as cleanup_error:
                        logger.warning(f"Could not remove file {file_path}: {cleanup_error}")

                    # Update batch job progress
                    batch_job.processed_files = processed_count
                    batch_job.failed_files = failed_count
                    db.session.commit()

                    logger.info(f"Batch job {batch_job_id}: processed {processed_count + failed_count}/{len(file_data)} files")

                except Exception as file_error:
                    logger.error(f"Error processing file {file_path}: {str(file_error)}")
                    failed_count += 1

                    # Update receipt as failed
                    receipt = Receipt.query.get(receipt_id)
                    if receipt:
                        receipt.processing_status = 'failed'
                        receipt.error_message = str(file_error)
                        db.session.commit()

                    # Update batch job
                    batch_job.failed_files = failed_count
                    db.session.commit()

            # Complete batch job
            batch_job.status = 'completed'
            batch_job.completed_at = datetime.utcnow()
            batch_job.processed_files = processed_count
            batch_job.failed_files = failed_count
            db.session.commit()

            # Update active jobs tracking
            if batch_job_id in self.active_jobs:
                self.active_jobs[batch_job_id]['status'] = 'completed'

            logger.info(f"Batch job {batch_job_id} completed: {processed_count} successful, {failed_count} failed")

        except Exception as e:
            logger.error(f"Error in batch processing job {batch_job_id}: {str(e)}")

            # Mark job as failed
            try:
                batch_job = BatchJob.query.get(batch_job_id)
                if batch_job:
                    batch_job.status = 'failed'
                    db.session.commit()

                if batch_job_id in self.active_jobs:
                    self.active_jobs[batch_job_id]['status'] = 'failed'

            except Exception as db_error:
                logger.error(f"Error updating failed batch job: {str(db_error)}")

    def get_job_status(self, batch_job_id: int) -> Dict[str, Any]:
        """
        Get status of a batch job

        Args:
            batch_job_id (int): ID of the batch job

        Returns:
            Dict containing job status information
        """
        try:
            batch_job = BatchJob.query.get(batch_job_id)
            if not batch_job:
                return {'error': 'Batch job not found'}

            status_data = batch_job.to_dict()

            # Add runtime information if job is active
            if batch_job_id in self.active_jobs:
                job_info = self.active_jobs[batch_job_id]
                status_data['runtime_seconds'] = time.time() - job_info['start_time']
                status_data['thread_alive'] = job_info['thread'].is_alive()

            return status_data

        except Exception as e:
            logger.error(f"Error getting batch job status: {str(e)}")
            return {'error': str(e)}

    def cancel_job(self, batch_job_id: int) -> Dict[str, Any]:
        """
        Cancel a running batch job

        Args:
            batch_job_id (int): ID of the batch job to cancel

        Returns:
            Dict containing cancellation result
        """
        try:
            batch_job = BatchJob.query.get(batch_job_id)
            if not batch_job:
                return {'error': 'Batch job not found'}

            if batch_job.status not in ['pending', 'processing']:
                return {'error': 'Job cannot be cancelled (not running)'}

            # Update database status
            batch_job.status = 'cancelled'
            batch_job.completed_at = datetime.utcnow()
            db.session.commit()

            # Update active jobs tracking
            if batch_job_id in self.active_jobs:
                self.active_jobs[batch_job_id]['status'] = 'cancelled'

            logger.info(f"Batch job {batch_job_id} cancelled")
            return {'success': True, 'message': 'Job cancelled successfully'}

        except Exception as e:
            logger.error(f"Error cancelling batch job: {str(e)}")
            return {'error': str(e)}

    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """
        Clean up tracking data for old completed jobs

        Args:
            max_age_hours (int): Maximum age in hours for keeping job data
        """
        try:
            current_time = time.time()
            jobs_to_remove = []

            for job_id, job_info in self.active_jobs.items():
                job_age_hours = (current_time - job_info['start_time']) / 3600

                if (job_age_hours > max_age_hours and
                    job_info['status'] in ['completed', 'failed', 'cancelled']):
                    jobs_to_remove.append(job_id)

            for job_id in jobs_to_remove:
                del self.active_jobs[job_id]
                logger.debug(f"Cleaned up tracking data for job {job_id}")

        except Exception as e:
            logger.error(f"Error cleaning up completed jobs: {str(e)}")

    def get_active_jobs_summary(self) -> Dict[str, Any]:
        """Get summary of all active jobs"""
        try:
            summary = {
                'total_active_jobs': len(self.active_jobs),
                'jobs_by_status': {},
                'jobs': []
            }

            for job_id, job_info in self.active_jobs.items():
                status = job_info['status']
                summary['jobs_by_status'][status] = summary['jobs_by_status'].get(status, 0) + 1

                summary['jobs'].append({
                    'job_id': job_id,
                    'status': status,
                    'runtime_seconds': time.time() - job_info['start_time'],
                    'thread_alive': job_info['thread'].is_alive()
                })

            return summary

        except Exception as e:
            logger.error(f"Error getting active jobs summary: {str(e)}")
            return {'error': str(e)}

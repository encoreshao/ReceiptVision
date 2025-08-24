"""
File processing service for handling different file types
"""

import os
import time
import logging
from typing import Dict, Any, List
from PIL import Image

from ocr.ocr_engine import OCREngine
from ocr.pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)


class FileProcessor:
    """Service for processing uploaded files"""

    def __init__(self):
        self.ocr_engine = OCREngine()
        self.pdf_processor = PDFProcessor()

        # Supported file types
        self.image_extensions = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif'}
        self.pdf_extensions = {'pdf'}

    def process_file(self, file_path: str, receipt_id: int) -> Dict[str, Any]:
        """
        Process a single file and extract receipt data

        Args:
            file_path (str): Path to the uploaded file
            receipt_id (int): Database ID of the receipt record

        Returns:
            Dict containing processing results
        """
        start_time = time.time()

        try:
            logger.info(f"Processing file: {file_path}")

            # Determine file type
            file_extension = os.path.splitext(file_path)[1].lower().lstrip('.')

            if file_extension in self.image_extensions:
                result = self._process_image_file(file_path)
            elif file_extension in self.pdf_extensions:
                result = self._process_pdf_file(file_path)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported file type: {file_extension}',
                    'processing_time': time.time() - start_time
                }

            # Add processing metadata
            result['processing_time'] = time.time() - start_time
            result['file_type'] = file_extension
            result['receipt_id'] = receipt_id

            logger.info(f"File processing completed in {result['processing_time']:.2f}s")
            return result

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time,
                'receipt_id': receipt_id
            }

    def _process_image_file(self, image_path: str) -> Dict[str, Any]:
        """Process image file using OCR"""
        try:
            # Validate image
            if not self._validate_image(image_path):
                return {
                    'success': False,
                    'error': 'Invalid or corrupted image file'
                }

            # Process with OCR engine
            ocr_result = self.ocr_engine.process_image(image_path, 'image')

            return {
                'success': True,
                'data': ocr_result,
                'confidence_score': ocr_result.get('overall_confidence', 0.0),
                'pages_processed': 1
            }

        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return {
                'success': False,
                'error': f'Image processing error: {str(e)}'
            }

    def _process_pdf_file(self, pdf_path: str) -> Dict[str, Any]:
        """Process PDF file"""
        try:
            # Get PDF information
            pdf_info = self.pdf_processor.get_pdf_info(pdf_path)

            if 'error' in pdf_info:
                return {
                    'success': False,
                    'error': f'PDF processing error: {pdf_info["error"]}'
                }

            # Process PDF pages
            pages_data = self.pdf_processor.process_pdf(pdf_path)

            if not pages_data:
                return {
                    'success': False,
                    'error': 'Could not extract any data from PDF'
                }

            # Process each page and combine results
            combined_result = self._combine_pdf_results(pages_data)

            # Clean up temporary files
            self.pdf_processor.cleanup_temp_files()

            return {
                'success': True,
                'data': combined_result,
                'confidence_score': combined_result.get('overall_confidence', 0.0),
                'pages_processed': len(pages_data),
                'pdf_info': pdf_info
            }

        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            # Clean up on error
            self.pdf_processor.cleanup_temp_files()
            return {
                'success': False,
                'error': f'PDF processing error: {str(e)}'
            }

    def _combine_pdf_results(self, pages_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine OCR results from multiple PDF pages"""
        try:
            combined_data = {
                'merchant_name': None,
                'merchant_address': None,
                'merchant_phone': None,
                'transaction_date': None,
                'transaction_time': None,
                'subtotal': None,
                'tax_amount': None,
                'total_amount': None,
                'currency': 'USD',
                'items': [],
                'raw_text': '',
                'confidence_scores': {},
                'overall_confidence': 0.0,
                'processing_notes': [],
                'pages_data': []
            }

            page_confidences = []

            for page_data in pages_data:
                page_result = None

                # Process page with OCR if it has an image
                if page_data.get('image_path'):
                    page_result = self.ocr_engine.process_image(
                        page_data['image_path'], 'pdf_page'
                    )
                    page_confidences.append(page_result.get('overall_confidence', 0.0))

                # Use direct text if available and OCR failed
                elif page_data.get('text_content'):
                    # Parse text directly
                    page_result = self.ocr_engine._parse_receipt_data(page_data['text_content'])
                    page_result['raw_text'] = page_data['text_content']
                    page_result['overall_confidence'] = 0.7  # Lower confidence for direct text
                    page_confidences.append(0.7)

                if page_result:
                    # Combine data from this page
                    self._merge_page_data(combined_data, page_result)
                    combined_data['pages_data'].append({
                        'page_number': page_data['page_number'],
                        'confidence': page_result.get('overall_confidence', 0.0),
                        'data': page_result
                    })

            # Calculate overall confidence
            if page_confidences:
                combined_data['overall_confidence'] = sum(page_confidences) / len(page_confidences)

            # Combine raw text
            combined_data['raw_text'] = '\n\n'.join([
                page.get('data', {}).get('raw_text', '')
                for page in combined_data['pages_data']
            ])

            return combined_data

        except Exception as e:
            logger.error(f"Error combining PDF results: {str(e)}")
            return {
                'merchant_name': None,
                'merchant_address': None,
                'merchant_phone': None,
                'transaction_date': None,
                'transaction_time': None,
                'subtotal': None,
                'tax_amount': None,
                'total_amount': None,
                'currency': 'USD',
                'items': [],
                'raw_text': '',
                'confidence_scores': {},
                'overall_confidence': 0.0,
                'processing_notes': [f'Error combining results: {str(e)}']
            }

    def _merge_page_data(self, combined_data: Dict[str, Any], page_data: Dict[str, Any]):
        """Merge data from a single page into combined results"""
        # Merge fields, preferring non-null values with higher confidence

        # Merchant information
        if page_data.get('merchant_name') and not combined_data.get('merchant_name'):
            combined_data['merchant_name'] = page_data['merchant_name']

        if page_data.get('merchant_address') and not combined_data.get('merchant_address'):
            combined_data['merchant_address'] = page_data['merchant_address']

        if page_data.get('merchant_phone') and not combined_data.get('merchant_phone'):
            combined_data['merchant_phone'] = page_data['merchant_phone']

        # Transaction information
        if page_data.get('transaction_date') and not combined_data.get('transaction_date'):
            combined_data['transaction_date'] = page_data['transaction_date']

        if page_data.get('transaction_time') and not combined_data.get('transaction_time'):
            combined_data['transaction_time'] = page_data['transaction_time']

        # Financial information (prefer higher amounts for totals)
        if page_data.get('total_amount'):
            if not combined_data.get('total_amount') or page_data['total_amount'] > combined_data['total_amount']:
                combined_data['total_amount'] = page_data['total_amount']

        if page_data.get('subtotal'):
            if not combined_data.get('subtotal') or page_data['subtotal'] > combined_data['subtotal']:
                combined_data['subtotal'] = page_data['subtotal']

        if page_data.get('tax_amount'):
            if not combined_data.get('tax_amount'):
                combined_data['tax_amount'] = page_data['tax_amount']

        # Currency
        if page_data.get('currency') and page_data['currency'] != 'USD':
            combined_data['currency'] = page_data['currency']

        # Items (combine all items)
        if page_data.get('items'):
            combined_data['items'].extend(page_data['items'])

        # Processing notes
        if page_data.get('processing_notes'):
            combined_data['processing_notes'].extend(page_data['processing_notes'])

    def _validate_image(self, image_path: str) -> bool:
        """Validate that the image file is readable"""
        try:
            with Image.open(image_path) as img:
                img.verify()  # Verify image integrity
            return True
        except Exception as e:
            logger.error(f"Image validation failed: {str(e)}")
            return False

    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get list of supported file formats"""
        return {
            'images': list(self.image_extensions),
            'documents': list(self.pdf_extensions),
            'all': list(self.image_extensions | self.pdf_extensions)
        }

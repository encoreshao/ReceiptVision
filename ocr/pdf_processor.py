"""
PDF processing module for extracting images and text from PDF files
"""

import os
import logging
from typing import List, Dict, Any
from pdf2image import convert_from_path
import PyPDF2
import pdfplumber
from PIL import Image
import tempfile

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handle PDF file processing and conversion"""

    def __init__(self):
        self.temp_files = []

    def process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Process PDF file and extract images/text

        Args:
            pdf_path (str): Path to PDF file

        Returns:
            List of dictionaries containing page data
        """
        try:
            logger.info(f"Processing PDF: {pdf_path}")

            # First try to extract text directly
            text_pages = self._extract_text_from_pdf(pdf_path)

            # Convert PDF pages to images
            image_pages = self._convert_pdf_to_images(pdf_path)

            # Combine text and image data
            pages_data = []
            max_pages = max(len(text_pages), len(image_pages))

            for i in range(max_pages):
                page_data = {
                    'page_number': i + 1,
                    'text_content': text_pages[i] if i < len(text_pages) else '',
                    'image_path': image_pages[i] if i < len(image_pages) else None,
                    'has_text': bool(text_pages[i] if i < len(text_pages) else False),
                    'has_image': bool(image_pages[i] if i < len(image_pages) else False)
                }
                pages_data.append(page_data)

            logger.info(f"Processed {len(pages_data)} pages from PDF")
            return pages_data

        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            return []

    def _extract_text_from_pdf(self, pdf_path: str) -> List[str]:
        """Extract text from PDF using multiple methods"""
        text_pages = []

        # Method 1: Try pdfplumber (better for complex layouts)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    text_pages.append(text or '')

            if any(text.strip() for text in text_pages):
                logger.debug(f"Extracted text from {len(text_pages)} pages using pdfplumber")
                return text_pages

        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {str(e)}")

        # Method 2: Try PyPDF2 as fallback
        try:
            text_pages = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    text_pages.append(text or '')

            logger.debug(f"Extracted text from {len(text_pages)} pages using PyPDF2")
            return text_pages

        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {str(e)}")
            return []

    def _convert_pdf_to_images(self, pdf_path: str, dpi: int = 300) -> List[str]:
        """Convert PDF pages to images"""
        image_paths = []

        try:
            # Convert PDF to images
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                fmt='PNG',
                thread_count=2
            )

            # Save images to temporary files
            for i, image in enumerate(images):
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(
                    suffix=f'_page_{i+1}.png',
                    delete=False,
                    dir=tempfile.gettempdir()
                )
                temp_path = temp_file.name
                temp_file.close()

                # Save image
                image.save(temp_path, 'PNG')
                image_paths.append(temp_path)
                self.temp_files.append(temp_path)

                logger.debug(f"Converted page {i+1} to image: {temp_path}")

            return image_paths

        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}")
            return []

    def get_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """Get PDF metadata and information"""
        try:
            info = {
                'file_size': os.path.getsize(pdf_path),
                'num_pages': 0,
                'has_text': False,
                'metadata': {}
            }

            # Get page count and metadata
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                info['num_pages'] = len(pdf_reader.pages)

                # Get metadata
                if pdf_reader.metadata:
                    info['metadata'] = {
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'creator': pdf_reader.metadata.get('/Creator', ''),
                        'producer': pdf_reader.metadata.get('/Producer', ''),
                        'creation_date': pdf_reader.metadata.get('/CreationDate', ''),
                        'modification_date': pdf_reader.metadata.get('/ModDate', '')
                    }

                # Check if PDF has extractable text
                for page in pdf_reader.pages:
                    if page.extract_text().strip():
                        info['has_text'] = True
                        break

            return info

        except Exception as e:
            logger.error(f"Error getting PDF info: {str(e)}")
            return {'error': str(e)}

    def optimize_pdf_for_ocr(self, pdf_path: str) -> str:
        """Optimize PDF for better OCR results"""
        try:
            # For now, we'll just return the original path
            # In the future, we could implement PDF optimization like:
            # - Increase DPI for conversion
            # - Apply image preprocessing to each page
            # - Remove backgrounds
            # - Enhance contrast

            return pdf_path

        except Exception as e:
            logger.error(f"Error optimizing PDF: {str(e)}")
            return pdf_path

    def cleanup_temp_files(self):
        """Clean up temporary files created during processing"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Could not remove temp file {temp_file}: {str(e)}")

        self.temp_files.clear()

    def __del__(self):
        """Cleanup on destruction"""
        self.cleanup_temp_files()

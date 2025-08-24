"""
Main OCR Engine for receipt and invoice processing
Handles text extraction, data parsing, and confidence scoring
"""

import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import pytesseract
import cv2
import numpy as np
from PIL import Image
from dateutil import parser as date_parser
from fuzzywuzzy import fuzz

from .image_processor import ImageProcessor

logger = logging.getLogger(__name__)


class OCREngine:
    """Main OCR processing engine"""

    def __init__(self, tesseract_cmd=None):
        """Initialize OCR engine"""
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        self.image_processor = ImageProcessor()

        # Common merchant patterns
        self.merchant_patterns = [
            r'(?i)(?:store|shop|market|restaurant|cafe|bar|pub|hotel|gas|station|pharmacy|bank)',
            r'(?i)(?:walmart|target|costco|amazon|starbucks|mcdonalds|subway|cvs|walgreens)',
            r'(?i)(?:inc|llc|corp|ltd|co\.|company|enterprises|group)'
        ]

        # Currency patterns
        self.currency_patterns = {
            'USD': [r'\$', r'USD', r'US\$', r'DOLLAR'],
            'EUR': [r'€', r'EUR', r'EURO'],
            'GBP': [r'£', r'GBP', r'POUND'],
            'CAD': [r'CAD', r'C\$'],
        }

        # Common receipt keywords
        self.receipt_keywords = {
            'total': ['total', 'amount due', 'balance due', 'grand total', 'final total'],
            'subtotal': ['subtotal', 'sub total', 'sub-total', 'amount'],
            'tax': ['tax', 'vat', 'gst', 'hst', 'sales tax', 'state tax'],
            'date': ['date', 'time', 'transaction date', 'purchase date'],
            'phone': ['phone', 'tel', 'telephone', 'call', 'contact'],
            'address': ['address', 'street', 'ave', 'avenue', 'road', 'rd', 'blvd', 'boulevard']
        }

    def process_image(self, image_path: str, file_type: str = 'image') -> Dict[str, Any]:
        """
        Process image and extract receipt data

        Args:
            image_path (str): Path to image file
            file_type (str): Type of file (image, pdf)

        Returns:
            Dict containing extracted data and confidence scores
        """
        try:
            logger.info(f"Processing {file_type}: {image_path}")

            # Load and preprocess image
            processed_image = self.image_processor.preprocess_image(image_path)

            # Apply deskewing
            processed_image = self.image_processor.deskew_image(processed_image)

            # Extract text using OCR
            raw_text = self._extract_text(processed_image)

            if not raw_text.strip():
                logger.warning("No text extracted from image")
                return self._create_empty_result("No text could be extracted from the image")

            # Parse extracted data
            extracted_data = self._parse_receipt_data(raw_text)

            # Calculate confidence scores
            confidence_scores = self._calculate_confidence_scores(extracted_data, raw_text)

            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(confidence_scores)

            result = {
                'merchant_name': extracted_data.get('merchant_name'),
                'merchant_address': extracted_data.get('merchant_address'),
                'merchant_phone': extracted_data.get('merchant_phone'),
                'transaction_date': extracted_data.get('transaction_date'),
                'transaction_time': extracted_data.get('transaction_time'),
                'subtotal': extracted_data.get('subtotal'),
                'tax_amount': extracted_data.get('tax_amount'),
                'total_amount': extracted_data.get('total_amount'),
                'currency': extracted_data.get('currency', 'USD'),
                'items': extracted_data.get('items', []),
                'raw_text': raw_text,
                'confidence_scores': confidence_scores,
                'overall_confidence': overall_confidence,
                'processing_notes': extracted_data.get('processing_notes', [])
            }

            logger.info(f"Processing completed with confidence: {overall_confidence:.3f}")
            return result

        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return self._create_empty_result(f"Processing error: {str(e)}")

    def _extract_text(self, image: np.ndarray) -> str:
        """Extract text from preprocessed image using Tesseract"""
        try:
            # Configure Tesseract for better receipt recognition
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,()/$%@#&*-+= '

            # Extract text
            text = pytesseract.image_to_string(image, config=custom_config)

            # Also try with different PSM modes for better results
            psm_modes = [6, 8, 11, 13]  # Different page segmentation modes
            texts = [text]

            for psm in psm_modes[1:]:  # Skip first one as we already have it
                try:
                    config = f'--oem 3 --psm {psm}'
                    alt_text = pytesseract.image_to_string(image, config=config)
                    if len(alt_text.strip()) > len(text.strip()):
                        texts.append(alt_text)
                except:
                    continue

            # Use the longest extracted text
            final_text = max(texts, key=len) if texts else text

            logger.debug(f"Extracted {len(final_text)} characters of text")
            return final_text

        except Exception as e:
            logger.error(f"Error in text extraction: {str(e)}")
            return ""

    def _parse_receipt_data(self, text: str) -> Dict[str, Any]:
        """Parse receipt data from extracted text"""
        try:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            data = {
                'processing_notes': []
            }

            # Extract merchant information
            data.update(self._extract_merchant_info(lines))

            # Extract financial information
            data.update(self._extract_financial_info(lines))

            # Extract date and time
            data.update(self._extract_datetime_info(lines))

            # Extract items
            data['items'] = self._extract_items(lines)

            # Extract contact information
            data.update(self._extract_contact_info(lines))

            return data

        except Exception as e:
            logger.error(f"Error parsing receipt data: {str(e)}")
            return {'processing_notes': [f"Parsing error: {str(e)}"]}

    def _extract_merchant_info(self, lines: List[str]) -> Dict[str, Any]:
        """Extract merchant name and address"""
        merchant_data = {}

        # Look for merchant name (usually in first few lines)
        for i, line in enumerate(lines[:5]):
            # Skip lines that look like addresses or phone numbers
            if re.search(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', line):  # Phone pattern
                continue
            if re.search(r'\d+\s+\w+\s+(st|street|ave|avenue|rd|road|blvd|boulevard)', line, re.I):
                continue

            # Look for business indicators
            if any(re.search(pattern, line) for pattern in self.merchant_patterns):
                merchant_data['merchant_name'] = line
                break

            # If line has mostly letters and is substantial, could be merchant name
            if len(line) > 3 and len(re.findall(r'[a-zA-Z]', line)) / len(line) > 0.7:
                if not merchant_data.get('merchant_name'):
                    merchant_data['merchant_name'] = line

        # Look for address
        address_lines = []
        for line in lines:
            # Address patterns
            if re.search(r'\d+\s+\w+\s+(st|street|ave|avenue|rd|road|blvd|boulevard|ln|lane|dr|drive|way|ct|court|pl|place)', line, re.I):
                address_lines.append(line)
            elif re.search(r'\w+,\s*[A-Z]{2}\s+\d{5}', line):  # City, State ZIP
                address_lines.append(line)

        if address_lines:
            merchant_data['merchant_address'] = ' '.join(address_lines)

        return merchant_data

    def _extract_financial_info(self, lines: List[str]) -> Dict[str, Any]:
        """Extract financial information (totals, tax, etc.)"""
        financial_data = {}

        # Currency detection
        currency = 'USD'  # Default
        for curr, patterns in self.currency_patterns.items():
            if any(re.search(pattern, ' '.join(lines), re.I) for pattern in patterns):
                currency = curr
                break
        financial_data['currency'] = currency

        # Extract amounts
        for line in lines:
            line_lower = line.lower()

            # Look for total amount
            if any(keyword in line_lower for keyword in self.receipt_keywords['total']):
                amount = self._extract_amount(line)
                if amount:
                    financial_data['total_amount'] = amount

            # Look for subtotal
            elif any(keyword in line_lower for keyword in self.receipt_keywords['subtotal']):
                amount = self._extract_amount(line)
                if amount:
                    financial_data['subtotal'] = amount

            # Look for tax
            elif any(keyword in line_lower for keyword in self.receipt_keywords['tax']):
                amount = self._extract_amount(line)
                if amount:
                    financial_data['tax_amount'] = amount

        return financial_data

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract monetary amount from text"""
        # Pattern for amounts: $12.34, 12.34, $12,34, etc.
        patterns = [
            r'[\$€£]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)[\$€£]?',
            r'(\d+\.\d{2})',
            r'(\d+,\d{2})'  # European format
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    # Clean and convert
                    amount_str = matches[-1]  # Take last match (usually the amount)
                    amount_str = amount_str.replace(',', '.')  # Handle European format
                    amount_str = re.sub(r'[^\d.]', '', amount_str)
                    return float(amount_str)
                except ValueError:
                    continue

        return None

    def _extract_datetime_info(self, lines: List[str]) -> Dict[str, Any]:
        """Extract date and time information"""
        datetime_data = {}

        for line in lines:
            # Look for date patterns
            date_patterns = [
                r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
                r'\d{2,4}[-/]\d{1,2}[-/]\d{1,2}',
                r'[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{2,4}',
                r'\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}'
            ]

            for pattern in date_patterns:
                matches = re.findall(pattern, line)
                if matches:
                    try:
                        parsed_date = date_parser.parse(matches[0], fuzzy=True)
                        datetime_data['transaction_date'] = parsed_date
                        break
                    except:
                        continue

            # Look for time patterns
            time_patterns = [
                r'\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?',
                r'\d{1,2}:\d{2}(?::\d{2})?'
            ]

            for pattern in time_patterns:
                matches = re.findall(pattern, line)
                if matches:
                    datetime_data['transaction_time'] = matches[0]
                    break

        return datetime_data

    def _extract_items(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract individual items from receipt"""
        items = []

        # Look for item patterns
        for line in lines:
            # Skip header/footer lines
            if any(keyword in line.lower() for keyword in ['total', 'subtotal', 'tax', 'change', 'cash', 'card']):
                continue

            # Look for item with price pattern
            # Pattern: Item name ... price
            item_pattern = r'^(.+?)\s+[\$€£]?\s*(\d+\.\d{2})$'
            match = re.match(item_pattern, line.strip())

            if match:
                item_name = match.group(1).strip()
                price = float(match.group(2))

                # Filter out non-item lines
                if len(item_name) > 2 and not re.search(r'^\d+$', item_name):
                    items.append({
                        'name': item_name,
                        'price': price,
                        'quantity': 1  # Default quantity
                    })

            # Alternative pattern: Quantity x Item ... price
            qty_pattern = r'^(\d+)\s*x?\s*(.+?)\s+[\$€£]?\s*(\d+\.\d{2})$'
            match = re.match(qty_pattern, line.strip())

            if match:
                quantity = int(match.group(1))
                item_name = match.group(2).strip()
                price = float(match.group(3))

                items.append({
                    'name': item_name,
                    'price': price,
                    'quantity': quantity
                })

        return items

    def _extract_contact_info(self, lines: List[str]) -> Dict[str, Any]:
        """Extract phone numbers and other contact info"""
        contact_data = {}

        for line in lines:
            # Phone number patterns
            phone_patterns = [
                r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',
                r'\((\d{3})\)\s*(\d{3})[-.\s]?(\d{4})',
                r'(\d{10})'
            ]

            for pattern in phone_patterns:
                matches = re.findall(pattern, line)
                if matches:
                    if isinstance(matches[0], tuple):
                        phone = ''.join(matches[0])
                    else:
                        phone = matches[0]

                    # Format phone number
                    phone = re.sub(r'[^\d]', '', phone)
                    if len(phone) == 10:
                        formatted_phone = f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
                        contact_data['merchant_phone'] = formatted_phone
                        break

        return contact_data

    def _calculate_confidence_scores(self, extracted_data: Dict[str, Any], raw_text: str) -> Dict[str, float]:
        """Calculate confidence scores for extracted fields"""
        scores = {}

        # Merchant name confidence
        if extracted_data.get('merchant_name'):
            # Higher confidence if contains business indicators
            business_indicators = sum(1 for pattern in self.merchant_patterns
                                    if re.search(pattern, extracted_data['merchant_name'], re.I))
            scores['merchant_name'] = min(0.9, 0.5 + business_indicators * 0.2)
        else:
            scores['merchant_name'] = 0.0

        # Financial data confidence
        for field in ['total_amount', 'subtotal', 'tax_amount']:
            if extracted_data.get(field):
                # Higher confidence if amount is reasonable and properly formatted
                amount = extracted_data[field]
                if 0.01 <= amount <= 10000:  # Reasonable range
                    scores[field] = 0.8
                else:
                    scores[field] = 0.6
            else:
                scores[field] = 0.0

        # Date confidence
        if extracted_data.get('transaction_date'):
            scores['transaction_date'] = 0.8
        else:
            scores['transaction_date'] = 0.0

        # Phone confidence
        if extracted_data.get('merchant_phone'):
            phone = re.sub(r'[^\d]', '', extracted_data['merchant_phone'])
            if len(phone) == 10:
                scores['merchant_phone'] = 0.9
            else:
                scores['merchant_phone'] = 0.5
        else:
            scores['merchant_phone'] = 0.0

        # Items confidence
        items = extracted_data.get('items', [])
        if items:
            # Confidence based on number of items and price validity
            valid_items = sum(1 for item in items if item.get('price', 0) > 0)
            scores['items'] = min(0.9, valid_items / len(items) * 0.8)
        else:
            scores['items'] = 0.0

        # Text quality confidence
        if raw_text:
            # Based on text length and character variety
            text_length = len(raw_text.strip())
            char_variety = len(set(raw_text.lower())) / len(raw_text) if raw_text else 0
            scores['text_quality'] = min(0.9, (text_length / 500) * 0.5 + char_variety * 0.4)
        else:
            scores['text_quality'] = 0.0

        return scores

    def _calculate_overall_confidence(self, confidence_scores: Dict[str, float]) -> float:
        """Calculate overall confidence score"""
        if not confidence_scores:
            return 0.0

        # Weighted average of confidence scores
        weights = {
            'merchant_name': 0.2,
            'total_amount': 0.25,
            'transaction_date': 0.15,
            'items': 0.2,
            'text_quality': 0.1,
            'merchant_phone': 0.1
        }

        weighted_sum = 0.0
        total_weight = 0.0

        for field, weight in weights.items():
            if field in confidence_scores:
                weighted_sum += confidence_scores[field] * weight
                total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _create_empty_result(self, error_message: str) -> Dict[str, Any]:
        """Create empty result with error message"""
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
            'processing_notes': [error_message]
        }

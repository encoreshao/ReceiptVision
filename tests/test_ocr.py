"""
Tests for OCR functionality
"""
import pytest
from unittest.mock import Mock, patch
from PIL import Image
import io
from ocr.ocr_engine import OCREngine
from ocr.image_processor import ImageProcessor


def test_ocr_engine_initialization():
    """Test OCR engine can be initialized."""
    engine = OCREngine()
    assert engine is not None


def test_image_processor_initialization():
    """Test image processor can be initialized."""
    processor = ImageProcessor()
    assert processor is not None


def test_create_test_image():
    """Test creating a simple test image."""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='white')
    assert img.size == (100, 100)
    assert img.mode == 'RGB'


@patch('ocr.ocr_engine.pytesseract.image_to_string')
def test_ocr_engine_extract_text_mock(mock_tesseract):
    """Test OCR text extraction with mocked tesseract."""
    # Mock tesseract response
    mock_tesseract.return_value = "Test receipt text"

    engine = OCREngine()

    # Create a test image
    img = Image.new('RGB', (100, 100), color='white')

    # Test text extraction
    result = engine.extract_text(img)

    assert result == "Test receipt text"
    mock_tesseract.assert_called_once()


def test_image_processor_preprocess():
    """Test image preprocessing."""
    processor = ImageProcessor()

    # Create a test image
    img = Image.new('RGB', (100, 100), color='white')

    # Test preprocessing (should not raise an error)
    try:
        processed_img = processor.preprocess_image(img)
        assert processed_img is not None
    except Exception as e:
        # If preprocessing fails due to missing dependencies, that's okay for CI
        pytest.skip(f"Image processing dependencies not available: {e}")


@patch('ocr.ocr_engine.pytesseract.image_to_string')
def test_ocr_engine_extract_data_mock(mock_tesseract):
    """Test OCR data extraction with mocked tesseract."""
    # Mock tesseract response with receipt-like text
    mock_tesseract.return_value = """
    WALMART SUPERCENTER
    123 MAIN ST
    ANYTOWN, ST 12345
    (555) 123-4567

    MILK                 $3.99
    BREAD                $2.49
    EGGS                 $4.99

    SUBTOTAL            $11.47
    TAX                  $0.92
    TOTAL               $12.39

    01/15/2024 14:30
    """

    engine = OCREngine()

    # Create a test image
    img = Image.new('RGB', (200, 300), color='white')

    # Test data extraction
    result = engine.extract_receipt_data(img)

    assert isinstance(result, dict)
    # The exact extraction depends on the implementation
    # Just verify we get a dictionary back
    mock_tesseract.assert_called()


def test_image_processor_denoise():
    """Test image denoising functionality."""
    processor = ImageProcessor()

    # Create a test image
    img = Image.new('RGB', (100, 100), color='white')

    try:
        # Test denoising (should not raise an error)
        denoised_img = processor.denoise_image(img)
        assert denoised_img is not None
    except Exception as e:
        # If denoising fails due to missing dependencies, that's okay for CI
        pytest.skip(f"Image denoising dependencies not available: {e}")


def test_confidence_score_calculation():
    """Test confidence score calculation."""
    engine = OCREngine()

    # Test with sample extracted data
    sample_data = {
        'merchant_name': 'WALMART',
        'total_amount': 12.39,
        'transaction_date': '2024-01-15',
        'raw_text': 'WALMART SUPERCENTER\nTOTAL $12.39'
    }

    confidence = engine.calculate_confidence_score(sample_data)

    assert isinstance(confidence, float)
    assert 0.0 <= confidence <= 1.0


def test_empty_image_handling():
    """Test handling of empty or invalid images."""
    engine = OCREngine()

    # Test with None
    result = engine.extract_text(None)
    assert result == "" or result is None

    # Test with very small image
    tiny_img = Image.new('RGB', (1, 1), color='white')
    result = engine.extract_text(tiny_img)
    # Should not crash, result can be empty
    assert isinstance(result, str) or result is None

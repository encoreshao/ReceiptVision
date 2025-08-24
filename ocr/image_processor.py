"""
Advanced image processing module for OCR optimization
Includes denoising, adaptive thresholding, and morphological operations
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from skimage import filters, morphology, restoration
from skimage.morphology import disk
import logging

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Advanced image processing for OCR optimization"""

    def __init__(self):
        self.processed_images = []

    def preprocess_image(self, image_path, enhance_contrast=True, denoise=True,
                        adaptive_threshold=True, morphological_ops=True):
        """
        Comprehensive image preprocessing pipeline

        Args:
            image_path (str): Path to the image file
            enhance_contrast (bool): Apply contrast enhancement
            denoise (bool): Apply denoising
            adaptive_threshold (bool): Apply adaptive thresholding
            morphological_ops (bool): Apply morphological operations

        Returns:
            np.ndarray: Processed image array
        """
        try:
            # Load image
            if isinstance(image_path, str):
                image = cv2.imread(image_path)
                if image is None:
                    # Try with PIL for other formats
                    pil_image = Image.open(image_path)
                    image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            else:
                image = image_path

            logger.info(f"Processing image with shape: {image.shape}")

            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Step 1: Contrast enhancement
            if enhance_contrast:
                gray = self._enhance_contrast(gray)

            # Step 2: Denoising
            if denoise:
                gray = self._denoise_image(gray)

            # Step 3: Adaptive thresholding
            if adaptive_threshold:
                gray = self._adaptive_threshold(gray)

            # Step 4: Morphological operations
            if morphological_ops:
                gray = self._morphological_operations(gray)

            return gray

        except Exception as e:
            logger.error(f"Error in image preprocessing: {str(e)}")
            raise

    def _enhance_contrast(self, image):
        """Apply contrast enhancement using CLAHE"""
        try:
            # Create CLAHE object (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(image)

            # Additional contrast enhancement
            alpha = 1.2  # Contrast control (1.0-3.0)
            beta = 10    # Brightness control (0-100)
            enhanced = cv2.convertScaleAbs(enhanced, alpha=alpha, beta=beta)

            logger.debug("Applied contrast enhancement")
            return enhanced

        except Exception as e:
            logger.error(f"Error in contrast enhancement: {str(e)}")
            return image

    def _denoise_image(self, image):
        """Apply multiple denoising techniques"""
        try:
            # Method 1: Non-local means denoising
            denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)

            # Method 2: Gaussian blur for additional smoothing
            denoised = cv2.GaussianBlur(denoised, (3, 3), 0)

            # Method 3: Bilateral filter to preserve edges
            denoised = cv2.bilateralFilter(denoised, 9, 75, 75)

            logger.debug("Applied denoising")
            return denoised

        except Exception as e:
            logger.error(f"Error in denoising: {str(e)}")
            return image

    def _adaptive_threshold(self, image):
        """Apply adaptive thresholding for better text extraction"""
        try:
            # Method 1: Adaptive threshold with Gaussian
            thresh1 = cv2.adaptiveThreshold(
                image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )

            # Method 2: Adaptive threshold with mean
            thresh2 = cv2.adaptiveThreshold(
                image, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY, 11, 2
            )

            # Method 3: Otsu's thresholding
            _, thresh3 = cv2.threshold(
                image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

            # Combine thresholding methods
            combined = cv2.bitwise_and(thresh1, thresh2)
            combined = cv2.bitwise_or(combined, thresh3)

            logger.debug("Applied adaptive thresholding")
            return combined

        except Exception as e:
            logger.error(f"Error in adaptive thresholding: {str(e)}")
            return image

    def _morphological_operations(self, image):
        """Apply morphological operations for text cleanup"""
        try:
            # Define kernels
            kernel_rect = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            kernel_ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

            # Opening (erosion followed by dilation) - removes noise
            opened = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel_rect)

            # Closing (dilation followed by erosion) - fills gaps
            closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_ellipse)

            # Remove small noise with area opening
            # Convert to binary if not already
            if len(np.unique(closed)) > 2:
                _, closed = cv2.threshold(closed, 127, 255, cv2.THRESH_BINARY)

            # Additional cleanup for text
            # Remove small connected components
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
                closed, connectivity=8
            )

            # Filter out small components
            min_area = 10  # Minimum area for text components
            cleaned = np.zeros_like(closed)

            for i in range(1, num_labels):
                if stats[i, cv2.CC_STAT_AREA] >= min_area:
                    cleaned[labels == i] = 255

            logger.debug("Applied morphological operations")
            return cleaned

        except Exception as e:
            logger.error(f"Error in morphological operations: {str(e)}")
            return image

    def deskew_image(self, image):
        """Detect and correct image skew"""
        try:
            # Find all white pixels
            coords = np.column_stack(np.where(image > 0))

            # Find minimum area rectangle
            rect = cv2.minAreaRect(coords)
            angle = rect[2]

            # Correct angle
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle

            # Rotate image
            if abs(angle) > 0.5:  # Only rotate if significant skew
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(
                    image, M, (w, h), flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )
                logger.debug(f"Corrected skew by {angle:.2f} degrees")
                return rotated

            return image

        except Exception as e:
            logger.error(f"Error in deskewing: {str(e)}")
            return image

    def enhance_text_regions(self, image):
        """Enhance text regions specifically"""
        try:
            # Apply sharpening filter
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(image, -1, kernel)

            # Enhance edges
            edges = cv2.Canny(image, 50, 150)
            enhanced = cv2.addWeighted(sharpened, 0.8, edges, 0.2, 0)

            logger.debug("Enhanced text regions")
            return enhanced

        except Exception as e:
            logger.error(f"Error in text enhancement: {str(e)}")
            return image

    def get_processing_confidence(self, original_image, processed_image):
        """Calculate confidence score based on image processing quality"""
        try:
            # Calculate various quality metrics

            # 1. Contrast improvement
            orig_std = np.std(original_image)
            proc_std = np.std(processed_image)
            contrast_improvement = proc_std / orig_std if orig_std > 0 else 1.0

            # 2. Edge preservation
            orig_edges = cv2.Canny(original_image, 50, 150)
            proc_edges = cv2.Canny(processed_image, 50, 150)
            edge_ratio = np.sum(proc_edges > 0) / np.sum(orig_edges > 0) if np.sum(orig_edges > 0) > 0 else 1.0

            # 3. Noise reduction (inverse of variance in smooth regions)
            kernel = np.ones((5,5), np.float32) / 25
            smooth_orig = cv2.filter2D(original_image, -1, kernel)
            smooth_proc = cv2.filter2D(processed_image, -1, kernel)

            noise_orig = np.var(original_image - smooth_orig)
            noise_proc = np.var(processed_image - smooth_proc)
            noise_reduction = noise_orig / noise_proc if noise_proc > 0 else 1.0

            # Combine metrics
            confidence = min(1.0, (contrast_improvement * 0.4 +
                                 edge_ratio * 0.3 +
                                 min(noise_reduction, 2.0) * 0.3))

            logger.debug(f"Processing confidence: {confidence:.3f}")
            return confidence

        except Exception as e:
            logger.error(f"Error calculating processing confidence: {str(e)}")
            return 0.5  # Default moderate confidence

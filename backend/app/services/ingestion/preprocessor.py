"""Image preprocessing for scanned documents — deskew, denoise, binarize."""

import cv2
import numpy as np
from typing import Optional


def preprocess_for_ocr(image_path: str) -> tuple[np.ndarray, dict]:
    """
    Preprocess a scanned document image for OCR.

    Steps:
    1. Read image
    2. Convert to grayscale
    3. Noise reduction
    4. Skew detection + correction
    5. Adaptive thresholding (binarization)

    Returns:
        (processed_image, metadata) where metadata contains preprocessing details.
    """
    metadata = {"steps": []}

    # Read image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    original_shape = img.shape[:2]
    metadata["original_size"] = {"height": original_shape[0], "width": original_shape[1]}

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    metadata["steps"].append("grayscale_conversion")

    # Noise reduction using Gaussian blur
    denoised = cv2.GaussianBlur(gray, (3, 3), 0)
    metadata["steps"].append("gaussian_denoise")

    # Skew detection and correction
    skew_angle = _detect_skew(denoised)
    if abs(skew_angle) > 0.5:
        denoised = _deskew(denoised, skew_angle)
        metadata["skew_angle"] = round(skew_angle, 2)
        metadata["steps"].append(f"deskew_{skew_angle:.1f}deg")

    # Adaptive thresholding for binarization
    binary = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=15,
        C=8,
    )
    metadata["steps"].append("adaptive_threshold")

    # Optional: morphological operations to clean up
    kernel = np.ones((1, 1), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    metadata["steps"].append("morphological_cleanup")

    return binary, metadata


def _detect_skew(image: np.ndarray) -> float:
    """Detect document skew angle using Hough Line Transform."""
    try:
        # Edge detection
        edges = cv2.Canny(image, 50, 150, apertureSize=3)

        # Hough Line Transform
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180,
            threshold=100,
            minLineLength=image.shape[1] // 4,
            maxLineGap=20,
        )

        if lines is None or len(lines) == 0:
            return 0.0

        # Calculate angles
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 == 0:
                continue
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            # Only consider near-horizontal lines
            if abs(angle) < 30:
                angles.append(angle)

        if not angles:
            return 0.0

        # Return median angle
        return float(np.median(angles))

    except Exception:
        return 0.0


def _deskew(image: np.ndarray, angle: float) -> np.ndarray:
    """Rotate image to correct skew."""
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Calculate new bounding box
    cos_val = abs(rotation_matrix[0, 0])
    sin_val = abs(rotation_matrix[0, 1])
    new_w = int(h * sin_val + w * cos_val)
    new_h = int(h * cos_val + w * sin_val)

    rotation_matrix[0, 2] += (new_w - w) / 2
    rotation_matrix[1, 2] += (new_h - h) / 2

    # Use white background for documents
    rotated = cv2.warpAffine(
        image, rotation_matrix, (new_w, new_h),
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255,
    )

    return rotated


def preprocess_for_classification(image_path: str) -> np.ndarray:
    """
    Light preprocessing for component photos before classification.
    Just normalize and resize — no binarization.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    # Resize to max 1024px on longest side
    h, w = img.shape[:2]
    max_dim = max(h, w)
    if max_dim > 1024:
        scale = 1024 / max_dim
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    return img

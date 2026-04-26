"""Input type detector — determines if a file is a digital doc, scanned doc, or component photo."""

import os
import mimetypes
from enum import Enum


class InputType(str, Enum):
    DIGITAL_DOC = "digital_doc"
    SCANNED_DOC = "scanned_doc"
    COMPONENT_PHOTO = "component_photo"


# Extensions that are always digital docs
DIGITAL_EXTENSIONS = {".txt", ".doc", ".docx", ".rtf", ".csv", ".md"}

# Extensions that need further analysis
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}

# PDF can be either digital or scanned
PDF_EXTENSIONS = {".pdf"}


def detect_input_type(file_path: str, mime_type: str | None = None) -> InputType:
    """
    Detect whether a file is a digital document, scanned document, or component photo.

    Logic:
    1. Text files (.txt, .doc, .docx) → always digital_doc
    2. PDFs → check if text-extractable; if yes → digital_doc, else → scanned_doc
    3. Images → analyze content to distinguish scanned docs from component photos
       - Uses aspect ratio + content heuristics
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext in DIGITAL_EXTENSIONS:
        return InputType.DIGITAL_DOC

    if ext in PDF_EXTENSIONS:
        return _classify_pdf(file_path)

    if ext in IMAGE_EXTENSIONS:
        return _classify_image(file_path)

    # Fallback: try MIME type
    if mime_type:
        if mime_type.startswith("text/") or "document" in mime_type or "pdf" in mime_type:
            return InputType.DIGITAL_DOC
        if mime_type.startswith("image/"):
            return _classify_image(file_path)

    return InputType.DIGITAL_DOC


def _classify_pdf(file_path: str) -> InputType:
    """Check if a PDF has extractable text or is a scanned image."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        total_text = ""
        for page in doc:
            total_text += page.get_text()
        doc.close()

        # If PDF has substantial text, it's digital
        if len(total_text.strip()) > 50:
            return InputType.DIGITAL_DOC
        else:
            return InputType.SCANNED_DOC
    except Exception:
        return InputType.DIGITAL_DOC


def _classify_image(file_path: str) -> InputType:
    """
    Distinguish scanned documents from component photos using image heuristics.

    Scanned docs tend to:
    - Have higher aspect ratios (portrait orientation, letter/A4 size)
    - Have predominantly white/light backgrounds
    - Have high contrast between text and background

    Component photos tend to:
    - Have more varied colors (metallic, dark backgrounds)
    - Have lower contrast, more gradients
    - Often landscape or square orientation
    """
    try:
        from PIL import Image
        import statistics

        img = Image.open(file_path)
        width, height = img.size

        # Convert to grayscale for analysis
        gray = img.convert("L")
        pixels = list(gray.getdata())

        # Calculate statistics
        mean_val = statistics.mean(pixels)
        std_val = statistics.stdev(pixels) if len(pixels) > 1 else 0

        # Aspect ratio (height/width for portrait docs)
        aspect = height / width if width > 0 else 1.0

        # Count bright pixels (>200) — documents have lots of white space
        bright_ratio = sum(1 for p in pixels if p > 200) / len(pixels) if pixels else 0

        # Heuristic scoring
        doc_score = 0.0

        # Portrait orientation suggests document
        if aspect > 1.2:
            doc_score += 0.3
        elif aspect > 1.0:
            doc_score += 0.15

        # High brightness suggests document (white paper)
        if mean_val > 180:
            doc_score += 0.3
        elif mean_val > 150:
            doc_score += 0.15

        # High bright pixel ratio suggests document
        if bright_ratio > 0.5:
            doc_score += 0.25
        elif bright_ratio > 0.3:
            doc_score += 0.1

        # High contrast (bimodal distribution) suggests document with text
        if std_val > 60:
            doc_score += 0.15

        if doc_score >= 0.45:
            return InputType.SCANNED_DOC
        else:
            return InputType.COMPONENT_PHOTO

    except Exception:
        # If we can't analyze, assume scanned doc (safer default for images)
        return InputType.SCANNED_DOC

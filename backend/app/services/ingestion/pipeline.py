"""
Processing orchestrator — coordinates the full ingestion pipeline for a document.

Flow:
1. Detect input type (digital doc / scanned doc / component photo)
2. Route to appropriate processor:
   - Digital doc → extract text directly (PDF parser or text reader)
   - Scanned doc → preprocess → OCR → extract text
   - Component photo → light preprocess → flag for Layer 2 classification
3. Return unified ProcessedDocument
"""

import os
import base64
from dataclasses import dataclass, field
from typing import Optional

from app.services.ingestion.detector import detect_input_type, InputType
from app.services.ingestion.pdf_parser import extract_pdf_text, extract_text_file
from app.services.ingestion.preprocessor import preprocess_for_ocr, preprocess_for_classification
from app.services.ingestion.ocr import run_ocr


@dataclass
class ProcessedDocument:
    """Unified output from Layer 1 processing."""
    input_type: str
    clean_text: str
    raw_text: str
    ocr_confidence: Optional[float] = None
    structure_metadata: dict = field(default_factory=dict)
    tables: list = field(default_factory=list)
    image_base64: Optional[str] = None  # For component photos → Layer 2
    preprocessing_metadata: dict = field(default_factory=dict)
    error: Optional[str] = None


def process_document(file_path: str, mime_type: str | None = None) -> ProcessedDocument:
    """
    Main entry point: process a single file through the Layer 1 pipeline.

    Args:
        file_path: Path to the uploaded file on disk
        mime_type: Optional MIME type hint

    Returns:
        ProcessedDocument with extracted content ready for Layer 2
    """
    if not os.path.exists(file_path):
        return ProcessedDocument(
            input_type="unknown",
            clean_text="",
            raw_text="",
            error=f"File not found: {file_path}",
        )

    # Step 1: Detect input type
    input_type = detect_input_type(file_path, mime_type)

    # Step 2: Route to appropriate processor
    try:
        if input_type == InputType.DIGITAL_DOC:
            return _process_digital_doc(file_path, input_type)
        elif input_type == InputType.SCANNED_DOC:
            return _process_scanned_doc(file_path, input_type)
        elif input_type == InputType.COMPONENT_PHOTO:
            return _process_component_photo(file_path, input_type)
        else:
            return ProcessedDocument(
                input_type=input_type.value,
                clean_text="",
                raw_text="",
                error=f"Unknown input type: {input_type}",
            )
    except Exception as e:
        return ProcessedDocument(
            input_type=input_type.value,
            clean_text="",
            raw_text="",
            error=str(e),
        )


def _process_digital_doc(file_path: str, input_type: InputType) -> ProcessedDocument:
    """Process a digital document (text file or PDF with extractable text)."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        extraction = extract_pdf_text(file_path)
        clean_text = extraction.full_text.strip()
        structure = extraction.structure
        # Extract headings for structure-aware chunking later
        structure["headings"] = extraction.structure.get("headings", [])
        structure["pages"] = [
            {
                "page": p.page_number,
                "headings": p.headings,
                "has_images": p.has_images,
            }
            for p in extraction.pages
        ]
    else:
        # Plain text or similar
        raw = extract_text_file(file_path)
        clean_text = raw.strip()
        structure = _detect_text_structure(clean_text)

    return ProcessedDocument(
        input_type=input_type.value,
        clean_text=clean_text,
        raw_text=clean_text,
        ocr_confidence=1.0,  # Digital docs have perfect "OCR"
        structure_metadata=structure,
    )


def _process_scanned_doc(file_path: str, input_type: InputType) -> ProcessedDocument:
    """Process a scanned document image through OCR pipeline."""
    # Preprocess
    processed_image, preprocess_meta = preprocess_for_ocr(file_path)

    # OCR
    ocr_result = run_ocr(processed_image, extract_tables=True)

    clean_text = ocr_result.text.strip()
    structure = {
        **ocr_result.structure,
        "preprocessing": preprocess_meta,
    }

    return ProcessedDocument(
        input_type=input_type.value,
        clean_text=clean_text,
        raw_text=ocr_result.text,
        ocr_confidence=ocr_result.confidence,
        structure_metadata=structure,
        tables=ocr_result.tables,
        preprocessing_metadata=preprocess_meta,
    )


def _process_component_photo(file_path: str, input_type: InputType) -> ProcessedDocument:
    """Process a component photo — prepare for Layer 2 classification."""
    # Encode image as base64 for sending to vision LLM in Layer 2
    with open(file_path, "rb") as f:
        image_bytes = f.read()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    # Determine MIME for base64
    ext = os.path.splitext(file_path)[1].lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
    mime = mime_map.get(ext, "image/jpeg")

    return ProcessedDocument(
        input_type=input_type.value,
        clean_text="",  # No text for photos
        raw_text="",
        ocr_confidence=None,
        structure_metadata={"mime_type": mime, "file_size": len(image_bytes)},
        image_base64=f"data:{mime};base64,{image_b64}",
    )


def _detect_text_structure(text: str) -> dict:
    """Detect structural elements in plain text (headings, sections, tables)."""
    lines = text.split("\n")
    headings = []
    has_tables = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Detect headings: ALL CAPS lines, or lines with --- underline
        if stripped.isupper() and len(stripped) > 3 and len(stripped) < 100:
            headings.append(stripped)

        # Detect table markers
        if "|" in stripped and stripped.count("|") >= 2:
            has_tables = True

    return {
        "headings": headings,
        "has_tables": has_tables,
        "line_count": len(lines),
        "char_count": len(text),
    }

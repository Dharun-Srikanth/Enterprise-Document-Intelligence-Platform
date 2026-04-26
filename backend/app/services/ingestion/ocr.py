"""OCR pipeline using Tesseract for scanned documents."""

import cv2
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OCRResult:
    text: str
    confidence: float
    tables: list[list[list[str]]] = field(default_factory=list)
    structure: dict = field(default_factory=dict)


def run_ocr(image: np.ndarray, extract_tables: bool = True) -> OCRResult:
    """
    Run Tesseract OCR on a preprocessed image.

    Args:
        image: Preprocessed grayscale/binary image (numpy array)
        extract_tables: Whether to attempt table structure extraction

    Returns:
        OCRResult with text, confidence, and optional table data
    """
    try:
        import pytesseract
    except ImportError:
        return _fallback_ocr(image)

    # Run OCR with detailed output
    try:
        ocr_data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT,
            config="--psm 6 --oem 3",
        )
    except Exception as e:
        return _fallback_ocr(image)

    # Extract text and calculate confidence
    words = []
    confidences = []
    for i, text in enumerate(ocr_data["text"]):
        conf = int(ocr_data["conf"][i])
        if conf > 0 and text.strip():
            words.append(text.strip())
            confidences.append(conf)

    full_text = _reconstruct_text(ocr_data)
    avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0

    # Extract tables if requested
    tables = []
    if extract_tables:
        tables = _extract_tables(image, ocr_data)

    structure = {
        "word_count": len(words),
        "line_count": len(set(zip(ocr_data["block_num"], ocr_data["line_num"]))),
        "block_count": len(set(ocr_data["block_num"])),
    }

    return OCRResult(
        text=full_text,
        confidence=round(avg_confidence, 3),
        tables=tables,
        structure=structure,
    )


def _reconstruct_text(ocr_data: dict) -> str:
    """Reconstruct text preserving line and paragraph structure."""
    lines = {}
    for i, text in enumerate(ocr_data["text"]):
        if not text.strip():
            continue
        block = ocr_data["block_num"][i]
        par = ocr_data["par_num"][i]
        line = ocr_data["line_num"][i]
        key = (block, par, line)
        if key not in lines:
            lines[key] = []
        lines[key].append(text)

    # Build text with proper spacing
    result_parts = []
    prev_block = None
    for key in sorted(lines.keys()):
        block, par, line = key
        if prev_block is not None and block != prev_block:
            result_parts.append("")  # Paragraph break
        prev_block = block
        result_parts.append(" ".join(lines[key]))

    return "\n".join(result_parts)


def _extract_tables(image: np.ndarray, ocr_data: dict) -> list[list[list[str]]]:
    """
    Attempt to extract table structures from OCR data.

    Uses positional analysis of OCR bounding boxes to detect tabular layouts:
    - Groups words into rows by vertical position
    - Groups columns by horizontal position clustering
    """
    if not any(t.strip() for t in ocr_data["text"]):
        return []

    # Collect word positions
    word_entries = []
    for i, text in enumerate(ocr_data["text"]):
        if not text.strip() or int(ocr_data["conf"][i]) <= 0:
            continue
        word_entries.append({
            "text": text.strip(),
            "left": ocr_data["left"][i],
            "top": ocr_data["top"][i],
            "width": ocr_data["width"][i],
            "height": ocr_data["height"][i],
        })

    if len(word_entries) < 4:
        return []

    # Group by rows (similar top positions)
    rows_dict = {}
    row_threshold = 15  # pixels

    for entry in word_entries:
        top = entry["top"]
        matched_row = None
        for row_top in rows_dict:
            if abs(top - row_top) < row_threshold:
                matched_row = row_top
                break
        if matched_row is not None:
            rows_dict[matched_row].append(entry)
        else:
            rows_dict[top] = [entry]

    # Filter to rows that look like table rows (multiple columns, aligned)
    table_rows = []
    for row_top in sorted(rows_dict.keys()):
        entries = sorted(rows_dict[row_top], key=lambda e: e["left"])
        if len(entries) >= 2:
            table_rows.append(entries)

    if len(table_rows) < 2:
        return []

    # Detect column positions by finding consistent horizontal gaps
    # For simplicity, just split each row into cells based on large gaps
    tables = []
    current_table = []

    for row in table_rows:
        cells = []
        current_cell = [row[0]["text"]]
        for j in range(1, len(row)):
            gap = row[j]["left"] - (row[j-1]["left"] + row[j-1]["width"])
            if gap > 30:  # Large gap = new column
                cells.append(" ".join(current_cell))
                current_cell = [row[j]["text"]]
            else:
                current_cell.append(row[j]["text"])
        cells.append(" ".join(current_cell))
        current_table.append(cells)

    if current_table:
        tables.append(current_table)

    return tables


def _fallback_ocr(image: np.ndarray) -> OCRResult:
    """Fallback when Tesseract is not available — returns empty result."""
    return OCRResult(
        text="[OCR unavailable — Tesseract not installed]",
        confidence=0.0,
        tables=[],
        structure={"error": "tesseract_not_available"},
    )

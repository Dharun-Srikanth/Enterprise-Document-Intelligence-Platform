"""PDF text extraction using PyMuPDF."""

from dataclasses import dataclass, field


@dataclass
class ExtractedPage:
    page_number: int
    text: str
    tables: list[list[list[str]]] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)
    has_images: bool = False


@dataclass
class PDFExtraction:
    total_pages: int
    pages: list[ExtractedPage]
    full_text: str
    structure: dict


def extract_pdf_text(file_path: str) -> PDFExtraction:
    """
    Extract text and structure from a PDF file.

    Uses PyMuPDF to extract:
    - Plain text per page
    - Text blocks with position info (for structure detection)
    - Embedded images (flagged for potential OCR)
    """
    import fitz  # PyMuPDF

    doc = fitz.open(file_path)
    pages = []
    all_text = []
    all_headings = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        all_text.append(text)

        # Extract text blocks for structure analysis
        blocks = page.get_text("dict")["blocks"]
        headings = []
        for block in blocks:
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        # Detect headings by font size
                        if span.get("size", 0) > 14:
                            heading_text = span.get("text", "").strip()
                            if heading_text:
                                headings.append(heading_text)

        # Check for images
        images = page.get_images(full=True)
        has_images = len(images) > 0

        pages.append(ExtractedPage(
            page_number=page_num + 1,
            text=text,
            headings=headings,
            has_images=has_images,
        ))
        all_headings.extend(headings)

    doc.close()

    full_text = "\n\n".join(all_text)

    structure = {
        "total_pages": len(pages),
        "headings": all_headings,
        "has_images": any(p.has_images for p in pages),
        "pages_with_images": [p.page_number for p in pages if p.has_images],
    }

    return PDFExtraction(
        total_pages=len(pages),
        pages=pages,
        full_text=full_text,
        structure=structure,
    )


def extract_text_file(file_path: str) -> str:
    """Extract text from a plain text file."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    # Last resort: read as binary and decode with errors ignored
    with open(file_path, "rb") as f:
        return f.read().decode("utf-8", errors="replace")

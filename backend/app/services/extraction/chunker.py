"""Document chunker — structure-aware chunking for vector store."""

import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 800  # characters
DEFAULT_CHUNK_OVERLAP = 150  # characters


@dataclass
class DocumentChunkData:
    chunk_index: int
    text: str
    metadata: dict


def chunk_document(
    text: str,
    structure_metadata: dict | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[DocumentChunkData]:
    """
    Split document text into chunks for vector embedding.

    Uses structure-aware chunking:
    1. If headings are detected, split by sections first
    2. Then apply size-based splitting within sections
    3. Preserve section context in chunk metadata
    """
    if not text or not text.strip():
        return []

    headings = (structure_metadata or {}).get("headings", [])

    if headings:
        return _structure_aware_chunk(text, headings, chunk_size, chunk_overlap)
    else:
        return _sliding_window_chunk(text, chunk_size, chunk_overlap)


def _structure_aware_chunk(
    text: str,
    headings: list[str],
    chunk_size: int,
    chunk_overlap: int,
) -> list[DocumentChunkData]:
    """Split by document sections (headings), then by size within sections."""
    chunks = []
    chunk_idx = 0

    # Find section boundaries
    sections = _split_by_headings(text, headings)

    for section_heading, section_text in sections:
        if not section_text.strip():
            continue

        # If section is small enough, keep as single chunk
        if len(section_text) <= chunk_size:
            chunks.append(DocumentChunkData(
                chunk_index=chunk_idx,
                text=section_text.strip(),
                metadata={"section": section_heading},
            ))
            chunk_idx += 1
        else:
            # Split section into smaller chunks
            sub_chunks = _sliding_window_chunk(
                section_text, chunk_size, chunk_overlap, start_idx=chunk_idx
            )
            for sc in sub_chunks:
                sc.metadata["section"] = section_heading
            chunks.extend(sub_chunks)
            chunk_idx += len(sub_chunks)

    return chunks


def _split_by_headings(text: str, headings: list[str]) -> list[tuple[str, str]]:
    """Split text into (heading, content) pairs using detected headings."""
    if not headings:
        return [("Document", text)]

    sections = []
    remaining = text
    last_heading = "Introduction"

    for heading in headings:
        # Find heading in text
        idx = remaining.find(heading)
        if idx == -1:
            # Try case-insensitive
            lower_remaining = remaining.lower()
            lower_heading = heading.lower()
            idx = lower_remaining.find(lower_heading)

        if idx > 0:
            # Content before this heading belongs to the previous section
            before = remaining[:idx].strip()
            if before:
                sections.append((last_heading, before))
            remaining = remaining[idx:]
            last_heading = heading
        elif idx == 0:
            last_heading = heading
            remaining = remaining[len(heading):]

    # Last section
    if remaining.strip():
        sections.append((last_heading, remaining.strip()))

    if not sections:
        sections = [("Document", text)]

    return sections


def _sliding_window_chunk(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    start_idx: int = 0,
) -> list[DocumentChunkData]:
    """Simple sliding window chunking with paragraph-aware boundaries."""
    chunks = []
    paragraphs = re.split(r"\n\s*\n", text)

    current_chunk = ""
    chunk_idx = start_idx

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) + 1 <= chunk_size:
            current_chunk += ("\n\n" + para if current_chunk else para)
        else:
            if current_chunk:
                chunks.append(DocumentChunkData(
                    chunk_index=chunk_idx,
                    text=current_chunk,
                    metadata={},
                ))
                chunk_idx += 1

                # Overlap: keep tail of current chunk
                if chunk_overlap > 0:
                    overlap_text = current_chunk[-chunk_overlap:]
                    current_chunk = overlap_text + "\n\n" + para
                else:
                    current_chunk = para
            else:
                # Single paragraph larger than chunk_size — force split
                for i in range(0, len(para), chunk_size - chunk_overlap):
                    chunk_text = para[i:i + chunk_size]
                    if chunk_text.strip():
                        chunks.append(DocumentChunkData(
                            chunk_index=chunk_idx,
                            text=chunk_text.strip(),
                            metadata={},
                        ))
                        chunk_idx += 1
                current_chunk = ""

    # Flush remaining
    if current_chunk.strip():
        chunks.append(DocumentChunkData(
            chunk_index=chunk_idx,
            text=current_chunk.strip(),
            metadata={},
        ))

    return chunks

"""Upload API routes with background processing pipeline."""

import os
import uuid
import logging
import aiofiles
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db, async_session
from app.models.document import Document
from app.config import get_settings
from app.services.ingestion.pipeline import process_document

router = APIRouter(prefix="/api", tags=["upload"])
settings = get_settings()
logger = logging.getLogger(__name__)


async def _run_processing(doc_id: uuid.UUID, file_path: str, mime_type: str | None):
    """Background task: run Layer 1 + Layer 2 processing on an uploaded document."""
    async with async_session() as db:
        try:
            # Update status to processing
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if not doc:
                return

            doc.processing_status = "processing"
            await db.commit()

            # === LAYER 1: Ingestion + OCR ===
            import asyncio
            processed = await asyncio.to_thread(process_document, file_path, mime_type)

            # Refresh doc from DB
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if not doc:
                return

            if processed.error:
                doc.processing_status = "failed"
                doc.processing_error = processed.error
                await db.commit()
                return

            doc.file_type = processed.input_type
            doc.clean_text = processed.clean_text
            doc.raw_text = processed.raw_text
            doc.ocr_confidence = processed.ocr_confidence
            doc.structure_metadata = processed.structure_metadata
            await db.commit()

            logger.info(f"Layer 1 done for {doc.filename}: type={processed.input_type}")

            # === LAYER 2: Extraction, Classification & Storage ===
            from app.services.extraction.pipeline import process_stream_a, process_stream_b

            if processed.input_type in ("digital_doc", "scanned_doc"):
                # Stream A: Document processing
                l2_results = await process_stream_a(doc, db, use_llm=True)
                logger.info(f"Layer 2 Stream A done for {doc.filename}: {l2_results}")
            elif processed.input_type == "component_photo" and processed.image_base64:
                # Stream B: Component photo classification
                l2_results = await process_stream_b(doc, db, processed.image_base64)
                logger.info(f"Layer 2 Stream B done for {doc.filename}: {l2_results}")

            # Mark as completed
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if doc:
                doc.processing_status = "completed"
                await db.commit()

            logger.info(f"Fully processed {doc.filename}")

        except Exception as e:
            logger.exception(f"Processing failed for doc {doc_id}")
            try:
                result = await db.execute(select(Document).where(Document.id == doc_id))
                doc = result.scalar_one_or_none()
                if doc:
                    doc.processing_status = "failed"
                    doc.processing_error = str(e)
                    await db.commit()
            except Exception:
                pass


@router.post("/upload")
async def upload_files(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload one or more files for processing."""
    results = []

    for file in files:
        # Validate file size
        content = await file.read()
        size_mb = len(content) / (1024 * 1024)
        if size_mb > settings.max_upload_size_mb:
            results.append({
                "filename": file.filename,
                "error": f"File exceeds {settings.max_upload_size_mb}MB limit",
            })
            continue

        # Detect file type from MIME (preliminary — refined in processing)
        mime = file.content_type or "application/octet-stream"
        file_type = _detect_file_type(mime, file.filename)

        # Save file to disk
        doc_id = uuid.uuid4()
        ext = os.path.splitext(file.filename)[1] if file.filename else ""
        save_path = os.path.join(settings.upload_dir, f"{doc_id}{ext}")
        os.makedirs(settings.upload_dir, exist_ok=True)

        async with aiofiles.open(save_path, "wb") as f:
            await f.write(content)

        # Create DB record
        doc = Document(
            id=doc_id,
            filename=file.filename or "unknown",
            file_type=file_type,
            mime_type=mime,
            processing_status="pending",
            file_path=save_path,
        )
        db.add(doc)
        await db.flush()

        # Queue background processing
        background_tasks.add_task(_run_processing, doc_id, save_path, mime)

        results.append({
            "id": str(doc_id),
            "filename": file.filename,
            "file_type": file_type,
            "mime_type": mime,
            "size_mb": round(size_mb, 2),
            "status": "pending",
        })

    await db.commit()
    return {"uploaded": len(results), "files": results}


@router.get("/upload/status/{doc_id}")
async def get_upload_status(doc_id: str, db: AsyncSession = Depends(get_db)):
    """Get processing status of a document."""
    try:
        uid = uuid.UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")

    result = await db.execute(select(Document).where(Document.id == uid))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "file_type": doc.file_type,
        "status": doc.processing_status,
        "doc_category": doc.doc_category,
        "ocr_confidence": doc.ocr_confidence,
        "error": doc.processing_error,
    }


def _detect_file_type(mime: str, filename: str | None) -> str:
    """Basic file type detection from MIME type. Layer 1 will refine this."""
    mime_lower = mime.lower()
    fname_lower = (filename or "").lower()

    if mime_lower in ("application/pdf",):
        return "digital_doc"  # Will be refined after checking if text-extractable
    elif mime_lower in ("text/plain", "application/msword",
                         "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
        return "digital_doc"
    elif mime_lower.startswith("image/"):
        # Will be refined in Layer 1 (scanned_doc vs component_photo)
        return "scanned_doc"
    else:
        return "digital_doc"

"""Document listing API routes."""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.document import Document

router = APIRouter(prefix="/api", tags=["documents"])


@router.get("/documents")
async def list_documents(db: AsyncSession = Depends(get_db)):
    """List all ingested documents with metadata."""
    result = await db.execute(
        select(Document).order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    return {
        "total": len(docs),
        "documents": [
            {
                "id": str(d.id),
                "filename": d.filename,
                "file_type": d.file_type,
                "doc_category": d.doc_category,
                "processing_status": d.processing_status,
                "ocr_confidence": d.ocr_confidence,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ],
    }


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    """Get full document details with entities, components, and chunks."""
    from app.models.entity import Entity
    from app.models.component import Component
    from app.models.document_chunk import DocumentChunk

    try:
        uid = uuid.UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")

    result = await db.execute(select(Document).where(Document.id == uid))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Fetch related entities
    ent_result = await db.execute(
        select(Entity).where(Entity.document_id == uid).order_by(Entity.entity_type)
    )
    entities = ent_result.scalars().all()

    # Fetch related components
    comp_result = await db.execute(
        select(Component).where(Component.document_id == uid)
    )
    components = comp_result.scalars().all()

    # Fetch related chunks
    chunk_result = await db.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == uid).order_by(DocumentChunk.chunk_index)
    )
    chunks = chunk_result.scalars().all()

    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "file_type": doc.file_type,
        "mime_type": doc.mime_type,
        "doc_category": doc.doc_category,
        "doc_category_secondary": doc.doc_category_secondary,
        "category_confidence": doc.category_confidence,
        "clean_text": doc.clean_text,
        "ocr_confidence": doc.ocr_confidence,
        "processing_status": doc.processing_status,
        "processing_error": doc.processing_error,
        "structure_metadata": doc.structure_metadata,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "entities": [
            {
                "entity_type": e.entity_type,
                "entity_value": e.entity_value,
                "normalized_value": e.normalized_value,
                "confidence": e.confidence,
            }
            for e in entities
        ],
        "components": [
            {
                "component_type": c.component_type,
                "component_confidence": c.component_confidence,
                "material": c.material,
                "material_confidence": c.material_confidence,
                "estimated_cost_low": float(c.estimated_cost_low) if c.estimated_cost_low else None,
                "estimated_cost_high": float(c.estimated_cost_high) if c.estimated_cost_high else None,
                "estimated_cost_mid": float(c.estimated_cost_mid) if c.estimated_cost_mid else None,
                "carbon_footprint_kg_co2e": float(c.carbon_footprint_kg_co2e) if c.carbon_footprint_kg_co2e else None,
                "emission_factor_source": c.emission_factor_source,
                "overall_confidence": c.overall_confidence,
                "is_flagged": c.is_flagged,
                "flag_reason": c.flag_reason,
            }
            for c in components
        ],
        "chunks": [
            {
                "chunk_index": ch.chunk_index,
                "chunk_text": ch.chunk_text[:200] if ch.chunk_text else "",
                "section": (ch.chunk_metadata or {}).get("section", ""),
            }
            for ch in chunks
        ],
    }


@router.get("/components")
async def list_components(db: AsyncSession = Depends(get_db)):
    """List all classified tear-down components."""
    from app.models.component import Component

    result = await db.execute(
        select(Component).order_by(Component.created_at.desc())
    )
    components = result.scalars().all()
    return {
        "total": len(components),
        "components": [
            {
                "id": str(c.id),
                "document_id": str(c.document_id),
                "component_type": c.component_type,
                "material": c.material,
                "estimated_cost_low": float(c.estimated_cost_low) if c.estimated_cost_low else None,
                "estimated_cost_high": float(c.estimated_cost_high) if c.estimated_cost_high else None,
                "estimated_cost_mid": float(c.estimated_cost_mid) if c.estimated_cost_mid else None,
                "carbon_footprint_kg_co2e": float(c.carbon_footprint_kg_co2e) if c.carbon_footprint_kg_co2e else None,
                "overall_confidence": c.overall_confidence,
                "is_flagged": c.is_flagged,
                "flag_reason": c.flag_reason,
            }
            for c in components
        ],
    }

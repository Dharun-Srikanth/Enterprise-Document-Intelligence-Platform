"""
Layer 2 Processing Pipeline — Extraction, Classification & Storage.

Orchestrates:
- Stream A (Documents): Entity extraction, document classification, relationship mapping
- Stream B (Photos): Component classification, material ID, cost/carbon estimation
- Storage: PostgreSQL (entities, components) + ChromaDB (embeddings)
"""

import uuid
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import Document
from app.models.entity import Entity
from app.models.entity_relationship import EntityRelationship
from app.models.component import Component
from app.models.document_chunk import DocumentChunk

from app.services.extraction.entity_extractor import extract_entities
from app.services.extraction.doc_classifier import classify_document
from app.services.extraction.relationship_mapper import extract_relationships
from app.services.extraction.component_classifier import classify_component
from app.services.extraction.sustainability import estimate_sustainability
from app.services.extraction.chunker import chunk_document

logger = logging.getLogger(__name__)


async def process_stream_a(
    doc: Document,
    db: AsyncSession,
    use_llm: bool = True,
) -> dict:
    """
    Stream A: Process a document (digital or scanned).
    - Entity extraction
    - Document classification
    - Relationship mapping
    - Chunking + embedding
    """
    text = doc.clean_text or ""
    if not text.strip():
        logger.warning(f"Document {doc.id} has no text to process")
        return {"entities": 0, "relationships": 0, "chunks": 0}

    results = {"entities": 0, "relationships": 0, "chunks": 0}

    # 1. Document Classification
    try:
        classification = classify_document(text)
        doc.doc_category = classification.primary_category
        doc.doc_category_secondary = classification.secondary_category
        doc.category_confidence = classification.primary_confidence
        logger.info(f"Classified {doc.filename}: {classification.primary_category} ({classification.primary_confidence})")
    except Exception as e:
        logger.error(f"Classification failed for {doc.filename}: {e}")

    # 2. Entity Extraction
    entity_records = []
    try:
        entities = extract_entities(text, use_llm=use_llm)
        for ent in entities:
            entity_record = Entity(
                id=uuid.uuid4(),
                document_id=doc.id,
                entity_type=ent.entity_type,
                entity_value=ent.value,
                normalized_value=ent.normalized_value,
                confidence=ent.confidence,
                start_offset=ent.start_offset,
                end_offset=ent.end_offset,
            )
            db.add(entity_record)
            entity_records.append(entity_record)
        results["entities"] = len(entities)
        logger.info(f"Extracted {len(entities)} entities from {doc.filename}")
    except Exception as e:
        logger.error(f"Entity extraction failed for {doc.filename}: {e}")

    # 3. Relationship Mapping
    if entity_records and use_llm:
        try:
            entity_dicts = [
                {"entity_type": e.entity_type, "value": e.entity_value}
                for e in entity_records
            ]
            relationships = extract_relationships(text, entity_dicts)

            # Map relationship entity values back to entity IDs
            entity_lookup = {}
            for er in entity_records:
                key = (er.entity_type, er.entity_value.lower().strip())
                entity_lookup[key] = er

            for rel in relationships:
                src_key = (rel.source_type, rel.source_value.lower().strip())
                tgt_key = (rel.target_type, rel.target_value.lower().strip())

                src_entity = entity_lookup.get(src_key)
                tgt_entity = entity_lookup.get(tgt_key)

                if src_entity and tgt_entity:
                    rel_record = EntityRelationship(
                        id=uuid.uuid4(),
                        document_id=doc.id,
                        source_entity_id=src_entity.id,
                        target_entity_id=tgt_entity.id,
                        relationship_type=rel.relationship_type,
                        confidence=rel.confidence,
                    )
                    db.add(rel_record)
                    results["relationships"] += 1

            logger.info(f"Mapped {results['relationships']} relationships from {doc.filename}")
        except Exception as e:
            logger.error(f"Relationship mapping failed for {doc.filename}: {e}")

    # 4. Chunking + Vector Store
    try:
        chunks = chunk_document(text, doc.structure_metadata)
        for chunk_data in chunks:
            chunk_record = DocumentChunk(
                id=uuid.uuid4(),
                document_id=doc.id,
                chunk_index=chunk_data.chunk_index,
                chunk_text=chunk_data.text,
                chunk_metadata=chunk_data.metadata,
            )
            db.add(chunk_record)

        results["chunks"] = len(chunks)
        logger.info(f"Created {len(chunks)} chunks from {doc.filename}")

        # Embed and store in ChromaDB
        try:
            await _store_embeddings(doc, chunks)
        except Exception as e:
            logger.warning(f"Vector store embedding failed for {doc.filename}: {e}")

    except Exception as e:
        logger.error(f"Chunking failed for {doc.filename}: {e}")

    return results


async def process_stream_b(
    doc: Document,
    db: AsyncSession,
    image_data_url: str,
) -> dict:
    """
    Stream B: Process a tear-down component photo.
    - Component classification (vision)
    - Material identification (vision)
    - Cost estimation (benchmark lookup)
    - Carbon footprint estimation (benchmark lookup)
    """
    results = {"component": None, "flagged": False}

    # 1. Classify component + material using vision
    try:
        classification = classify_component(image_data_url)
    except Exception as e:
        logger.error(f"Component classification failed for {doc.filename}: {e}")
        return results

    # 2. Estimate cost + carbon from benchmark
    try:
        estimate = estimate_sustainability(
            classification.component_type,
            classification.material,
        )
    except Exception as e:
        logger.error(f"Sustainability estimation failed: {e}")
        estimate = None

    # 3. Determine confidence and flagging
    overall_confidence = min(
        classification.component_confidence,
        classification.material_confidence,
    )
    is_flagged = overall_confidence < 0.6
    flag_reason = None
    if is_flagged:
        reasons = []
        if classification.component_confidence < 0.6:
            reasons.append(f"Low component confidence: {classification.component_confidence:.2f}")
        if classification.material_confidence < 0.6:
            reasons.append(f"Low material confidence: {classification.material_confidence:.2f}")
        flag_reason = "; ".join(reasons)

    # 4. Store in DB
    component = Component(
        id=uuid.uuid4(),
        document_id=doc.id,
        component_type=classification.component_type,
        component_confidence=classification.component_confidence,
        material=classification.material,
        material_confidence=classification.material_confidence,
        estimated_cost_low=estimate.cost_low if estimate else None,
        estimated_cost_high=estimate.cost_high if estimate else None,
        estimated_cost_mid=estimate.cost_mid if estimate else None,
        carbon_footprint_kg_co2e=estimate.carbon_footprint_kg_co2e if estimate else None,
        emission_factor_source=estimate.emission_factor_source if estimate else None,
        overall_confidence=overall_confidence,
        is_flagged=is_flagged,
        flag_reason=flag_reason,
        classification_metadata={
            "reasoning": classification.reasoning,
            "raw_response": classification.raw_response,
            "benchmark_match": estimate.match_found if estimate else False,
            "benchmark_notes": estimate.notes if estimate else None,
        },
    )
    db.add(component)

    results["component"] = {
        "type": classification.component_type,
        "material": classification.material,
        "cost_mid": float(estimate.cost_mid) if estimate and estimate.cost_mid else None,
        "carbon_kg_co2e": float(estimate.carbon_footprint_kg_co2e) if estimate and estimate.carbon_footprint_kg_co2e else None,
        "confidence": overall_confidence,
        "flagged": is_flagged,
    }

    logger.info(
        f"Classified {doc.filename}: {classification.component_type} / "
        f"{classification.material} (conf={overall_confidence:.2f}, flagged={is_flagged})"
    )

    return results


async def _store_embeddings(doc: Document, chunks: list) -> None:
    """Embed chunks and store in ChromaDB."""
    import asyncio
    from app.services.llm_client import get_embeddings
    from app.db.vector_store import get_collection

    if not chunks:
        return

    texts = [c.text for c in chunks]
    ids = [f"{doc.id}_chunk_{c.chunk_index}" for c in chunks]
    metadatas = [
        {
            "document_id": str(doc.id),
            "filename": doc.filename or "",
            "file_type": doc.file_type or "",
            "doc_category": doc.doc_category or "",
            "chunk_index": c.chunk_index,
            "section": c.metadata.get("section", ""),
        }
        for c in chunks
    ]

    # Get embeddings (run in thread since it's sync I/O)
    embeddings = await asyncio.to_thread(get_embeddings, texts)

    # Store in ChromaDB
    collection = await asyncio.to_thread(get_collection, "documents")
    await asyncio.to_thread(
        collection.upsert,
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    logger.info(f"Stored {len(chunks)} embeddings for {doc.filename}")

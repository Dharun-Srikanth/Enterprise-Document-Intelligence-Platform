"""
Backfill ChromaDB embeddings from existing PostgreSQL document chunks.

Run from the backend directory:
    python -m scripts.backfill_embeddings
"""

import sys
import os
import asyncio
import logging

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = 50  # embed this many chunks at a time


async def backfill():
    from sqlalchemy import text
    from app.db.database import async_session
    from app.db.vector_store import get_collection
    from app.services.llm_client import get_embeddings

    collection = get_collection("documents")
    existing_count = collection.count()
    logger.info(f"ChromaDB collection 'documents' currently has {existing_count} entries")

    async with async_session() as db:
        # Get all chunks with their document metadata
        result = await db.execute(text("""
            SELECT
                dc.id, dc.document_id, dc.chunk_index, dc.chunk_text, dc.chunk_metadata,
                d.filename, d.file_type, d.doc_category
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE d.processing_status = 'completed'
              AND d.clean_text IS NOT NULL
              AND d.clean_text != ''
            ORDER BY dc.document_id, dc.chunk_index
        """))
        rows = result.fetchall()

    logger.info(f"Found {len(rows)} chunks in PostgreSQL to embed")

    if not rows:
        logger.warning("No chunks found. Upload and process documents first.")
        return

    # Process in batches
    total_stored = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]

        ids = []
        texts = []
        metadatas = []

        for row in batch:
            chunk_id = row[0]
            doc_id = row[1]
            chunk_index = row[2]
            chunk_text = row[3]
            chunk_meta = row[4] or {}
            filename = row[5]
            file_type = row[6]
            doc_category = row[7]

            if not chunk_text or not chunk_text.strip():
                continue

            chroma_id = f"{doc_id}_chunk_{chunk_index}"
            ids.append(chroma_id)
            texts.append(chunk_text)
            metadatas.append({
                "document_id": str(doc_id),
                "filename": filename or "",
                "file_type": file_type or "",
                "doc_category": doc_category or "",
                "chunk_index": chunk_index or 0,
                "section": chunk_meta.get("section", ""),
            })

        if not texts:
            continue

        # Generate embeddings
        logger.info(f"Embedding batch {i // BATCH_SIZE + 1}: {len(texts)} chunks...")
        embeddings = get_embeddings(texts)

        # Store in ChromaDB
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        total_stored += len(texts)
        logger.info(f"  Stored {total_stored}/{len(rows)} chunks")

    final_count = collection.count()
    logger.info(f"Done! ChromaDB now has {final_count} entries (was {existing_count})")


if __name__ == "__main__":
    asyncio.run(backfill())

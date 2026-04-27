"""
Reset all data for a fresh demo.

Run from the backend directory:
    python -m scripts.reset_all_data
"""

import os
import sys
import shutil
import asyncio
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

TABLES_TO_CLEAR = [
    "query_logs",
    "entity_relationships",
    "components",
    "entities",
    "document_chunks",
    "documents",
]


async def reset():
    from sqlalchemy import text
    from app.db.database import async_session

    # 1. Clear PostgreSQL tables (in dependency order)
    logger.info("=== Clearing PostgreSQL tables ===")
    async with async_session() as db:
        for table in TABLES_TO_CLEAR:
            try:
                result = await db.execute(text(f"DELETE FROM {table}"))
                await db.commit()
                logger.info(f"  Cleared {table}: {result.rowcount} rows deleted")
            except Exception as e:
                await db.rollback()
                logger.warning(f"  Skipped {table}: {e}")

    # 2. Clear ChromaDB data
    logger.info("=== Clearing ChromaDB ===")
    chroma_dir = os.path.join(os.path.dirname(__file__), "..", "chroma_data")
    chroma_dir = os.path.abspath(chroma_dir)
    if os.path.exists(chroma_dir):
        shutil.rmtree(chroma_dir)
        logger.info(f"  Deleted {chroma_dir}")
    else:
        logger.info("  No chroma_data directory found")

    # 3. Clear uploaded files
    logger.info("=== Clearing uploaded files ===")
    uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
    uploads_dir = os.path.abspath(uploads_dir)
    if os.path.exists(uploads_dir):
        count = sum(1 for f in os.listdir(uploads_dir) if os.path.isfile(os.path.join(uploads_dir, f)))
        shutil.rmtree(uploads_dir)
        os.makedirs(uploads_dir, exist_ok=True)
        logger.info(f"  Deleted {count} files from {uploads_dir}")
    else:
        logger.info("  No uploads directory found")

    logger.info("=== All data cleared! Ready for fresh demo. ===")


if __name__ == "__main__":
    print("\n⚠️  This will DELETE all documents, entities, components, embeddings, and uploaded files.")
    confirm = input("Type 'yes' to confirm: ")
    if confirm.strip().lower() == "yes":
        asyncio.run(reset())
    else:
        print("Cancelled.")

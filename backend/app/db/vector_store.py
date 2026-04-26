"""ChromaDB vector store client."""

import os
import chromadb
from app.config import get_settings

settings = get_settings()

_client = None


def get_chroma_client():
    """Get ChromaDB client. Uses local persistent storage if CHROMA_HOST is 'local', else HTTP."""
    global _client
    if _client is None:
        if settings.chroma_host == "local":
            persist_dir = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_data")
            os.makedirs(persist_dir, exist_ok=True)
            _client = chromadb.PersistentClient(path=persist_dir)
        else:
            _client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    return _client


def get_collection(name: str = "documents"):
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )

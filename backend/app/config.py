"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "Document Intelligence Platform"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://docuser:docpass@postgres:5432/docintell"
    database_url_sync: str = "postgresql://docuser:docpass@postgres:5432/docintell"

    # ChromaDB
    chroma_host: str = "chromadb"
    chroma_port: int = 8000

    # Groq (free tier — https://console.groq.com)
    groq_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    llm_model_mini: str = "llama-3.3-70b-versatile"
    llm_model_vision: str = "llama-3.2-11b-vision-preview"
    embedding_model: str = "all-MiniLM-L6-v2"

    # File storage
    upload_dir: str = "/app/uploads"
    max_upload_size_mb: int = 50

    # Processing
    ocr_confidence_threshold: float = 0.6
    classification_confidence_threshold: float = 0.6

    model_config = {"env_file": [".env", "../.env"], "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()

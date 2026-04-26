"""SQLAlchemy model for documents."""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, Float, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # digital_doc, scanned_doc, component_photo
    mime_type: Mapped[str | None] = mapped_column(String(100))
    doc_category: Mapped[str | None] = mapped_column(String(50))
    doc_category_secondary: Mapped[str | None] = mapped_column(String(50))
    category_confidence: Mapped[float | None] = mapped_column(Float)
    raw_text: Mapped[str | None] = mapped_column(Text)
    clean_text: Mapped[str | None] = mapped_column(Text)
    structure_metadata: Mapped[dict | None] = mapped_column(JSONB)
    ocr_confidence: Mapped[float | None] = mapped_column(Float)
    processing_status: Mapped[str] = mapped_column(String(20), default="pending")
    processing_error: Mapped[str | None] = mapped_column(Text)
    file_path: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    entities: Mapped[list["Entity"]] = relationship("Entity", back_populates="document", cascade="all, delete-orphan")
    components: Mapped[list["Component"]] = relationship("Component", back_populates="document", cascade="all, delete-orphan")
    chunks: Mapped[list["DocumentChunk"]] = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


from app.models.entity import Entity
from app.models.component import Component
from app.models.document_chunk import DocumentChunk

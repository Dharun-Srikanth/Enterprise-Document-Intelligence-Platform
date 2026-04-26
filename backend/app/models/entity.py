"""SQLAlchemy model for extracted entities."""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, Float, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"))
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_value: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_value: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    start_offset: Mapped[int | None] = mapped_column(Integer)
    end_offset: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    document: Mapped["Document"] = relationship("Document", back_populates="entities")
    source_relationships: Mapped[list["EntityRelationship"]] = relationship(
        "EntityRelationship", foreign_keys="EntityRelationship.source_entity_id", back_populates="source_entity", cascade="all, delete-orphan"
    )
    target_relationships: Mapped[list["EntityRelationship"]] = relationship(
        "EntityRelationship", foreign_keys="EntityRelationship.target_entity_id", back_populates="target_entity", cascade="all, delete-orphan"
    )


from app.models.document import Document
from app.models.entity_relationship import EntityRelationship

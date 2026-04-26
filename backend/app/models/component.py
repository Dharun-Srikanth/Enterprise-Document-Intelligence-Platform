"""SQLAlchemy model for tear-down components."""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, Float, DateTime, Boolean, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base
from decimal import Decimal


class Component(Base):
    __tablename__ = "components"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"))
    component_type: Mapped[str] = mapped_column(String(100), nullable=False)
    component_confidence: Mapped[float | None] = mapped_column(Float)
    material: Mapped[str | None] = mapped_column(String(100))
    material_confidence: Mapped[float | None] = mapped_column(Float)
    estimated_cost_low: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    estimated_cost_high: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    estimated_cost_mid: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    carbon_footprint_kg_co2e: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    emission_factor_source: Mapped[str | None] = mapped_column(String(200))
    overall_confidence: Mapped[float | None] = mapped_column(Float)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    flag_reason: Mapped[str | None] = mapped_column(Text)
    classification_metadata: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    document: Mapped["Document"] = relationship("Document", back_populates="components")


from app.models.document import Document

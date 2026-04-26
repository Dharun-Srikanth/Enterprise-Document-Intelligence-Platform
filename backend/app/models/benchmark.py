"""SQLAlchemy model for benchmark reference data."""

from sqlalchemy import String, Text, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base
from decimal import Decimal


class BenchmarkData(Base):
    __tablename__ = "benchmark_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    component_type: Mapped[str] = mapped_column(String(100), nullable=False)
    material: Mapped[str] = mapped_column(String(100), nullable=False)
    cost_low: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    cost_high: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    cost_unit: Mapped[str] = mapped_column(String(20), default="USD")
    carbon_footprint_kg_co2e: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    emission_factor_source: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)

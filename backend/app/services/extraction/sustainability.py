"""Sustainability estimator — cost and carbon footprint from benchmark data."""

import csv
import os
import logging
from dataclasses import dataclass, field
from decimal import Decimal

logger = logging.getLogger(__name__)

_benchmark_cache: list[dict] | None = None

BENCHMARK_CSV_PATHS = [
    "/app/data/benchmark.csv",  # Docker path
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "benchmark.csv"),
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "test_data", "benchmark.csv"),
]


@dataclass
class SustainabilityEstimate:
    component_type: str
    material: str
    cost_low: Decimal | None = None
    cost_high: Decimal | None = None
    cost_mid: Decimal | None = None
    cost_unit: str = "USD"
    carbon_footprint_kg_co2e: Decimal | None = None
    emission_factor_source: str | None = None
    match_found: bool = False
    notes: str | None = None


def load_benchmark_data() -> list[dict]:
    """Load benchmark CSV data. Cached after first load."""
    global _benchmark_cache
    if _benchmark_cache is not None:
        return _benchmark_cache

    for path in BENCHMARK_CSV_PATHS:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    _benchmark_cache = list(reader)
                    logger.info(f"Loaded {len(_benchmark_cache)} benchmark entries from {abs_path}")
                    return _benchmark_cache
            except Exception as e:
                logger.warning(f"Failed to load benchmark from {abs_path}: {e}")

    logger.warning("No benchmark CSV found in any expected path")
    _benchmark_cache = []
    return _benchmark_cache


def estimate_sustainability(
    component_type: str,
    material: str,
) -> SustainabilityEstimate:
    """
    Look up cost and carbon footprint from benchmark data.

    Args:
        component_type: Classified component type (e.g. 'seat_track_assembly')
        material: Classified material type (e.g. 'cold_rolled_steel')

    Returns:
        SustainabilityEstimate with cost range and carbon footprint
    """
    data = load_benchmark_data()

    # Exact match
    for row in data:
        if (row.get("component_type", "").strip().lower() == component_type.lower() and
                row.get("material", "").strip().lower() == material.lower()):
            return _row_to_estimate(row, component_type, material)

    # Fuzzy match on component type only
    for row in data:
        if row.get("component_type", "").strip().lower() == component_type.lower():
            estimate = _row_to_estimate(row, component_type, material)
            estimate.notes = f"Material '{material}' not found; using closest match: {row.get('material')}"
            estimate.material = row.get("material", material)
            return estimate

    # No match at all
    return SustainabilityEstimate(
        component_type=component_type,
        material=material,
        match_found=False,
        notes=f"No benchmark data found for {component_type} / {material}",
    )


def _row_to_estimate(row: dict, component_type: str, material: str) -> SustainabilityEstimate:
    """Convert a CSV row to SustainabilityEstimate."""
    try:
        cost_low = Decimal(str(row.get("cost_low", "0")).strip()) if row.get("cost_low") else None
        cost_high = Decimal(str(row.get("cost_high", "0")).strip()) if row.get("cost_high") else None
        cost_mid = (cost_low + cost_high) / 2 if cost_low and cost_high else None
        carbon = Decimal(str(row.get("carbon_footprint_kg_co2e", "0")).strip()) if row.get("carbon_footprint_kg_co2e") else None
    except Exception as e:
        logger.warning(f"Failed to parse benchmark row: {e}")
        return SustainabilityEstimate(
            component_type=component_type,
            material=material,
            match_found=False,
            notes=f"Parse error: {e}",
        )

    return SustainabilityEstimate(
        component_type=component_type,
        material=material,
        cost_low=cost_low,
        cost_high=cost_high,
        cost_mid=cost_mid,
        cost_unit=row.get("cost_unit", "USD").strip(),
        carbon_footprint_kg_co2e=carbon,
        emission_factor_source=row.get("emission_factor_source", "").strip() or None,
        match_found=True,
        notes=row.get("notes", "").strip() or None,
    )


def get_all_benchmarks() -> list[SustainabilityEstimate]:
    """Return all benchmark entries as SustainabilityEstimate objects."""
    data = load_benchmark_data()
    return [
        _row_to_estimate(row, row.get("component_type", ""), row.get("material", ""))
        for row in data
    ]

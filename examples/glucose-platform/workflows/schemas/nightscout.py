"""Pandera schemas for Nightscout glucose data validation.

Raw layer schemas are defined manually.
Fact layer schema is GENERATED from dbt model YAML (single source of truth).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pandera.pandas import Field
from phlo_quality.schemas import PhloSchema, dbt_model_to_pandera

# Validation constants
VALID_DIRECTIONS = [
    "Flat",
    "FortyFiveUp",
    "FortyFiveDown",
    "SingleUp",
    "SingleDown",
    "DoubleUp",
    "DoubleDown",
    "NONE",
]


# =============================================================================
# RAW LAYER - Manual schemas (internal, not published)
# =============================================================================


class RawGlucoseEntries(PhloSchema):
    """Schema for raw Nightscout glucose entries from the API."""

    _id: str = Field(unique=True)
    sgv: int = Field(ge=1, le=1000)
    date: int
    date_string: datetime
    direction: str | None = Field(isin=VALID_DIRECTIONS)
    device: str | None
    type: str | None


# =============================================================================
# FACT LAYER - Generated from dbt model YAML (single source of truth)
# =============================================================================

_dbt_model_path = (
    Path(__file__).parent.parent.parent
    / "transforms"
    / "dbt"
    / "models"
    / "silver"
    / "fct_glucose_readings.yml"
)
FactGlucoseReadings = dbt_model_to_pandera(_dbt_model_path, "fct_glucose_readings")


# =============================================================================
# GOLD LAYER - Manual schema (complex aggregations)
# =============================================================================


class FactDailyGlucoseMetrics(PhloSchema):
    """Schema for the fct_daily_glucose_metrics table (gold layer)."""

    class Config:
        strict = True
        coerce = True

    reading_date: datetime = Field(unique=True)
    day_name: str = Field(
        isin=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    )
    day_of_week: int = Field(ge=1, le=7)
    week_of_year: int = Field(ge=1, le=53)
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=2100)
    reading_count: int = Field(ge=0)
    avg_glucose_mg_dl: float | None = Field(ge=0, le=1000)
    min_glucose_mg_dl: int | None = Field(ge=0, le=1000)
    max_glucose_mg_dl: int | None = Field(ge=0, le=1000)
    stddev_glucose_mg_dl: float | None = Field(ge=0)
    time_in_range_pct: float | None = Field(ge=0, le=100)
    time_below_range_pct: float | None = Field(ge=0, le=100)
    time_above_range_pct: float | None = Field(ge=0, le=100)
    estimated_a1c_pct: float | None = Field(ge=0, le=20)

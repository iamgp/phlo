from __future__ import annotations

from datetime import datetime

from dagster_pandera import pandera_schema_to_dagster_type
from pandera.pandas import DataFrameModel, Field

# Constants for validation
MIN_GLUCOSE_MG_DL = 20  # Minimum physiologically possible glucose reading
MAX_GLUCOSE_MG_DL = 600  # Maximum CGM meter reading

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


class FactGlucoseReadings(DataFrameModel):
    """
    Schema for the fact_glucose_readings table.

    Validates processed Nightscout glucose data including:
    - Valid glucose ranges (20-600 mg/dL)
    - Proper timestamp formatting
    - Valid direction indicators
    - Time dimension fields (hour, day of week)
    - Glucose categorization
    """

    entry_id: str = Field(
        nullable=False,
        unique=True,
        description="Unique identifier for each glucose reading entry",
    )

    glucose_mg_dl: int = Field(
        ge=MIN_GLUCOSE_MG_DL,
        le=MAX_GLUCOSE_MG_DL,
        nullable=False,
        description=f"Blood glucose level in mg/dL (valid range: {MIN_GLUCOSE_MG_DL}-{MAX_GLUCOSE_MG_DL})",
    )

    reading_timestamp: datetime = Field(
        nullable=False,
        description="Timestamp when the glucose reading was taken",
    )

    direction: str | None = Field(
        isin=VALID_DIRECTIONS,
        nullable=True,
        description="Trend direction of glucose levels (e.g., 'SingleUp', 'Flat')",
    )

    hour_of_day: int = Field(
        ge=0,
        le=23,
        nullable=False,
        description="Hour of day when reading was taken (0-23)",
    )

    day_of_week: int = Field(
        ge=0,
        le=6,
        nullable=False,
        description="Day of week (0=Monday, 6=Sunday)",
    )

    glucose_category: str = Field(
        isin=["hypoglycemia", "in_range", "hyperglycemia_mild", "hyperglycemia_severe"],
        nullable=False,
        description="Categorized glucose level based on ADA guidelines",
    )

    is_in_range: int = Field(
        isin=[0, 1],
        nullable=False,
        description="Whether glucose level is within target range (0=no, 1=yes)",
    )

    class Config:
        strict = True  # No additional columns allowed
        coerce = True  # Auto type coercion where possible


# Lazy-load Dagster type to avoid import-time overhead
_dagster_type_cache = None


def get_fact_glucose_dagster_type():
    """Get or create the Dagster type from Pandera schema."""
    global _dagster_type_cache
    if _dagster_type_cache is None:
        _dagster_type_cache = pandera_schema_to_dagster_type(FactGlucoseReadings)
    return _dagster_type_cache

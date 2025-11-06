# glucose.py - Pandera schemas for validating glucose monitoring data in the data pipeline
# Defines data quality checks and type validation for processed glucose readings
# Used by Dagster asset checks to ensure data integrity across transformations

from __future__ import annotations

from datetime import datetime

from dagster_pandera import pandera_schema_to_dagster_type
from pandera.pandas import DataFrameModel, Field

# --- Validation Constants ---
# Constants used for glucose data validation rules
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


# --- Pandera Schemas ---
# DataFrame schemas for validating structured data in the pipeline

class RawGlucoseEntries(DataFrameModel):
    """
    Schema for raw Nightscout glucose entries from the API.

    Validates raw glucose data at ingestion time before dbt transformation:
    - Valid glucose ranges (1-1000 mg/dL for raw data, wider than fact table)
    - Proper field types and nullability
    - Required metadata fields
    - Unique entry IDs
    """

    _id: str = Field(
        nullable=False,
        unique=True,
        description="Nightscout entry ID (unique identifier)",
    )

    sgv: int = Field(
        ge=1,
        le=1000,
        nullable=False,
        description="Sensor glucose value in mg/dL (1-1000 for raw data)",
    )

    date: int = Field(
        nullable=False,
        description="Unix timestamp in milliseconds",
    )

    date_string: datetime = Field(
        nullable=False,
        description="ISO 8601 timestamp",
    )

    direction: str | None = Field(
        isin=VALID_DIRECTIONS,
        nullable=True,
        description="Trend direction (e.g., 'SingleUp', 'Flat')",
    )

    device: str | None = Field(
        nullable=True,
        description="Device name that recorded the entry",
    )

    type: str | None = Field(
        nullable=True,
        description="Entry type (e.g., 'sgv')",
    )

    _cascade_ingested_at: datetime = Field(
        nullable=False,
        description="Timestamp when data was ingested by Cascade",
    )

    class Config:
        strict = False  # Allow DLT metadata fields
        coerce = True


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
        description=(
            f"Blood glucose level in mg/dL (valid range: {MIN_GLUCOSE_MG_DL}-{MAX_GLUCOSE_MG_DL})"
        ),
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


class FactDailyGlucoseMetrics(DataFrameModel):
    """
    Schema for the fct_daily_glucose_metrics table.

    Validates daily aggregated glucose metrics:
    - Daily statistics (avg, min, max, stddev)
    - Time in range percentages
    - Estimated A1C
    - Time dimensions
    """

    reading_date: datetime = Field(
        nullable=False,
        unique=True,
        description="Date of glucose readings (unique per day)",
    )

    day_name: str = Field(
        nullable=False,
        isin=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        description="Name of the day",
    )

    day_of_week: int = Field(
        ge=1,
        le=7,
        nullable=False,
        description="Day of week (1=Monday, 7=Sunday)",
    )

    week_of_year: int = Field(
        ge=1,
        le=53,
        nullable=False,
        description="Week of the year (1-53)",
    )

    month: int = Field(
        ge=1,
        le=12,
        nullable=False,
        description="Month number (1-12)",
    )

    year: int = Field(
        ge=2000,
        le=2100,
        nullable=False,
        description="Year (2000-2100 reasonable range)",
    )

    reading_count: int = Field(
        ge=0,
        nullable=False,
        description="Number of readings for the day",
    )

    avg_glucose_mg_dl: float | None = Field(
        ge=0,
        le=1000,
        nullable=True,
        description="Average glucose level for the day",
    )

    min_glucose_mg_dl: int | None = Field(
        ge=0,
        le=1000,
        nullable=True,
        description="Minimum glucose level for the day",
    )

    max_glucose_mg_dl: int | None = Field(
        ge=0,
        le=1000,
        nullable=True,
        description="Maximum glucose level for the day",
    )

    stddev_glucose_mg_dl: float | None = Field(
        ge=0,
        nullable=True,
        description="Standard deviation of glucose levels",
    )

    time_in_range_pct: float | None = Field(
        ge=0,
        le=100,
        nullable=True,
        description="Percentage of time in target range (70-180 mg/dL)",
    )

    time_below_range_pct: float | None = Field(
        ge=0,
        le=100,
        nullable=True,
        description="Percentage of time below range (<70 mg/dL)",
    )

    time_above_range_pct: float | None = Field(
        ge=0,
        le=100,
        nullable=True,
        description="Percentage of time above range (>180 mg/dL)",
    )

    estimated_a1c_pct: float | None = Field(
        ge=0,
        le=20,
        nullable=True,
        description="Estimated A1C percentage (GMI approximation)",
    )

    class Config:
        strict = True  # No additional columns allowed
        coerce = True  # Auto type coercion where possible


# --- Dagster Type Conversion ---
# Caching and conversion utilities for Dagster integration
# Lazy-load Dagster type to avoid import-time overhead
_dagster_type_cache = None


# --- Helper Functions ---
# Utility functions for schema integration
def get_fact_glucose_dagster_type():
    """Get or create the Dagster type from Pandera schema."""
    global _dagster_type_cache
    if _dagster_type_cache is None:
        _dagster_type_cache = pandera_schema_to_dagster_type(FactGlucoseReadings)
    return _dagster_type_cache

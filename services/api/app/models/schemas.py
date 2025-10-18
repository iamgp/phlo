from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


# Auth Models
class LoginRequest(BaseModel):
    """Login request."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict[str, Any]


# Glucose Models
class GlucoseReading(BaseModel):
    """Individual glucose reading."""

    timestamp: datetime
    glucose_mg_dl: float = Field(..., alias="sgv")
    direction: str | None = None
    device: str | None = None


class DailySummary(BaseModel):
    """Daily glucose summary."""

    date: date
    avg_glucose: float | None = None
    min_glucose: float | None = None
    max_glucose: float | None = None
    readings_count: int | None = None
    time_in_range_percent: float | None = None


class HourlyPattern(BaseModel):
    """Hourly glucose pattern."""

    hour_of_day: int
    avg_glucose: float | None = None
    readings_count: int | None = None


# Iceberg Models
class IcebergTable(BaseModel):
    """Iceberg table metadata."""

    schema_name: str
    table_name: str
    location: str | None = None


class QueryRequest(BaseModel):
    """SQL query request."""

    query: str = Field(..., max_length=10000)
    engine: str = Field("trino", pattern="^(trino|postgres)$")
    limit: int | None = Field(None, le=10000)


class QueryResponse(BaseModel):
    """SQL query response."""

    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    execution_time_ms: float


# Metadata Models
class TableFreshness(BaseModel):
    """Table freshness information."""

    table_name: str
    last_updated: datetime | None = None
    is_fresh: bool
    freshness_threshold_hours: int


class PipelineStatus(BaseModel):
    """Pipeline status."""

    pipeline_name: str
    last_run: datetime | None = None
    status: str
    next_scheduled_run: datetime | None = None

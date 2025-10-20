# asset_outputs.py - Pydantic models for Dagster asset output structures
# Defines the expected output schemas for various pipeline stages, used for
# validation and metadata tracking of asset materialization results

from __future__ import annotations

from pydantic import BaseModel, Field


# --- Asset Output Models ---
# Pydantic models defining the structure of outputs from different pipeline assets
class RawDataOutput(BaseModel):
    """Output model for raw data ingestion assets."""

    status: str = Field(
        ...,
        description="Status of the raw data: 'available' or 'no_data'",
    )
    path: str = Field(
        ...,
        description="Path to the raw data directory",
    )
    file_count: int = Field(
        default=0,
        ge=0,
        description="Total number of parquet files found",
    )
    files: list[str] = Field(
        default_factory=list,
        description="List of file names (up to 10 for display)",
        max_length=10,
    )


class TablePublishStats(BaseModel):
    """Statistics for a published table."""

    row_count: int = Field(
        ...,
        ge=0,
        description="Number of rows in the published table",
    )
    column_count: int = Field(
        ...,
        ge=0,
        description="Number of columns in the published table",
    )


class PublishPostgresOutput(BaseModel):
    """Output model for Trino to Postgres publishing assets."""

    tables: dict[str, TablePublishStats] = Field(
        ...,
        description="Publishing statistics for each table",
    )

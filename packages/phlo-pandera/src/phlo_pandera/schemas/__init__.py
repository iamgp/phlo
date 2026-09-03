"""Schemas module initialization.

This module provides base schemas and utilities for data validation using
Pandera. It exposes the PhloSchema base class and output schema models used
across the Phlo ecosystem.

Available Components:
    - **PhloSchema**: Base Pandera DataFrameModel with phlo smart defaults
    - **PublishPostgresOutput**: Pydantic model for table publishing results
    - **RawDataOutput**: Pydantic model for raw data ingestion results
    - **TablePublishStats**: Statistics for published tables

Example:
    ```python
    from phlo_pandera.schemas import PhloSchema
    from pandera.pandas import Field

    class CustomerDimensions(PhloSchema):
        customer_id: int = Field(unique=True)
        email: str | None = Field(nullable=True)
        created_at: str
        # No Config needed - defaults from PhloSchema are applied automatically
    ```

See Also:
    - ``schemas/base.py``: PhloSchema implementation
    - ``schemas/asset_outputs.py``: Output model definitions

"""

from __future__ import annotations

from phlo_pandera.schemas.asset_outputs import (
    PublishPostgresOutput,
    RawDataOutput,
    TablePublishStats,
)
from phlo_pandera.schemas.base import PhloSchema

# Public API
__all__ = [
    "PhloSchema",
    "PublishPostgresOutput",
    "RawDataOutput",
    "TablePublishStats",
]

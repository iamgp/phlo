"""
Pandera Schema Template

This template shows how to create a Pandera DataFrameModel for data validation.

TODO: Customize this template:
1. Rename the class to match your data (e.g., RawWeatherData, RawSalesTransactions)
2. Add fields that match your API/database columns
3. Set appropriate types and constraints
4. Add descriptions for documentation
"""

import pandera as pa
from pandera.typing import Series


class RawExampleData(pa.DataFrameModel):
    """
    Schema for raw example data.

    TODO: Update this docstring to describe your data source.
    Example: "Schema for raw weather observations from OpenWeather API."
    """

    # TODO: Replace these example fields with your actual data fields

    # Unique identifier (required for deduplication)
    id: Series[str] = pa.Field(
        nullable=False,
        description="Unique identifier for the record",
    )

    # Timestamp field (common in most datasets)
    timestamp: Series[str] = pa.Field(
        nullable=False,
        description="ISO 8601 timestamp of the event",
    )

    # String field example
    name: Series[str] = pa.Field(
        nullable=True,  # Optional field
        description="Name or description of the entity",
    )

    # Numeric field with constraints
    value: Series[float] = pa.Field(
        ge=0,  # Greater than or equal to 0
        le=1000,  # Less than or equal to 1000
        nullable=False,
        description="Numeric value with range validation",
    )

    # Integer field example
    count: Series[int] = pa.Field(
        ge=0,
        nullable=False,
        description="Count or quantity (non-negative integer)",
    )

    # Boolean field example
    is_active: Series[bool] = pa.Field(
        nullable=False,
        description="Active status flag",
    )

    # Optional field example
    notes: Series[str] = pa.Field(
        nullable=True,  # Can be null
        description="Optional notes or comments",
    )

    class Config:
        """
        Pandera configuration.

        strict: If True, columns not in schema will cause validation failure
        coerce: If True, attempt to coerce column types
        """

        strict = True  # Reject extra columns
        coerce = True  # Auto-convert types when possible


# TODO: If you need multiple schemas (e.g., for different API endpoints),
# define them here:


class RawExampleDataAlternative(pa.DataFrameModel):
    """Alternative schema for different data structure."""

    record_id: Series[str] = pa.Field(
        nullable=False,
        description="Alternative unique identifier",
    )

    created_at: Series[str] = pa.Field(
        nullable=False,
        description="Creation timestamp",
    )

    # Add your fields here...

    class Config:
        strict = True
        coerce = True


# Tips for defining schemas:
#
# 1. TYPES:
#    - str: String/text data
#    - int: Whole numbers
#    - float: Decimal numbers
#    - bool: True/False
#    - datetime: For date/time (Note: often APIs return strings, not datetime objects)
#
# 2. CONSTRAINTS:
#    - ge=n: Greater than or equal to n
#    - le=n: Less than or equal to n
#    - gt=n: Greater than n
#    - lt=n: Less than n
#    - isin=[...]: Value must be in list
#    - nullable=True/False: Whether None/null is allowed
#
# 3. DESCRIPTIONS:
#    - Always add descriptions - they appear in Iceberg table metadata
#    - Use clear, concise descriptions
#    - Example: "Customer email address" not just "email"
#
# 4. ICEBERG SCHEMA GENERATION:
#    - Pandera schema is AUTO-CONVERTED to PyIceberg schema
#    - No need to define Iceberg schema separately
#    - Field descriptions become Iceberg column docs
#
# 5. VALIDATION:
#    - Pandera validates BEFORE writing to Iceberg
#    - Invalid rows are logged but ingestion continues (with warning)
#    - Check Dagster logs for validation failures
#
# 6. COMMON PATTERNS:
#
#    # Percentage (0-100)
#    percentage: Series[float] = pa.Field(ge=0, le=100, description="Percentage value")
#
#    # Email
#    email: Series[str] = pa.Field(
#        str_matches=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
#        description="Email address"
#    )
#
#    # Enum/Category
#    status: Series[str] = pa.Field(
#        isin=["pending", "active", "completed", "failed"],
#        description="Status code"
#    )
#
#    # Positive number
#    amount: Series[float] = pa.Field(gt=0, description="Transaction amount (USD)")
#
#    # Unix timestamp
#    unix_timestamp: Series[int] = pa.Field(ge=0, description="Unix epoch timestamp")

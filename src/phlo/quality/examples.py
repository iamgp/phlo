"""
Examples of using the @phlo.quality decorator.

This module demonstrates all quality check types and decorator patterns.
"""


import phlo
from phlo.quality import (
    CountCheck,
    CustomSQLCheck,
    FreshnessCheck,
    NullCheck,
    RangeCheck,
    UniqueCheck,
)


# Example 1: Basic quality checks with NullCheck and RangeCheck
@phlo.quality(
    table="bronze.weather_observations",
    checks=[
        NullCheck(columns=["station_id", "temperature"]),
        RangeCheck(column="temperature", min_value=-50, max_value=60),
    ],
    group="weather",
)
def weather_quality_basic():
    """Quality checks for weather observations."""
    pass


# Example 2: Comprehensive quality checks with multiple types
@phlo.quality(
    table="bronze.sensor_readings",
    checks=[
        # No nulls in critical columns
        NullCheck(columns=["sensor_id", "reading_value", "timestamp"]),
        # Values within expected range
        RangeCheck(column="reading_value", min_value=0, max_value=100),
        # Data is fresh (< 2 hours old)
        FreshnessCheck(timestamp_column="timestamp", max_age_hours=2),
        # Sensor IDs are unique per timestamp
        UniqueCheck(columns=["sensor_id", "timestamp"]),
        # At least 100 readings expected
        CountCheck(min_rows=100),
    ],
    group="sensors",
    blocking=True,
)
def sensor_quality_comprehensive():
    """Comprehensive quality checks for sensor readings."""
    pass


# Example 3: Permissive thresholds (allow some failures)
@phlo.quality(
    table="bronze.customer_data",
    checks=[
        # Allow up to 5% null values in optional fields
        NullCheck(columns=["phone", "address"], allow_threshold=0.05),
        # Allow up to 1% out-of-range values
        RangeCheck(column="age", min_value=0, max_value=150, allow_threshold=0.01),
        # Allow up to 0.5% duplicates
        UniqueCheck(columns=["customer_id"], allow_threshold=0.005),
    ],
    group="crm",
    warn_threshold=0.3,  # Warn if more than 30% of checks fail
)
def customer_quality_permissive():
    """Quality checks for customer data with permissive thresholds."""
    pass


# Example 4: Custom SQL checks
@phlo.quality(
    table="bronze.transactions",
    checks=[
        NullCheck(columns=["transaction_id", "amount"]),
        # Custom check: amount must be positive
        CustomSQLCheck(
            name_="positive_amount",
            sql="SELECT (amount > 0) AS is_valid FROM data",
        ),
        # Custom check: end_date must be after start_date
        CustomSQLCheck(
            name_="date_consistency",
            sql="SELECT (end_date >= start_date) AS is_valid FROM data",
        ),
    ],
    group="payments",
)
def transaction_quality_custom():
    """Quality checks for transactions with custom SQL validation."""
    pass


# Example 5: Schema validation with Pandera
@phlo.quality(
    table="silver.customer_dimensions",
    checks=[
        # Note: Requires schema to be defined in phlo.schemas
        # SchemaCheck(schema=CustomerDimensionsSchema),
    ],
    group="dimensions",
    blocking=True,
)
def customer_dims_quality_schema():
    """Quality checks using Pandera schema validation."""
    pass


# Example 6: Partitioned data with freshness check
@phlo.quality(
    table="bronze.glucose_entries",
    checks=[
        NullCheck(columns=["sgv", "timestamp"]),
        RangeCheck(column="sgv", min_value=20, max_value=600),
        FreshnessCheck(timestamp_column="timestamp", max_age_hours=24),
    ],
    group="nightscout",
    blocking=True,
)
def glucose_quality_partitioned():
    """Quality checks for partitioned glucose data."""
    pass


# Example 7: DuckDB backend (for local testing)
@phlo.quality(
    table="local.test_data",
    checks=[
        NullCheck(columns=["id", "value"]),
        CountCheck(min_rows=1, max_rows=1000),
    ],
    group="testing",
    backend="duckdb",
)
def test_quality_duckdb():
    """Quality checks using DuckDB backend."""
    pass


# Example 8: Complex business logic validation
@phlo.quality(
    table="silver.order_details",
    checks=[
        # Data quality
        NullCheck(columns=["order_id", "product_id", "quantity", "unit_price"]),
        CountCheck(min_rows=0),  # Allow empty

        # Value validation
        RangeCheck(column="quantity", min_value=1, max_value=10000),
        RangeCheck(column="unit_price", min_value=0, max_value=1000000),

        # Business rules
        CustomSQLCheck(
            name_="valid_total",
            sql="SELECT (quantity * unit_price = total_price) FROM data",
        ),
        CustomSQLCheck(
            name_="valid_discount",
            sql="SELECT (discount_percent BETWEEN 0 AND 100) FROM data",
        ),

        # Uniqueness
        UniqueCheck(columns=["order_id", "line_item_number"]),
    ],
    group="sales",
    warn_threshold=0.1,  # Warn if more than 10% fail
)
def order_quality_business_rules():
    """Quality checks for orders with business rule validation."""
    pass


def demo_decorator_benefits():
    """
    Demonstrate the benefits of @phlo.quality decorator.

    BEFORE (Manual, ~40 lines of boilerplate):
    ```python
    from dagster import AssetCheckResult, AssetKey, MetadataValue, asset_check
    import pandas as pd

    @asset_check(name="weather_quality", asset=AssetKey(["weather_observations"]), blocking=True)
    def weather_quality_check(context, trino) -> AssetCheckResult:
        with trino.cursor() as cursor:
            cursor.execute("SELECT * FROM bronze.weather_observations")
            df = pd.DataFrame(cursor.fetchall(), columns=[d[0] for d in cursor.description])

        null_count = df['station_id'].isna().sum()
        if null_count > 0:
            return AssetCheckResult(passed=False, metadata={"error": f"{null_count} nulls"})

        violations = ((df['temperature'] < -50) | (df['temperature'] > 60)).sum()
        if violations > 0:
            return AssetCheckResult(passed=False, metadata={"error": f"{violations} out-of-range"})

        return AssetCheckResult(passed=True, metadata={"rows": len(df)})
    ```

    AFTER (With @phlo.quality, 8 lines - 80% reduction!):
    ```python
    import phlo
    from phlo.quality import NullCheck, RangeCheck

    @phlo.quality(
        table="bronze.weather_observations",
        checks=[
            NullCheck(columns=["station_id", "temperature"]),
            RangeCheck(column="temperature", min_value=-50, max_value=60),
        ],
    )
    def weather_quality():
        pass
    ```
    """
    pass

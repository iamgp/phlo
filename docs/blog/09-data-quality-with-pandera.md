# Part 9: Data Quality—Pandera Schemas and Asset Checks

In Part 8, we built a complete pipeline. But how do we ensure data quality throughout? This post covers validation at multiple layers.

## The Data Quality Problem

Without validation, bad data silently propagates:

```python
# This data is... problematic
glucose_reading = {
    "glucose_mg_dl": -50,  # Negative? Impossible
    "timestamp": "2024-13-45",  # Invalid date
    "device": None,  # Required field missing
    "reading_type": "unknown",  # Invalid enum
}

# Query downstream just sees rows
# Dashboard shows glucose values from -50 to 5000
# Alerts fire for impossible "low" readings
```

## Three Layers of Validation

Phlo uses validation at three points:

```
API Data
    ↓
[1] Ingestion: Pandera schema validation
    ↓
DLT Staging Tables
    ↓
[2] dbt Tests: Business logic validation
    ↓
Iceberg/Postgres Marts
    ↓
[3] Dagster Asset Checks: Runtime monitoring
    ↓
Dashboards/Alerts
```

## Layer 1: Pandera Schemas (Ingestion)

Pandera provides type-safe validation with detailed error reporting.

### Setting Up a Schema

Phlo uses Pandera's DataFrameModel approach for cleaner, class-based schemas:

```python
# File: examples/glucose-platform/workflows/schemas/nightscout.py
from pandera.pandas import DataFrameModel, Field

# Validation constants
MIN_GLUCOSE_MG_DL = 20
MAX_GLUCOSE_MG_DL = 600

VALID_DIRECTIONS = [
    "Flat", "FortyFiveUp", "FortyFiveDown",
    "SingleUp", "SingleDown", "DoubleUp", "DoubleDown", "NONE"
]


class RawGlucoseEntries(DataFrameModel):
    """
    Schema for raw Nightscout glucose entries from the API.

    Validates raw glucose data at ingestion time:
    - Valid glucose ranges (1-1000 mg/dL for raw data)
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

    class Config:
        strict = False  # Allow DLT metadata fields
        coerce = True


class FactGlucoseReadings(DataFrameModel):
    """
    Schema for the fct_glucose_readings table (silver layer).

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
        description=f"Blood glucose in mg/dL ({MIN_GLUCOSE_MG_DL}-{MAX_GLUCOSE_MG_DL})",
    )

    reading_timestamp: datetime = Field(
        nullable=False,
        description="Timestamp when the glucose reading was taken",
    )

    hour_of_day: int = Field(
        ge=0,
        le=23,
        nullable=False,
        description="Hour of day when reading was taken (0-23)",
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
        strict = True
        coerce = True
```

### Using Pandera in @phlo_ingestion

The `@phlo_ingestion` decorator automatically validates data with Pandera schemas:

```python
# File: examples/glucose-platform/workflows/ingestion/nightscout/readings.py

import phlo
from dlt.sources.rest_api import rest_api
from workflows.schemas.nightscout import RawGlucoseEntries

@phlo_ingestion(
    table_name="glucose_entries",
    unique_key="_id",
    validation_schema=RawGlucoseEntries,  # Automatic validation
    group="nightscout",
    cron="0 */1 * * *",
    freshness_hours=(1, 24),
)
def glucose_entries(partition_date: str):
    """
    Ingest Nightscout glucose entries with automatic validation.

    The decorator validates data against RawGlucoseEntries schema:
    - Checks all field types and constraints
    - Validates glucose ranges (1-1000 for raw)
    - Ensures unique entry IDs
    - Logs validation failures with details
    """
    start_time_iso = f"{partition_date}T00:00:00.000Z"
    end_time_iso = f"{partition_date}T23:59:59.999Z"

    source = rest_api(
        client={"base_url": "https://gwp-diabetes.fly.dev/api/v1"},
        resources=[
            {
                "name": "entries",
                "endpoint": {
                    "path": "entries.json",
                    "params": {
                        "count": 10000,
                        "find[dateString][$gte]": start_time_iso,
                        "find[dateString][$lt]": end_time_iso,
                    },
                },
            }
        ],
    )

    return source
```

### Detailed Error Messages

When validation fails, Pandera provides actionable feedback:

```
SchemaError: Column 'sgv' has an out-of-range value:

  row_num  sgv
       42  -50   ← Glucose -50? Impossible

  Check failed: lambda x: (x >= 20) & (x <= 600)
  Glucose must be 20-600 mg/dL

Failure counts:
  Total: 3 failures
  Unique values failing: 1
```

This helps you:
- Identify exact problematic rows
- Understand which rule failed
- Decide: drop, fix, or investigate

## Layer 2: dbt Tests (Transformations)

After ingestion, dbt tests validate business logic during transformations.

### Schema Tests (YAML-based)

```yaml
# transforms/dbt/models/bronze/stg_glucose_entries.yml
version: 2

models:
  - name: stg_glucose_entries
    description: Staged glucose entries with basic cleaning
    
    columns:
      - name: entry_id
        description: Unique identifier
        tests:
          - unique
          - not_null
      
      - name: glucose_mg_dl
        description: Glucose in mg/dL
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 20
              max_value: 600
              strictly: false
          - dbt_expectations.expect_column_values_to_match_regex:
              regex: "^\\d+$"
      
      - name: timestamp_iso
        description: ISO 8601 timestamp
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: "timestamp_iso ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T'"
      
      - name: device_type
        description: Device type (enum)
        tests:
          - not_null
          - accepted_values:
              values: ['dexcom', 'freestyle', 'medtronic']
```

### Custom Tests (SQL)

```sql
-- transforms/dbt/tests/no_duplicate_readings.sql
-- Test: Ensure no duplicate readings within 5 minutes

SELECT
  device_type,
  COUNT(*) as reading_count,
  MIN(timestamp_iso) as earliest,
  MAX(timestamp_iso) as latest
FROM {{ ref('stg_glucose_entries') }}
GROUP BY
  device_type,
  DATE_TRUNC('5 minutes', timestamp_iso)
HAVING COUNT(*) > 1
```

If this query returns rows, the test fails (duplicates found).

### Running dbt Tests

```bash
# Test all transformations
dbt test --select stg_glucose_entries

# Test specific column
dbt test --select stg_glucose_entries.unique:entry_id

# Show detailed failure output
dbt test --select stg_glucose_entries --debug
```

## Layer 3: Dagster Asset Checks (Runtime)

After orchestration, Dagster asset checks monitor data quality in production. Phlo provides **two approaches**: the declarative `@phlo_quality` decorator and traditional `@asset_check` for custom logic.

### Approach 1: @phlo_quality Decorator (Declarative)

For common checks (null, range, freshness), use the `@phlo_quality` decorator to reduce boilerplate by 70-80%:

```python
# File: examples/glucose-platform/workflows/quality/nightscout.py

import phlo
from phlo_quality import NullCheck, RangeCheck, FreshnessCheck

@phlo_quality(
    table="silver.fct_glucose_readings",
    checks=[
        NullCheck(columns=["entry_id", "glucose_mg_dl", "reading_timestamp"]),
        RangeCheck(column="glucose_mg_dl", min_value=20, max_value=600),
        RangeCheck(column="hour_of_day", min_value=0, max_value=23),
        FreshnessCheck(column="reading_timestamp", max_age_hours=24),
    ],
    group="nightscout",
    blocking=True,
)
def glucose_readings_quality():
    """Declarative quality checks for glucose readings using @phlo_quality."""
    pass


@phlo_quality(
    table="gold.fct_daily_glucose_metrics",
    checks=[
        NullCheck(columns=["reading_date", "reading_count", "avg_glucose_mg_dl"]),
        RangeCheck(column="avg_glucose_mg_dl", min_value=20, max_value=600),
        RangeCheck(column="time_in_range_pct", min_value=0, max_value=100),
    ],
    group="nightscout",
    blocking=True,
)
def daily_metrics_quality():
    """Declarative quality checks for daily glucose metrics."""
    pass
```

### Approach 2: Traditional @asset_check (Custom Logic)

For complex validation with Pandera schemas or custom business logic:

```python
# File: examples/glucose-platform/workflows/quality/nightscout.py

from dagster import AssetCheckResult, AssetKey, asset_check
from phlo_trino.resource import TrinoResource
from workflows.schemas.nightscout import FactGlucoseReadings
import pandera.errors


@asset_check(
    name="nightscout_glucose_quality",
    asset=AssetKey(["fct_glucose_readings"]),
    blocking=True,
    description="Validate processed Nightscout glucose data using Pandera schema validation.",
)
def nightscout_glucose_quality_check(context, trino: TrinoResource) -> AssetCheckResult:
    """
    Quality check using Pandera for type-safe schema validation.

    Validates glucose readings against the FactGlucoseReadings schema,
    checking data types, ranges, and business rules directly against Iceberg via Trino.
    """
    query = """
    SELECT
        entry_id,
        glucose_mg_dl,
        reading_timestamp,
        direction,
        hour_of_day,
        day_of_week,
        glucose_category,
        is_in_range
    FROM iceberg_dev.silver.fct_glucose_readings
    """

    partition_key = getattr(context, "partition_key", None)
    if partition_key:
        query = f"{query}\nWHERE DATE(reading_timestamp) = DATE '{partition_key}'"
        context.log.info(f"Validating partition: {partition_key}")

    try:
        with trino.cursor(schema="silver") as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

        fact_df = pd.DataFrame(rows, columns=columns)

        # Type conversions
        fact_df["glucose_mg_dl"] = fact_df["glucose_mg_dl"].astype("int64")
        fact_df["hour_of_day"] = fact_df["hour_of_day"].astype("int64")
        fact_df["day_of_week"] = fact_df["day_of_week"].astype("int64")
        fact_df["is_in_range"] = fact_df["is_in_range"].astype("int64")
        fact_df["reading_timestamp"] = pd.to_datetime(fact_df["reading_timestamp"])

        context.log.info(f"Loaded {len(fact_df)} rows for validation")

    except Exception as exc:
        context.log.error(f"Failed to load data from Trino: {exc}")
        return AssetCheckResult(
            passed=False,
            metadata={
                "reason": "trino_query_failed",
                "error": str(exc),
            },
        )

    if fact_df.empty:
        return AssetCheckResult(
            passed=True,
            metadata={
                "rows_validated": 0,
                "note": "No data available for selected partition",
            },
        )

    # Validate with Pandera schema
    context.log.info("Validating data with Pandera schema...")
    try:
        FactGlucoseReadings.validate(fact_df, lazy=True)
        context.log.info("All validation checks passed!")

        return AssetCheckResult(
            passed=True,
            metadata={
                "rows_validated": len(fact_df),
                "columns_validated": len(fact_df.columns),
            },
        )

    except pandera.errors.SchemaErrors as err:
        failure_cases = err.failure_cases
        context.log.warning(f"Validation failed with {len(failure_cases)} check failures")

        return AssetCheckResult(
            passed=False,
            metadata={
                "rows_evaluated": len(fact_df),
                "failed_checks": len(failure_cases),
                "failures_by_column": failure_cases.groupby("column").size().to_dict(),
                "sample_failures": failure_cases.head(10).to_dict(orient="records"),
            },
        )
```

### Viewing Check Results

In Dagster UI:

```
Asset: fct_glucose_readings
├─ ✓ glucose_range_check (PASSED)
│  └─ valid_count: 4,987 / 5,000
│  └─ percentage_valid: 99.74%
├─ ✓ glucose_freshness_check (PASSED)
│  └─ latest_reading_hours_ago: 0.15
├─ ✗ glucose_statistical_bounds_check (FAILED)
│  └─ outlier_count: 3
│  └─ bounds: [45.2, 215.8]
│  └─ Action: Investigate readings outside [45, 215]
```

## Comparing Both Approaches

Both approaches are used in the actual Phlo implementation and serve different purposes:

### @phlo_quality: Declarative (10 lines)

Best for standard checks - reduces boilerplate by 70-80%:

```python
# File: examples/glucose-platform/workflows/quality/nightscout.py

import phlo
from phlo_quality import NullCheck, RangeCheck, FreshnessCheck

@phlo_quality(
    table="silver.fct_glucose_readings",
    checks=[
        NullCheck(columns=["entry_id", "glucose_mg_dl", "reading_timestamp"]),
        RangeCheck(column="glucose_mg_dl", min_value=20, max_value=600),
        RangeCheck(column="hour_of_day", min_value=0, max_value=23),
        FreshnessCheck(column="reading_timestamp", max_age_hours=24),
    ],
    group="nightscout",
    blocking=True,
)
def glucose_readings_quality():
    """Declarative quality checks for glucose readings."""
    pass
```

### Traditional @asset_check: Custom Logic (80+ lines)

Best for complex validation with Pandera schemas or custom business logic:

```python
# File: examples/glucose-platform/workflows/quality/nightscout.py

@asset_check(
    name="nightscout_glucose_quality",
    asset=AssetKey(["fct_glucose_readings"]),
    blocking=True,
)
def nightscout_glucose_quality_check(context, trino: TrinoResource) -> AssetCheckResult:
    """Full Pandera schema validation with custom error handling."""

    # Query data from Trino
    query = """SELECT entry_id, glucose_mg_dl, ... FROM iceberg_dev.silver.fct_glucose_readings"""
    with trino.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    fact_df = pd.DataFrame(rows, columns=columns)

    # Validate with Pandera schema
    try:
        FactGlucoseReadings.validate(fact_df, lazy=True)
        return AssetCheckResult(passed=True, metadata={...})
    except pandera.errors.SchemaErrors as err:
        return AssetCheckResult(passed=False, metadata={...})
```

**Both approaches are valid** - use `@phlo_quality` for common checks, `@asset_check` for complex logic.

### Available Check Types

| Check Type | Purpose | Parameters |
|------------|---------|------------|
| `NullCheck` | Verify no nulls | `columns`, `tolerance` (% allowed) |
| `RangeCheck` | Verify numeric bounds | `column`, `min_value`, `max_value` |
| `FreshnessCheck` | Verify data recency | `column`, `max_age_hours` |
| `UniqueCheck` | Verify uniqueness | `columns` (can be composite) |
| `CountCheck` | Verify row count | `min_count`, `max_count` |
| `SchemaCheck` | Validate against Pandera | `schema` (DataFrameModel class) |
| `CustomSQLCheck` | Run arbitrary SQL | `sql`, `expected_result` |

### Check Parameters in Detail

**NullCheck with tolerance:**
```python
# Strict: no nulls allowed
NullCheck(columns=["sgv", "timestamp"])

# Lenient: allow up to 1% nulls
NullCheck(columns=["device"], tolerance=0.01)
```

**RangeCheck:**
```python
# Both bounds
RangeCheck(column="sgv", min_value=20, max_value=600)

# Only lower bound
RangeCheck(column="price", min_value=0)

# Only upper bound
RangeCheck(column="percentage", max_value=100)
```

**FreshnessCheck:**
```python
# Data must be less than 2 hours old
FreshnessCheck(column="timestamp", max_age_hours=2)

# Different column name
FreshnessCheck(column="created_at", max_age_hours=24)
```

**UniqueCheck:**
```python
# Single column unique
UniqueCheck(columns=["id"])

# Composite unique (combination must be unique)
UniqueCheck(columns=["user_id", "timestamp"])
```

**CustomSQLCheck for complex rules:**
```python
CustomSQLCheck(
    name="business_hours_only",
    sql="""
        SELECT COUNT(*) as violations
        FROM {table}
        WHERE HOUR(timestamp) < 6 OR HOUR(timestamp) > 22
    """,
    expected_result=0,  # Zero violations expected
)
```

### Decorator Parameters

```python
@phlo_quality(
    table="silver.fct_glucose_readings",  # Fully qualified table name
    checks=[...],                          # List of check instances
    group="glucose",                       # Asset group (optional)
    blocking=True,                         # Fail downstream if check fails
    warn_threshold=0.1,                    # Warn if >10% of checks fail
    backend="trino",                       # Query backend: "trino" or "duckdb"
)
```

**blocking parameter:**
- `blocking=True` (default): Failed checks prevent downstream assets from running
- `blocking=False`: Failed checks log warnings but don't block execution

**warn_threshold:**
- Set to `0.0` for strict mode (any failure = warning)
- Set to `0.1` to allow 10% of checks to fail before warning

### Combining with Pandera Schemas

For complex validation, combine the decorator with Pandera:

```python
from phlo_quality import SchemaCheck
from workflows.schemas.glucose import FactGlucoseReadings

@phlo_quality(
    table="silver.fct_glucose_readings",
    checks=[
        # Use Pandera for full schema validation
        SchemaCheck(schema=FactGlucoseReadings),
        
        # Plus additional runtime checks
        FreshnessCheck(column="timestamp", max_age_hours=2),
    ],
)
def glucose_comprehensive_quality():
    pass
```

### When to Use Each Approach

| Scenario | Recommended Approach | Example |
|----------|---------------------|---------|
| Standard null/range/freshness checks | `@phlo_quality` decorator | `NullCheck`, `RangeCheck`, `FreshnessCheck` |
| Full Pandera schema validation | Traditional `@asset_check` | `FactGlucoseReadings.validate()` |
| Complex business logic | Traditional `@asset_check` | Custom distribution checks |
| Statistical analysis | Traditional `@asset_check` | Outlier detection |
| Multiple simple checks | `@phlo_quality` decorator | Combine `NullCheck` + `RangeCheck` |
| Custom error handling | Traditional `@asset_check` | Detailed failure reporting |

**Real-world usage in examples/glucose-platform**:
- `@phlo_quality`: `glucose_readings_quality()`, `daily_metrics_quality()` - standard checks
- `@asset_check`: `nightscout_glucose_quality_check()` - full Pandera validation with custom error handling

Both approaches are valid and complement each other. The decorator handles common cases efficiently, while traditional checks provide full control for complex scenarios.

## Validation at Each Layer

### Why Three Layers?

```
┌─────────────────────────────────────┐
│ Layer 1: Pandera (Ingestion)        │
│ ✓ Type correctness                  │
│ ✓ Basic constraints (range, enum)   │
│ ✓ Prevent bad data entering system  │
└─────────────────────────────────────┘
          ↓ (only clean data passes)
┌─────────────────────────────────────┐
│ Layer 2: dbt Tests (Transformation) │
│ ✓ Business logic rules              │
│ ✓ Cross-table consistency           │
│ ✓ Catch issues during transform     │
└─────────────────────────────────────┘
          ↓ (only valid transforms apply)
┌─────────────────────────────────────┐
│ Layer 3: Asset Checks (Runtime)     │
│ ✓ Production data quality           │
│ ✓ Anomaly detection                 │
│ ✓ Freshness monitoring              │
└─────────────────────────────────────┘
```

Each layer catches different issues:

- **Pandera**: Bad API responses
- **dbt**: Broken business logic
- **Asset Checks**: Unexpected data patterns

## Practical Example: Catching a Bug

```
Tuesday 3am: Nightscout API starts returning SGV = NULL

[1] Pandera catches it:
    ✗ Column 'sgv' has null values (not nullable)
    → Ingestion stops, alert sent
    → Manual investigation before data corrupts

Without Layer 1:
    [2] dbt Test would catch it:
        ✗ not_null check fails
        → Build fails
        → Data already written to staging
    
    Without Layer 2:
        [3] Asset Check catches it:
            ✗ All values are NULL
            → Dashboard shows "N/A"
            → Users question data validity
```

## Configuring Validation Strictness

```python
# phlo/config.py
from pydantic import BaseSettings

class DataQualityConfig(BaseSettings):
    # Validation behavior
    pandera_strict: bool = True  # Fail on any schema error
    allow_null_in_required: bool = False
    
    # Thresholds for warnings
    max_invalid_percentage: float = 1.0  # Warn if >1% invalid
    freshness_threshold_hours: float = 2.0
    
    # Anomaly detection
    enable_statistical_checks: bool = True
    outlier_std_devs: float = 3.0
    
    class Config:
        env_file = ".env"

config = DataQualityConfig()
```

Use in code:

```python
# Ingestion: strict
if config.pandera_strict:
    validated_df = glucose_entries_schema.validate(data)
else:
    # Lenient: log but continue
    try:
        validated_df = glucose_entries_schema.validate(data)
    except pa.errors.SchemaError as e:
        context.log.warning(f"Schema validation failed: {e}")
        validated_df = data  # Proceed anyway
```

## Monitoring Dashboard

Create a Superset dashboard for data quality:

```sql
-- Query: Validation failures by day
SELECT
  DATE(check_timestamp) as date,
  check_name,
  COUNT(*) as failure_count,
  COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY DATE(check_timestamp)) as pct
FROM data_quality_logs
WHERE status = 'FAILED'
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;

-- Query: Freshness by asset
SELECT
  asset_name,
  MAX(data_date) as latest_data,
  NOW() - MAX(data_date) as hours_stale,
  CASE 
    WHEN NOW() - MAX(data_date) < '2 hours'::interval THEN '✓ Fresh'
    WHEN NOW() - MAX(data_date) < '24 hours'::interval THEN '⚠ Stale'
    ELSE '✗ Very Stale'
  END as freshness_status
FROM asset_metadata
GROUP BY 1
ORDER BY 3 DESC;
```

## Summary

Phlo uses **three-layer validation**:

1. **Pandera** (ingestion): Type and constraint checking
2. **dbt** (transformation): Business logic and consistency
3. **Dagster** (runtime): Production monitoring and anomaly detection

This ensures:
- Bad data never enters the system
- Transforms execute correctly
- Production issues are caught quickly

**Next**: [Part 10: Metadata and Governance with OpenMetadata](10-metadata-governance.md)

See you there!

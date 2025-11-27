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

In Phlo, schemas live in `phlo/schemas/`:

```python
# phlo/schemas/glucose_entries.py
import pandera as pa
from pandera import Column, DataFrameSchema, Check, Index
from typing import Optional


glucose_entries_schema = DataFrameSchema(
    columns={
        # Required fields with type and constraints
        "_id": Column(
            pa.String,
            checks=[
                Check(lambda x: x.str.len() > 0, "ID must not be empty"),
                Check(lambda x: x.is_unique, "ID must be unique"),
            ],
            nullable=False,
        ),
        "sgv": Column(
            pa.Int64,
            checks=[
                Check(lambda x: (x >= 20) & (x <= 600), "Glucose must be 20-600 mg/dL"),
            ],
            nullable=False,
            description="Glucose reading in mg/dL",
        ),
        "timestamp": Column(
            pa.Int64,
            checks=[
                Check(lambda x: x > 0, "Timestamp must be positive"),
            ],
            nullable=False,
            description="Unix milliseconds",
        ),
        "date_string": Column(
            pa.String,
            checks=[
                Check(
                    lambda x: x.str.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"),
                    "Date must be ISO 8601",
                ),
            ],
            nullable=False,
        ),
        "device": Column(
            pa.String,
            checks=[
                Check(
                    lambda x: x.isin([
                        "dexcom", "freestyle", "medtronic", "nightscout"
                    ]),
                    "Device must be known type",
                ),
            ],
            nullable=False,
        ),
        "trend": Column(
            pa.String,
            checks=[
                Check(
                    lambda x: x.isin(["FLAT", "SINGLE UP", "DOUBLE UP", 
                                      "SINGLE DOWN", "DOUBLE DOWN", "NOT COMPUTABLE"]),
                    "Trend must be valid",
                ),
            ],
            nullable=True,  # Some devices don't provide
        ),
    },
    strict=False,  # Allow extra columns (will be dropped)
    coerce=True,  # Try to convert types
)
```

### Using Pandera in DLT

```python
# phlo/defs/ingestion/dlt_assets.py
from phlo.schemas.glucose_entries import glucose_entries_schema
import pandera as pa
import dlt

@asset(
    name="dlt_glucose_entries",
    description="Raw glucose data from Nightscout API",
    group_name="ingestion",
)
def load_glucose_entries(context) -> None:
    """Ingest glucose readings with validation."""
    
    # DLT loads from API
    pipeline = dlt.pipeline(
        pipeline_name="glucose_pipeline",
        destination="s3",
        dataset_name="raw",
    )
    
    # Load data from API
    data = fetch_from_nightscout_api()
    
    # Validate with Pandera BEFORE loading
    try:
        validated_df = glucose_entries_schema.validate(data)
        context.log.info(f"✓ Validation passed: {len(validated_df)} rows")
    except pa.errors.SchemaError as e:
        context.log.error(f"✗ Validation failed:\n{e}")
        # Log problematic rows for investigation
        for idx, error in e.failure_cases.iterrows():
            context.log.warning(f"  Row {idx}: {error}")
        raise
    
    # Only load validated data
    pipeline.run(
        validated_df,
        table_name="glucose_entries",
        write_disposition="append",
    )
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

After orchestration, Dagster asset checks monitor data quality in production.

### Defining Asset Checks

```python
# phlo/defs/quality/glucose_checks.py
from dagster import asset, asset_check, AssetCheckResult, Config
import pandas as pd
from datetime import timedelta


@asset
def fct_glucose_readings():
    """Glucose readings fact table."""
    # ... asset code ...
    pass


@asset_check(asset=fct_glucose_readings)
def glucose_range_check(fct_glucose_readings: pd.DataFrame) -> AssetCheckResult:
    """Ensure glucose readings are in valid range."""
    
    invalid_rows = fct_glucose_readings[
        (fct_glucose_readings['glucose_mg_dl'] < 20) |
        (fct_glucose_readings['glucose_mg_dl'] > 600)
    ]
    
    passed = len(invalid_rows) == 0
    
    return AssetCheckResult(
        passed=passed,
        metadata={
            "invalid_count": len(invalid_rows),
            "valid_count": len(fct_glucose_readings) - len(invalid_rows),
            "percentage_valid": (
                100 * (len(fct_glucose_readings) - len(invalid_rows)) 
                / len(fct_glucose_readings)
            ),
        },
    )


@asset_check(asset=fct_glucose_readings)
def glucose_freshness_check(fct_glucose_readings: pd.DataFrame) -> AssetCheckResult:
    """Ensure recent readings exist."""
    
    latest_reading = fct_glucose_readings['timestamp_iso'].max()
    hours_old = (pd.Timestamp.now(tz='UTC') - latest_reading).total_seconds() / 3600
    
    passed = hours_old < 2  # Alert if no reading in 2 hours
    
    return AssetCheckResult(
        passed=passed,
        metadata={
            "latest_reading_hours_ago": round(hours_old, 2),
            "threshold_hours": 2,
        },
    )


@asset_check(asset=fct_glucose_readings)
def glucose_statistical_bounds_check(
    fct_glucose_readings: pd.DataFrame,
) -> AssetCheckResult:
    """Detect outliers using statistical bounds."""
    
    glucose_values = fct_glucose_readings['glucose_mg_dl']
    mean = glucose_values.mean()
    std = glucose_values.std()
    
    # Flag readings more than 3 std devs from mean
    outliers = glucose_values[
        (glucose_values < mean - 3 * std) |
        (glucose_values > mean + 3 * std)
    ]
    
    passed = len(outliers) < 5  # Allow a few, but flag many
    
    return AssetCheckResult(
        passed=passed,
        metadata={
            "outlier_count": len(outliers),
            "mean": round(mean, 2),
            "std": round(std, 2),
            "bounds": f"[{round(mean - 3*std, 2)}, {round(mean + 3*std, 2)}]",
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

## The @phlo.quality Decorator

The asset checks above work, but they're verbose. Each check requires:
- A function definition
- Boilerplate for querying data
- Manual result construction
- Repetitive metadata handling

For common checks (null, range, freshness), Phlo provides the `@phlo.quality` decorator that reduces boilerplate by 70-80%.

### Before: Traditional Asset Checks (60+ lines)

```python
@asset_check(asset=fct_glucose_readings)
def glucose_null_check(fct_glucose_readings: pd.DataFrame) -> AssetCheckResult:
    null_counts = fct_glucose_readings[['glucose_mg_dl', 'timestamp']].isnull().sum()
    passed = null_counts.sum() == 0
    return AssetCheckResult(passed=passed, metadata={"null_counts": null_counts.to_dict()})

@asset_check(asset=fct_glucose_readings)
def glucose_range_check(fct_glucose_readings: pd.DataFrame) -> AssetCheckResult:
    invalid = fct_glucose_readings[
        (fct_glucose_readings['glucose_mg_dl'] < 20) |
        (fct_glucose_readings['glucose_mg_dl'] > 600)
    ]
    passed = len(invalid) == 0
    return AssetCheckResult(passed=passed, metadata={"invalid_count": len(invalid)})

@asset_check(asset=fct_glucose_readings)
def glucose_freshness_check(fct_glucose_readings: pd.DataFrame) -> AssetCheckResult:
    latest = fct_glucose_readings['timestamp'].max()
    hours_old = (pd.Timestamp.now(tz='UTC') - latest).total_seconds() / 3600
    passed = hours_old < 24
    return AssetCheckResult(passed=passed, metadata={"hours_old": hours_old})
```

### After: @phlo.quality Decorator (10 lines)

```python
import phlo
from phlo.quality import NullCheck, RangeCheck, FreshnessCheck

@phlo.quality(
    table="silver.fct_glucose_readings",
    checks=[
        NullCheck(columns=["glucose_mg_dl", "timestamp"]),
        RangeCheck(column="glucose_mg_dl", min_value=20, max_value=600),
        FreshnessCheck(column="timestamp", max_age_hours=24),
    ],
    group="glucose",
    blocking=True,
)
def glucose_quality():
    """Quality checks for glucose readings."""
    pass
```

Same functionality, fraction of the code.

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
@phlo.quality(
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
from phlo.quality import SchemaCheck
from workflows.schemas.glucose import FactGlucoseReadings

@phlo.quality(
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

| Scenario | Recommended Approach |
|----------|---------------------|
| Standard null/range/freshness checks | `@phlo.quality` decorator |
| Complex business logic | Traditional `@asset_check` |
| Statistical analysis | Traditional `@asset_check` |
| Pandera schema validation | `SchemaCheck` in decorator |
| One-off investigation | Traditional `@asset_check` |

The decorator handles 80% of cases. Use traditional checks when you need custom logic.

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

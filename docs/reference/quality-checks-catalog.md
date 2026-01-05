# Quality Checks Catalog

Comprehensive reference for all quality check types available in the `@phlo_quality` framework.

## Overview

Phlo's declarative quality framework reduces quality check boilerplate by 70-80% through the `@phlo_quality` decorator and reusable check classes. Instead of writing verbose asset checks with custom SQL and validation logic, you define quality checks declaratively using pre-built check types.

**Key Benefits:**

- **Declarative:** Define what to check, not how to check it
- **Reusable:** Pre-built checks for common validation patterns
- **Partition-aware:** Automatic partition scoping for incremental data
- **Rich metadata:** Detailed failure diagnostics with sample rows
- **Multiple backends:** Works with Trino, DuckDB, or custom queries

## Quick Reference

| Check Type | Purpose | Primary Use Case |
|------------|---------|------------------|
| [NullCheck](#nullcheck) | Verify columns have no null values | Data completeness validation |
| [UniqueCheck](#uniquecheck) | Verify uniqueness constraints | Primary key validation |
| [RangeCheck](#rangecheck) | Verify numeric values within bounds | Data quality bounds |
| [FreshnessCheck](#freshnesscheck) | Verify data recency | Stale data detection |
| [CountCheck](#countcheck) | Verify row count expectations | Pipeline completeness |
| [PatternCheck](#patterncheck) | Verify string patterns with regex | Format validation |
| [SchemaCheck](#schemacheck) | Verify Pandera schema compliance | Type-safe validation |
| [CustomSQLCheck](#customsqlcheck) | Execute arbitrary SQL validation | Custom business rules |
| [ReconciliationCheck](#reconciliationcheck) | Compare row counts across tables | Pipeline integrity |
| [AggregateConsistencyCheck](#aggregateconsistencycheck) | Verify aggregates match source | Aggregation accuracy |
| [KeyParityCheck](#keyparitycheck) | Verify matching keys across tables | Missing/extra row detection |
| [MultiAggregateConsistencyCheck](#multiaggregatecheck) | Verify multiple aggregates efficiently | Multi-metric validation |
| [ChecksumReconciliationCheck](#checksumreconciliationcheck) | Row-level hash comparison | Data drift detection |

## Basic Example

```python
from phlo_quality import phlo_quality, NullCheck, RangeCheck, UniqueCheck

@phlo_quality(
    table="silver.fct_glucose_readings",
    checks=[
        NullCheck(columns=["entry_id", "glucose_mg_dl"]),
        UniqueCheck(columns=["entry_id"]),
        RangeCheck(column="glucose_mg_dl", min_value=20, max_value=600),
    ],
    group="nightscout",
    blocking=True,
    partition_column="reading_date",
)
def glucose_readings_quality():
    """Declarative quality checks for glucose readings."""
    pass
```

This 10-line function replaces 30-40 lines of manual asset check code.

---

## Column-Level Checks

### NullCheck

Verifies that specified columns contain no null values.

**Use when:** You need to enforce NOT NULL constraints on critical columns (IDs, timestamps, required fields).

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `columns` | `list[str]` | Required | Columns that must not contain nulls |
| `allow_threshold` | `float` | `0.0` | Maximum fraction of nulls allowed (0.0 = no nulls, 0.05 = 5% nulls) |

**Returns:**

- `passed`: Whether null percentage is within threshold for all columns
- `metric_value`: Dictionary of null counts per column
- `metadata`: Null counts, percentages, and sample rows with nulls

**Example:**

```python
from phlo_quality import NullCheck, phlo_quality

@phlo_quality(
    table="bronze.weather_observations",
    checks=[
        # Strict: no nulls allowed
        NullCheck(columns=["station_id", "observation_time"]),

        # Lenient: allow up to 5% nulls in optional fields
        NullCheck(columns=["wind_speed", "visibility"], allow_threshold=0.05),
    ],
    group="weather",
)
def weather_nulls():
    pass
```

**Failure Example:**

```
Column 'temperature' has 12.5% nulls (threshold: 0.0%)
```

**When to use vs dbt tests:**

- Use `NullCheck` when you want rich Python-based diagnostics with sample rows
- Use dbt's `not_null` test when you only need pass/fail status
- `NullCheck` provides better debugging with threshold support and detailed metadata

---

### UniqueCheck

Verifies that specified columns have unique value combinations (no duplicates).

**Use when:** You need to enforce primary key or composite key uniqueness constraints.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `columns` | `list[str]` | Required | Columns that must have unique combinations |
| `allow_threshold` | `float` | `0.0` | Maximum fraction of duplicates allowed |

**Returns:**

- `passed`: Whether duplicate percentage is within threshold
- `metric_value`: Dictionary with duplicate count
- `metadata`: Duplicate count, percentage, and sample duplicate rows

**Example:**

```python
from phlo_quality import UniqueCheck, phlo_quality

@phlo_quality(
    table="silver.fct_glucose_readings",
    checks=[
        # Single column uniqueness
        UniqueCheck(columns=["entry_id"]),

        # Composite key uniqueness
        UniqueCheck(columns=["station_id", "observation_time"]),

        # Allow small percentage of duplicates (e.g., for append-only tables)
        UniqueCheck(columns=["transaction_id"], allow_threshold=0.01),
    ],
    group="quality",
)
def uniqueness_checks():
    pass
```

**Failure Example:**

```
Found 45 duplicate rows (2.3%) in columns ['entry_id'] (threshold: 0.0%)
```

**When to use vs dbt tests:**

- Use `UniqueCheck` for detailed duplicate row analysis
- Use dbt's `unique` test for simple pass/fail validation
- `UniqueCheck` shows you actual duplicate values, dbt only tells you if any exist

---

### RangeCheck

Verifies that numeric column values fall within a specified range.

**Use when:** You need to validate business logic bounds (e.g., age 0-120, temperature -50 to 60).

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `column` | `str` | Required | Column to check |
| `min_value` | `float \| None` | `None` | Minimum allowed value (inclusive) |
| `max_value` | `float \| None` | `None` | Maximum allowed value (inclusive) |
| `allow_threshold` | `float` | `0.0` | Maximum fraction of out-of-range values allowed |

**Returns:**

- `passed`: Whether violations are within threshold
- `metric_value`: Dictionary with actual min, max, and out-of-range count
- `metadata`: Expected vs actual ranges, violation details, sample violating rows

**Example:**

```python
from phlo_quality import RangeCheck, phlo_quality

@phlo_quality(
    table="silver.fct_glucose_readings",
    checks=[
        # Both bounds
        RangeCheck(column="glucose_mg_dl", min_value=20, max_value=600),
        RangeCheck(column="hour_of_day", min_value=0, max_value=23),

        # Only minimum bound
        RangeCheck(column="stargazers_count", min_value=0),

        # Only maximum bound
        RangeCheck(column="temperature_celsius", max_value=60),

        # Allow some outliers
        RangeCheck(column="response_time_ms", min_value=0, max_value=5000, allow_threshold=0.01),
    ],
    group="ranges",
)
def range_validations():
    pass
```

**Failure Example:**

```
Column 'glucose_mg_dl' has 0.8% out-of-range values (threshold: 0.0%).
Expected range: [20, 600], Actual range: [15, 650]
```

**When to use vs dbt tests:**

- Use `RangeCheck` when you need to see actual min/max values and outliers
- Use dbt's generic tests for simple threshold checks
- `RangeCheck` provides richer diagnostics for data quality investigations

---

### PatternCheck

Verifies that string column values match a regular expression pattern.

**Use when:** You need to validate formats (emails, phone numbers, IDs, postal codes).

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `column` | `str` | Required | Column to check |
| `pattern` | `str` | Required | Regex pattern that values must match |
| `allow_threshold` | `float` | `0.0` | Maximum fraction of non-matching values allowed |
| `case_sensitive` | `bool` | `True` | Whether pattern matching is case sensitive |

**Returns:**

- `passed`: Whether non-matches are within threshold
- `metric_value`: Dictionary with match and non-match counts
- `metadata`: Pattern, match counts, sample non-matching values

**Example:**

```python
from phlo_quality import PatternCheck, phlo_quality

@phlo_quality(
    table="raw.user_profile",
    checks=[
        # GitHub username pattern
        PatternCheck(
            column="login",
            pattern=r"^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$"
        ),

        # Email validation
        PatternCheck(
            column="email",
            pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        ),

        # US postal code (allow 5% invalid for international users)
        PatternCheck(
            column="postal_code",
            pattern=r"^\d{5}(-\d{4})?$",
            allow_threshold=0.05
        ),

        # Case-insensitive match
        PatternCheck(
            column="country_code",
            pattern=r"^[A-Z]{2}$",
            case_sensitive=False
        ),
    ],
    group="format_validation",
)
def pattern_checks():
    pass
```

**Failure Example:**

```
Column 'email' has 3.2% values not matching pattern (threshold: 0.0%).
Sample non-matches: ['user@', 'invalid.email', 'test@.com', '@example.com', 'user name@test.com']
```

**When to use vs dbt tests:**

- Use `PatternCheck` when you need to see which values are invalid
- dbt tests don't have built-in regex support without custom macros
- `PatternCheck` is easier for complex format validation

---

## Table-Level Checks

### CountCheck

Verifies that the table row count meets expectations.

**Use when:** You need to ensure pipelines produce expected data volumes (detect empty tables, missing partitions, or runaway queries).

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_rows` | `int \| None` | `None` | Minimum expected row count |
| `max_rows` | `int \| None` | `None` | Maximum expected row count |

**Returns:**

- `passed`: Whether row count is within bounds
- `metric_value`: Dictionary with actual row count
- `metadata`: Row count and configured bounds

**Example:**

```python
from phlo_quality import CountCheck, phlo_quality

@phlo_quality(
    table="silver.fct_glucose_readings",
    checks=[
        # At least 1 row (ensure partition not empty)
        CountCheck(min_rows=1),

        # Both bounds (expect daily data volume)
        CountCheck(min_rows=100, max_rows=10000),

        # Only maximum (prevent runaway queries)
        CountCheck(max_rows=1000000),
    ],
    group="volume",
    partition_column="reading_date",
)
def volume_checks():
    pass
```

**Failure Example:**

```
Row count 0 is below minimum 1
Row count 15000 is above maximum 10000
```

**When to use vs dbt tests:**

- Use `CountCheck` for partition-aware volume validation
- dbt's `dbt_expectations.expect_table_row_count_to_be_between` is similar but less integrated
- `CountCheck` works seamlessly with phlo's partition scoping

---

### FreshnessCheck

Verifies that data is fresh (not stale) by checking the maximum timestamp.

**Use when:** You need to detect stale data, delayed pipelines, or missing recent data.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timestamp_column` | `str` | Required | Column containing timestamps to check |
| `max_age_hours` | `float` | Required | Maximum age in hours for data to be considered fresh |
| `reference_time` | `datetime \| None` | `None` | Reference time to compare against (defaults to now) |

**Returns:**

- `passed`: Whether data is fresh enough
- `metric_value`: Dictionary with max age in hours
- `metadata`: Max timestamp, reference time, age calculation

**Example:**

```python
from phlo_quality import FreshnessCheck, phlo_quality

@phlo_quality(
    table="silver.fct_glucose_readings",
    checks=[
        # Data should be less than 24 hours old
        FreshnessCheck(timestamp_column="reading_timestamp", max_age_hours=24),

        # Real-time data (less than 2 hours old)
        FreshnessCheck(timestamp_column="ingestion_time", max_age_hours=2),

        # Daily batch (less than 36 hours to allow weekend delays)
        FreshnessCheck(timestamp_column="batch_date", max_age_hours=36),
    ],
    group="freshness",
)
def freshness_checks():
    pass
```

**Failure Example:**

```
Data is stale. Most recent timestamp is 48.5 hours old (threshold: 24.0 hours)
```

**When to use vs dbt tests:**

- Use `FreshnessCheck` for programmatic freshness validation in Python
- Use dbt's freshness checks in `sources.yml` for dbt-managed sources
- `FreshnessCheck` is better for complex freshness logic (e.g., different thresholds per partition)

---

### SchemaCheck

Verifies that a DataFrame matches a Pandera schema with type-safe validation.

**Use when:** You need comprehensive schema validation including types, constraints, and custom checks.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `schema` | `Any` | Required | Pandera DataFrameModel or schema to validate against |
| `lazy` | `bool` | `True` | Use lazy validation to collect all errors (vs fail-fast) |

**Returns:**

- `passed`: Whether all schema validations pass
- `metric_value`: Dictionary with schema validity status
- `metadata`: Schema name, validation counts, failures by column/check, sample failures

**Example:**

```python
import pandera as pa
from pandera.typing import Series
from phlo_quality import SchemaCheck, phlo_quality

# Define Pandera schema
class WeatherObservations(pa.DataFrameModel):
    station_id: Series[str] = pa.Field(nullable=False)
    temperature: Series[float] = pa.Field(ge=-50, le=60)
    humidity: Series[float] = pa.Field(ge=0, le=100)
    observation_time: Series[pa.DateTime] = pa.Field(nullable=False)

    class Config:
        strict = True
        coerce = True

@phlo_quality(
    table="bronze.weather_observations",
    checks=[
        SchemaCheck(schema=WeatherObservations),
    ],
    group="schema",
)
def weather_schema_check():
    pass
```

**Failure Example:**

```
Schema validation failed with 15 errors
Failures by column: {'temperature': 8, 'humidity': 7}
Failures by check: {'greater_than_or_equal_to': 10, 'less_than_or_equal_to': 5}
```

**When to use vs dbt tests:**

- Use `SchemaCheck` when you need Python-based type validation with Pandera
- Use dbt schema tests for SQL-based validation
- `SchemaCheck` is better for complex Python transformations and data science workflows
- dbt is better for SQL-centric transformations

---

## Advanced SQL Checks

### CustomSQLCheck

Executes arbitrary SQL to validate data using custom business logic.

**Use when:** You need custom validation logic that doesn't fit pre-built checks (e.g., cross-column validation, complex business rules).

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name_` | `str` | Required | Name of this check |
| `sql` | `str` | Required | SQL query that returns TRUE for valid rows, FALSE for invalid |
| `expected` | `bool` | `True` | Expected result (default: TRUE for all rows valid) |
| `allow_threshold` | `float` | `0.0` | Maximum fraction of failures allowed |

**Returns:**

- `passed`: Whether failures are within threshold
- `metric_value`: Dictionary with failure and total counts
- `metadata`: Failure details and percentages

**Example:**

```python
from phlo_quality import CustomSQLCheck, phlo_quality

@phlo_quality(
    table="silver.fct_weather_observations",
    checks=[
        # Cross-column validation
        CustomSQLCheck(
            name_="temperature_consistency",
            sql="SELECT (max_temp >= min_temp) FROM data"
        ),

        # Business rule validation
        CustomSQLCheck(
            name_="valid_measurements",
            sql="""
                SELECT (temperature IS NOT NULL AND humidity IS NOT NULL)
                OR measurement_type = 'INCOMPLETE'
                FROM data
            """
        ),

        # Complex calculation
        CustomSQLCheck(
            name_="revenue_consistency",
            sql="""
                SELECT ABS(revenue - (quantity * unit_price)) < 0.01
                FROM data
            """
        ),
    ],
    group="custom",
)
def custom_validations():
    pass
```

**Note:** Requires DuckDB to be available for SQL execution.

**When to use vs dbt tests:**

- Use `CustomSQLCheck` for Python workflow custom logic
- Use dbt singular tests for SQL workflow custom logic
- Both are equally powerful; choice depends on your workflow language preference

---

## Reconciliation Checks

Reconciliation checks compare data **across tables** to ensure pipeline integrity and consistency.

### ReconciliationCheck

Compares row counts between source and target tables to detect data loss or duplication.

**Use when:** You need to verify that transformations preserve row counts (1:1 transforms, unions, filters).

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_table` | `str` | Required | Fully qualified source table name |
| `partition_column` | `str` | `"_phlo_partition_date"` | Column used for partition filtering |
| `check_type` | `str` | `"rowcount_parity"` | Type: 'rowcount_parity' (exact match) or 'rowcount_gte' (target >= source) |
| `tolerance` | `float` | `0.0` | Allowed percentage difference (0.0 = exact, 0.05 = 5% tolerance) |
| `absolute_tolerance` | `int \| None` | `None` | Allowed absolute difference in row counts |
| `where_clause` | `str \| None` | `None` | Optional WHERE clause to filter source data |

**Returns:**

- `passed`: Whether row counts match within tolerance
- `metric_value`: Source count, target count, difference
- `metadata`: Tables, partition, tolerance, generated SQL query

**Example:**

```python
from phlo_quality import ReconciliationCheck, phlo_quality

@phlo_quality(
    table="gold.fct_github_events",
    checks=[
        # Exact row count match (1:1 transformation)
        ReconciliationCheck(
            source_table="silver.stg_github_events",
            partition_column="_phlo_partition_date",
            check_type="rowcount_parity",
            tolerance=0.0,
        ),

        # Allow 5% difference (for approximate joins)
        ReconciliationCheck(
            source_table="bronze.raw_events",
            tolerance=0.05,
        ),

        # Target should have at least as many rows as source
        ReconciliationCheck(
            source_table="staging.events",
            check_type="rowcount_gte",
        ),

        # With filter on source
        ReconciliationCheck(
            source_table="bronze.all_events",
            where_clause="event_type = 'push'",
        ),
    ],
    group="reconciliation",
    partition_aware=True,
)
def events_reconciliation():
    """Ensure no rows lost in transformation."""
    pass
```

**Failure Example:**

```
Row count reconciliation failed: target has 1,250 rows, source has 1,300 rows
(diff: 3.85%, tolerance: 0.0%)
```

**Debugging tip:** Check the `query` field in metadata to see the exact SQL used to count source rows.

**When to use vs dbt tests:**

- Use `ReconciliationCheck` for Python-managed pipelines
- Use dbt's `dbt_utils.relationships` or custom reconciliation tests for dbt pipelines
- `ReconciliationCheck` is better for cross-layer validation outside dbt

---

### AggregateConsistencyCheck

Verifies that computed aggregates in a target table match the expected computation from source data.

**Use when:** You need to validate aggregation accuracy (e.g., daily totals, rollup tables).

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_table` | `str` | Required | Fully qualified source table name |
| `aggregate_column` | `str` | Required | Column in target containing aggregate value |
| `source_expression` | `str` | Required | SQL expression to compute from source (e.g., 'COUNT(*)', 'SUM(amount)') |
| `partition_column` | `str` | `"_phlo_partition_date"` | Column for partition filtering |
| `group_by` | `list[str]` | `[]` | Columns to group by when comparing aggregates |
| `tolerance` | `float` | `0.0` | Allowed percentage difference |
| `absolute_tolerance` | `int \| None` | `None` | Allowed absolute difference |
| `where_clause` | `str \| None` | `None` | Optional WHERE clause for source |

**Returns:**

- `passed`: Whether aggregates match within tolerance
- `metric_value`: Mismatch count and total checked
- `metadata`: Source table, expression, sample mismatches, generated SQL

**Example:**

```python
from phlo_quality import AggregateConsistencyCheck, phlo_quality

@phlo_quality(
    table="gold.fct_daily_github_metrics",
    checks=[
        # Verify total_events matches source count
        AggregateConsistencyCheck(
            source_table="gold.fct_github_events",
            aggregate_column="total_events",
            source_expression="COUNT(*)",
            partition_column="_phlo_partition_date",
            group_by=["activity_date"],
            tolerance=0.0,
        ),

        # Verify sum of amounts
        AggregateConsistencyCheck(
            source_table="silver.transactions",
            aggregate_column="total_revenue",
            source_expression="SUM(amount)",
            group_by=["date", "category"],
        ),

        # Allow small floating point differences
        AggregateConsistencyCheck(
            source_table="raw.measurements",
            aggregate_column="avg_temperature",
            source_expression="AVG(temp_celsius)",
            group_by=["station_id", "date"],
            absolute_tolerance=0.01,
        ),
    ],
    group="reconciliation",
)
def aggregate_consistency():
    """Verify aggregated metrics match source."""
    pass
```

**Failure Example:**

```
Aggregate consistency check failed: 3 mismatches out of 30 checked (tolerance: 0.0%)
Sample mismatches: [
  {group_key: '2024-01-15', target: 1250, source: 1300},
  {group_key: '2024-01-16', target: 980, source: 995},
  ...
]
```

**When to use vs dbt tests:**

- Use `AggregateConsistencyCheck` for validating Python-computed aggregates
- Use dbt tests for validating dbt-computed aggregates
- This check is especially valuable for incremental aggregation validation

---

### KeyParityCheck

Verifies that source and target tables have matching keys to catch missing or extra rows.

**Use when:** Row counts match but you suspect missing/extra rows (e.g., row deleted from source, row added incorrectly to target).

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_table` | `str` | Required | Fully qualified source table name |
| `key_columns` | `list[str]` | Required | Primary key or composite key columns |
| `partition_column` | `str` | `"_phlo_partition_date"` | Column for partition filtering |
| `tolerance` | `float` | `0.0` | Allowed fraction of missing keys |
| `where_clause` | `str \| None` | `None` | Optional WHERE clause for source |

**Returns:**

- `passed`: Whether key mismatch is within tolerance
- `metric_value`: Missing in target, missing in source, total keys
- `metadata`: Sample missing keys from both sides

**Example:**

```python
from phlo_quality import KeyParityCheck, phlo_quality

@phlo_quality(
    table="gold.dim_customers",
    checks=[
        # Verify all customer IDs present
        KeyParityCheck(
            source_table="silver.stg_customers",
            key_columns=["customer_id"],
        ),

        # Composite key parity
        KeyParityCheck(
            source_table="bronze.order_items",
            key_columns=["order_id", "item_id"],
        ),

        # Allow small discrepancy
        KeyParityCheck(
            source_table="staging.users",
            key_columns=["user_id"],
            tolerance=0.01,  # 1% missing keys allowed
        ),
    ],
    group="reconciliation",
)
def key_parity():
    """Verify no missing or extra keys."""
    pass
```

**Failure Example:**

```
Key parity check failed: 15 missing in target, 3 missing in source
(mismatch: 1.8%, tolerance: 0.0%)
Sample missing in target: ['user-123', 'user-456', ...]
Sample missing in source: ['user-999']
```

**When to use vs ReconciliationCheck:**

- Use `KeyParityCheck` when row counts match but you suspect key mismatches
- Use `ReconciliationCheck` for simple row count validation
- `KeyParityCheck` is more expensive (loads all keys) but catches subtle issues

---

### MultiAggregateConsistencyCheck

Efficiently validates multiple aggregates in a single query to reduce source table scans.

**Use when:** You need to validate many aggregates and want to optimize performance.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_table` | `str` | Required | Fully qualified source table name |
| `aggregates` | `list[AggregateSpec]` | Required | List of aggregate specifications |
| `partition_column` | `str` | `"_phlo_partition_date"` | Column for partition filtering |
| `group_by` | `list[str]` | `[]` | Columns to group by |
| `tolerance` | `float` | `0.0` | Allowed percentage difference |
| `absolute_tolerance` | `int \| None` | `None` | Allowed absolute difference |
| `where_clause` | `str \| None` | `None` | Optional WHERE clause |

**AggregateSpec Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Alias for the source aggregate expression |
| `expression` | `str` | SQL expression (e.g., 'COUNT(*)', 'SUM(amount)') |
| `target_column` | `str` | Target table column containing aggregate |

**Example:**

```python
from phlo_quality import AggregateSpec, MultiAggregateConsistencyCheck, phlo_quality

@phlo_quality(
    table="gold.fct_daily_metrics",
    checks=[
        MultiAggregateConsistencyCheck(
            source_table="silver.fct_events",
            aggregates=[
                AggregateSpec(
                    name="total_events",
                    expression="COUNT(*)",
                    target_column="event_count"
                ),
                AggregateSpec(
                    name="total_revenue",
                    expression="SUM(revenue)",
                    target_column="daily_revenue"
                ),
                AggregateSpec(
                    name="avg_duration",
                    expression="AVG(duration_seconds)",
                    target_column="avg_duration_seconds"
                ),
            ],
            group_by=["date", "category"],
            partition_column="_phlo_partition_date",
        ),
    ],
    group="reconciliation",
)
def multi_aggregate_check():
    """Efficiently validate multiple aggregates."""
    pass
```

**Benefits over separate AggregateConsistencyChecks:**

- Single query scans source table once (vs once per aggregate)
- Faster for tables with many aggregates
- Atomic validation (all aggregates checked together)

---

### ChecksumReconciliationCheck

Performs row-level hash comparison between source and target tables to detect data drift.

**Use when:** You need to verify that not just row counts match, but actual **data values** match (detect silent data corruption, transformation bugs).

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_table` | `str` | Required | Fully qualified source table name |
| `target_table` | `str` | Required | Fully qualified target table name (usually same as @phlo_quality table) |
| `key_columns` | `list[str]` | Required | Primary key columns for alignment |
| `columns` | `list[str] \| None` | `None` | Columns to hash (None = all non-key columns) |
| `partition_column` | `str` | `"_phlo_partition_date"` | Partition filtering column |
| `tolerance` | `float` | `0.0` | Allowed fraction of mismatches |
| `absolute_tolerance` | `int \| None` | `None` | Allowed absolute count of mismatches |
| `hash_algorithm` | `str` | `"xxhash64"` | Hash algorithm ('xxhash64' or 'md5') |
| `float_precision` | `int` | `6` | Precision for float normalization |
| `sample` | `float \| None` | `None` | Deterministic sampling fraction (0 < sample <= 1) |
| `limit` | `int \| None` | `None` | Limit number of keys compared (for large tables) |

**Returns:**

- `passed`: Whether mismatches are within tolerance
- `metric_value`: Missing in target, missing in source, hash mismatches, total keys
- `metadata`: Detailed mismatch analysis, sample mismatched keys

**Example:**

```python
from phlo_quality import ChecksumReconciliationCheck, phlo_quality

@phlo_quality(
    table="gold.dim_products",
    checks=[
        # Full row-level comparison
        ChecksumReconciliationCheck(
            source_table="silver.stg_products",
            target_table="gold.dim_products",
            key_columns=["product_id"],
        ),

        # Hash specific columns only
        ChecksumReconciliationCheck(
            source_table="bronze.raw_users",
            target_table="silver.users",
            key_columns=["user_id"],
            columns=["name", "email", "status"],  # Exclude audit columns
        ),

        # Sample 10% of rows for performance
        ChecksumReconciliationCheck(
            source_table="huge_table.source",
            target_table="huge_table.target",
            key_columns=["id"],
            sample=0.10,
        ),

        # Limit to 100k rows for performance
        ChecksumReconciliationCheck(
            source_table="large_table.source",
            target_table="large_table.target",
            key_columns=["id"],
            limit=100000,
        ),
    ],
    group="reconciliation",
)
def checksum_reconciliation():
    """Verify row-level data matches."""
    pass
```

**Failure Example:**

```
Checksum reconciliation failed: 50 hash mismatches, 5 missing in target, 2 missing in source
(mismatch: 0.57%, tolerance: 0.0%)
Sample hash mismatches: ['product-123', 'product-456', ...]
```

**Performance Considerations:**

- Most expensive reconciliation check (loads all keys + computes hashes)
- Use `sample` or `limit` for large tables
- Use on critical tables where data integrity is paramount
- Consider running in a separate, less frequent schedule

**When to use:**

- Use for critical dimension tables (e.g., customers, products)
- Use when you've had data corruption issues in the past
- Use for compliance/audit requirements
- Don't use on massive fact tables without sampling

---

## Decision Guide: @phlo_quality vs dbt tests vs pytest

### Use @phlo_quality when:

- You're working in Python workflows (Dagster, Airflow, Prefect)
- You need rich metadata and diagnostics (sample rows, detailed failures)
- You want partition-aware validation with automatic scoping
- You're validating data in Iceberg/Trino/DuckDB tables
- You need reconciliation checks across tables
- You want 70% less boilerplate than manual asset checks

### Use dbt tests when:

- You're working in SQL-centric dbt workflows
- You need simple pass/fail validation
- You want to leverage dbt's incremental model testing
- You're testing dbt models, not external tables
- You prefer YAML configuration over Python code

### Use pytest when:

- You're testing Python transformation logic (not data)
- You need unit tests for functions
- You're testing edge cases in code, not data quality
- You need mocking and test fixtures

### Hybrid Approach (Recommended):

```python
# Use dbt tests for dbt models
# models/schema.yml
models:
  - name: fct_orders
    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - order_id
            - item_id

# Use @phlo_quality for external tables and cross-layer validation
@phlo_quality(
    table="iceberg.gold.fct_orders",
    checks=[
        ReconciliationCheck(
            source_table="postgres.marts.mrt_orders",
        ),
        CountCheck(min_rows=1000),
    ],
)
def orders_quality():
    pass

# Use pytest for transformation logic
def test_calculate_order_total():
    assert calculate_order_total([10, 20, 30]) == 60
```

---

## Best Practices

### 1. Start Simple, Add Gradually

Begin with basic checks and add more as you discover issues:

```python
# Week 1: Basic checks
@phlo_quality(
    table="silver.fct_events",
    checks=[
        NullCheck(columns=["event_id"]),
        CountCheck(min_rows=1),
    ],
)

# Week 2: Add range validation after investigating failures
@phlo_quality(
    table="silver.fct_events",
    checks=[
        NullCheck(columns=["event_id", "timestamp"]),
        UniqueCheck(columns=["event_id"]),
        CountCheck(min_rows=1),
        RangeCheck(column="user_age", min_value=0, max_value=120),
    ],
)
```

### 2. Use Thresholds Wisely

Don't aim for perfection immediately. Allow small thresholds and tighten over time:

```python
# Phase 1: Allow 5% nulls while cleaning data
NullCheck(columns=["optional_field"], allow_threshold=0.05)

# Phase 2: Reduce to 1%
NullCheck(columns=["optional_field"], allow_threshold=0.01)

# Phase 3: Enforce strict
NullCheck(columns=["optional_field"], allow_threshold=0.0)
```

### 3. Organize Checks by Layer

Group related checks together:

```python
# Bronze layer: Basic structure
@phlo_quality(
    table="bronze.raw_events",
    checks=[
        CountCheck(min_rows=1),
        NullCheck(columns=["id", "timestamp"]),
    ],
    group="bronze",
)

# Silver layer: Business logic
@phlo_quality(
    table="silver.fct_events",
    checks=[
        UniqueCheck(columns=["event_id"]),
        RangeCheck(column="amount", min_value=0),
        PatternCheck(column="email", pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$"),
    ],
    group="silver",
)

# Gold layer: Reconciliation
@phlo_quality(
    table="gold.fct_daily_metrics",
    checks=[
        ReconciliationCheck(source_table="silver.fct_events"),
        AggregateConsistencyCheck(
            source_table="silver.fct_events",
            aggregate_column="total_events",
            source_expression="COUNT(*)",
            group_by=["date"],
        ),
    ],
    group="gold",
)
```

### 4. Use blocking Strategically

Not all checks should block downstream assets:

```python
# Critical: Block downstream if failed
@phlo_quality(
    table="silver.dim_customers",
    checks=[UniqueCheck(columns=["customer_id"])],
    blocking=True,  # Block downstream
)

# Non-critical: Warn but don't block
@phlo_quality(
    table="silver.fct_events",
    checks=[FreshnessCheck(timestamp_column="created_at", max_age_hours=48)],
    blocking=False,  # Warn only
)
```

### 5. Leverage Partition Awareness

Let phlo automatically scope checks to partitions:

```python
# Partition-aware (recommended for incremental tables)
@phlo_quality(
    table="silver.fct_events",
    checks=[...],
    partition_aware=True,  # Default
    partition_column="event_date",
)

# Full table scan (use sparingly)
@phlo_quality(
    table="gold.dim_products",  # Slowly changing dimension
    checks=[...],
    full_table=True,  # Check entire table
)
```

### 6. Use Reconciliation Checks in Gold Layer

Add reconciliation checks at aggregation boundaries:

```python
# Ensure gold layer matches silver layer
@phlo_quality(
    table="gold.fct_daily_metrics",
    checks=[
        ReconciliationCheck(source_table="silver.fct_events"),
        AggregateConsistencyCheck(
            source_table="silver.fct_events",
            aggregate_column="event_count",
            source_expression="COUNT(*)",
            group_by=["date"],
        ),
    ],
    group="reconciliation",
)
```

### 7. Document Check Purpose

Use docstrings to explain why checks exist:

```python
@phlo_quality(
    table="silver.fct_glucose_readings",
    checks=[
        RangeCheck(column="glucose_mg_dl", min_value=20, max_value=600),
    ],
)
def glucose_quality():
    """
    Validate glucose readings are within medically valid ranges.

    Range 20-600 mg/dL covers hypoglycemia to severe hyperglycemia.
    Values outside this range indicate sensor errors.

    See: https://diabetes.org/glucose-ranges
    """
    pass
```

### 8. Monitor Check Performance

Use metadata to track validation performance:

```python
# Check execution logs show:
# - rows_validated: 15,432
# - checks_executed: 5
# - checks_failed: 1
# - execution_time: 1.2s
```

### 9. Sample Failures for Large Tables

Use `limit` or `sample` for expensive checks:

```python
# For 100M+ row tables
ChecksumReconciliationCheck(
    source_table="huge.source",
    target_table="huge.target",
    key_columns=["id"],
    sample=0.01,  # Check 1% of rows
)
```

### 10. Combine with Pandera Schemas

Use `SchemaCheck` with other checks for comprehensive validation:

```python
from workflows.schemas.events import EventsSchema

@phlo_quality(
    table="silver.fct_events",
    checks=[
        SchemaCheck(schema=EventsSchema),  # Type validation
        UniqueCheck(columns=["event_id"]),  # Business logic
        CountCheck(min_rows=1),  # Volume check
    ],
)
def events_quality():
    pass
```

---

## Additional Resources

- [phlo-quality Package Source](https://github.com/your-org/phlo/tree/main/packages/phlo-quality)
- [Nightscout Example](https://github.com/your-org/phlo-examples/tree/main/nightscout/workflows/quality)
- [GitHub Example](https://github.com/your-org/phlo-examples/tree/main/github/workflows/quality)
- [Pandera Documentation](https://pandera.readthedocs.io/)

---

## Contributing

Found a bug or want to add a new check type? See [CONTRIBUTING.md](../CONTRIBUTING.md).

## Questions?

- Slack: #phlo-quality
- GitHub Issues: [phlo/issues](https://github.com/your-org/phlo/issues)

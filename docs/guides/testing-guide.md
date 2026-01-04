# Comprehensive Testing Strategy Guide

A practical guide to testing in phlo: when to use `@phlo_quality`, dbt tests, or pytest.

## Overview: Three Testing Layers

Phlo provides three complementary testing approaches, each serving a different purpose:

1. **`@phlo_quality` Checks** - Declarative data quality assertions for production pipelines
2. **dbt Tests** - SQL-based validation for dbt models and transformations
3. **pytest Tests** - Unit and integration tests for custom Python logic

All three approaches work together to provide comprehensive test coverage across your data pipeline.

## Decision Matrix: When to Use Each Approach

### Use `@phlo_quality` when:
**Declarative quality checks for production data assets.** Use this for runtime validation of data quality in your production pipelines. Ideal for partition-aware checks, data freshness validation, and automated quality monitoring that integrates with alerting and observability.

**Examples:**
- Validating row counts, null checks, uniqueness constraints
- Checking data freshness (e.g., last partition is within 24 hours)
- Range validation (e.g., glucose readings between 20-600 mg/dL)
- Cross-table reconciliation checks

### Use dbt tests when:
**SQL validation for dbt models and analytical transformations.** Use this when testing dbt-specific logic, relationships between models, and business rules expressed in SQL. These tests run during `dbt build` and provide immediate feedback during development.

**Examples:**
- Column-level constraints (not_null, unique, accepted_values)
- Relationships between tables (foreign key validation)
- Custom SQL business logic tests
- Testing dbt-specific features (incremental models, snapshots)

### Use pytest when:
**Unit and integration tests for custom Python code.** Use this for testing Python functions, Pandera schema validation, merge strategies, custom business logic, and integration tests that require complex setup or mocking.

**Examples:**
- Testing schema validation logic (Pandera schemas)
- Testing merge strategy behavior (append vs merge, deduplication)
- Testing custom Python transformations
- Integration tests with mocked resources (Iceberg, Trino)
- Testing API endpoints, plugins, or custom utilities

## `@phlo_quality` Guide

The `@phlo_quality` decorator provides a declarative way to define data quality checks that run as part of your Dagster pipeline.

### Available Checks

See the [phlo-quality package documentation](/packages/phlo-quality) for the complete catalog.

**Built-in checks:**
- `NullCheck` - Validates columns have no NULL values
- `UniqueCheck` - Validates column values are unique
- `RangeCheck` - Validates values are within min/max bounds
- `FreshnessCheck` - Validates data is recent based on timestamp column
- `CountCheck` - Validates minimum/maximum row counts

### Declarative Pattern (Recommended)

The declarative pattern reduces boilerplate by 70-80% compared to traditional `@asset_check` functions:

```python
from phlo_quality import (
    phlo_quality,
    NullCheck,
    UniqueCheck,
    RangeCheck,
    FreshnessCheck,
    CountCheck,
)

@phlo_quality(
    table="silver.fct_glucose_readings",
    checks=[
        NullCheck(columns=["entry_id", "glucose_mg_dl", "reading_timestamp"]),
        UniqueCheck(columns=["entry_id"]),
        RangeCheck(column="glucose_mg_dl", min_value=20, max_value=600),
        RangeCheck(column="hour_of_day", min_value=0, max_value=23),
        FreshnessCheck(timestamp_column="reading_timestamp", max_age_hours=24),
        CountCheck(min_rows=1),
    ],
    group="nightscout",
    blocking=True,
    partition_column="reading_date",
)
def glucose_readings_quality():
    """Declarative quality checks for glucose readings using @phlo_quality."""
    pass
```

**Key features:**
- `table`: The fully qualified table name (schema.table)
- `checks`: List of check instances to run
- `group`: Logical grouping for organization in Dagster UI
- `blocking`: Whether failed checks should block downstream assets
- `partition_column`: Column used for partition-aware checking

### Custom `@asset_check` Pattern

For custom logic or complex validation that doesn't fit declarative checks:

```python
import pandas as pd
import pandera.errors
from dagster import AssetCheckResult, AssetKey, MetadataValue, asset_check
from phlo_trino.resource import TrinoResource
from workflows.schemas.nightscout import FactGlucoseReadings

@asset_check(
    name="nightscout_glucose_quality",
    asset=AssetKey(["fct_glucose_readings"]),
    blocking=True,
    description="Validate processed Nightscout glucose data using Pandera schema validation.",
)
def nightscout_glucose_quality_check(context) -> AssetCheckResult:
    """
    Custom quality check using Pandera for type-safe schema validation.

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
    FROM iceberg.silver.fct_glucose_readings
    """

    # Handle partitions
    partition_key = getattr(context, "partition_key", None)
    if partition_key is None:
        partition_key = getattr(context, "asset_partition_key", None)

    if partition_key:
        partition_date = partition_key
        query = f"{query}\nWHERE DATE(reading_timestamp) = DATE '{partition_date}'"
        context.log.info(f"Validating partition: {partition_date}")

    try:
        trino = _resolve_trino_resource(context)
        with trino.cursor(schema="silver") as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

            if not cursor.description:
                context.log.warning("Trino did not return column metadata")
                return AssetCheckResult(
                    passed=False,
                    metadata={"reason": MetadataValue.text("missing_column_metadata")},
                )

            columns = [desc[0] for desc in cursor.description]

        fact_df = pd.DataFrame(rows, columns=columns)

        # Type conversions for validation
        type_conversions = {
            "glucose_mg_dl": "int64",
            "hour_of_day": "int64",
            "day_of_week": "int64",
            "is_in_range": "int64",
        }
        for col, dtype in type_conversions.items():
            if col in fact_df.columns:
                fact_df[col] = fact_df[col].astype(dtype)

        if "reading_timestamp" in fact_df.columns:
            fact_df["reading_timestamp"] = pd.to_datetime(fact_df["reading_timestamp"])

        context.log.info(f"Loaded {len(fact_df)} rows for validation")

    except Exception as exc:
        context.log.error(f"Failed to load data from Trino: {exc}")
        return AssetCheckResult(
            passed=False,
            metadata={
                "reason": MetadataValue.text("trino_query_failed"),
                "error": MetadataValue.text(str(exc)),
            },
        )

    if fact_df.empty:
        context.log.warning("No rows returned for validation")
        return AssetCheckResult(
            passed=True,
            metadata={
                "rows_validated": MetadataValue.int(0),
                "note": MetadataValue.text("No data available for selected partition"),
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
                "rows_validated": MetadataValue.int(len(fact_df)),
                "columns_validated": MetadataValue.int(len(fact_df.columns)),
            },
        )

    except pandera.errors.SchemaErrors as err:
        failure_cases = err.failure_cases
        context.log.warning(f"Validation failed with {len(failure_cases)} check failures")

        return AssetCheckResult(
            passed=False,
            metadata={
                "rows_evaluated": MetadataValue.int(len(fact_df)),
                "failed_checks": MetadataValue.int(len(failure_cases)),
                "failures_by_column": MetadataValue.json(
                    failure_cases.groupby("column").size().to_dict()
                ),
                "sample_failures": MetadataValue.json(
                    failure_cases.head(10).to_dict(orient="records")
                ),
            },
        )

def _resolve_trino_resource(context) -> TrinoResource:
    """Helper to get Trino resource from context."""
    resources = getattr(context, "resources", None)
    trino = None
    if resources is not None:
        trino = getattr(resources, "trino", None)
        if trino is None and isinstance(resources, dict):
            trino = resources.get("trino")
    if trino is None:
        trino = TrinoResource()
    return trino
```

**When to use custom `@asset_check`:**
- Complex validation logic that can't be expressed declaratively
- Custom metric calculations
- Cross-table validation or reconciliation
- Need fine-grained control over error messages and metadata

### Partition-Aware Checks

Quality checks can automatically handle partitioned assets:

```python
@phlo_quality(
    table="silver.fct_glucose_readings",
    checks=[
        NullCheck(columns=["entry_id"]),
        FreshnessCheck(timestamp_column="reading_timestamp", max_age_hours=24),
    ],
    partition_column="reading_date",  # Enables partition-aware checking
    blocking=True,
)
def glucose_readings_quality():
    """Quality checks run per partition automatically."""
    pass
```

For non-partitioned assets or aggregate checks:

```python
@phlo_quality(
    table="postgres.marts.mrt_glucose_hourly_patterns",
    checks=[
        NullCheck(columns=["hour_of_day", "reading_count"]),
        RangeCheck(column="hour_of_day", min_value=0, max_value=23),
        CountCheck(min_rows=1),
    ],
    group="nightscout",
    blocking=True,
    partition_aware=False,  # Check entire table, not per partition
)
def mrt_glucose_hourly_patterns_quality():
    """Declarative quality checks for the hourly glucose patterns mart."""
    pass
```

## dbt Tests Guide

dbt tests are defined in `.yml` files alongside your dbt models in the `workflows/transforms/dbt/models/` directory.

### Standard Tests

dbt provides four built-in tests that cover most common validation needs:

```yaml
# fct_glucose_readings.yml - Schema tests for glucose readings fact table

version: 2

models:
  - name: fct_glucose_readings
    description: "Silver layer fact table for enriched glucose readings"
    columns:
      - name: entry_id
        description: "Unique identifier for the glucose entry"
        data_tests:
          - not_null
          - unique

      - name: glucose_mg_dl
        description: "Blood glucose level in mg/dL"
        data_tests:
          - not_null

      - name: reading_timestamp
        description: "Timestamp when the glucose reading was taken"
        data_tests:
          - not_null

      - name: glucose_category
        description: "Categorized glucose level"
        data_tests:
          - not_null
          - accepted_values:
              arguments:
                values:
                  [
                    "hypoglycemia",
                    "in_range",
                    "hyperglycemia_mild",
                    "hyperglycemia_severe",
                  ]

      - name: is_in_range
        description: "Whether glucose level is within target range"
        data_tests:
          - not_null
          - accepted_values:
              arguments:
                values: [0, 1]
                quote: false

      - name: reading_date
        description: "Date of the glucose reading"
        data_tests:
          - not_null

      - name: hour_of_day
        description: "Hour when reading was taken"
        data_tests:
          - not_null
          - accepted_values:
              arguments:
                values: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
                quote: false
```

**Built-in test types:**
- `not_null` - Ensures column has no NULL values
- `unique` - Ensures all values in column are unique
- `accepted_values` - Ensures values match a specified list
- `relationships` - Ensures foreign key relationships are valid

### Relationship Tests

Test referential integrity between tables:

```yaml
models:
  - name: fct_glucose_readings
    columns:
      - name: user_id
        description: "Reference to user who recorded this reading"
        data_tests:
          - relationships:
              to: ref('dim_users')
              field: user_id
```

### Custom dbt Tests

Create custom tests in `workflows/transforms/dbt/tests/`:

```sql
-- tests/assert_glucose_readings_have_valid_timestamps.sql
-- Test that all glucose readings have timestamps in the past

SELECT
    entry_id,
    reading_timestamp
FROM {{ ref('fct_glucose_readings') }}
WHERE reading_timestamp > CURRENT_TIMESTAMP
```

If the query returns any rows, the test fails.

### Integration with Dagster

dbt tests automatically integrate with Dagster through phlo. When you run `dbt build`, tests are executed and results appear in the Dagster UI.

**Optional wrapper pattern** for explicit control:

```python
from phlo_dbt import phlo_dbt

@phlo_dbt(
    manifest_path="workflows/transforms/dbt/target/manifest.json",
    profiles_dir="workflows/transforms/dbt/profiles",
)
def dbt_models():
    """All dbt models and tests are auto-discovered."""
    pass
```

## pytest Guide

pytest tests live in the `tests/` directory at the root of your phlo project.

### Fixtures from phlo_testing

The `phlo_testing` package provides fixtures for testing without Docker dependencies:

```python
# tests/conftest.py
"""
Pytest configuration and shared fixtures.

This conftest imports phlo_testing fixtures so all tests can use mocked
resources without Docker dependencies.
"""

from pathlib import Path
import pytest

# Import phlo_testing fixtures - these provide mocked Iceberg, Trino, DLT
from phlo_testing.fixtures import (
    load_json_fixture,
    mock_asset_context,
    mock_dlt_source_fixture,
    mock_iceberg_catalog,
    mock_resources,
    mock_trino,
    sample_dataframe,
    sample_dlt_data,
    sample_partition_date,
    sample_partition_range,
    temp_staging_dir,
)

# Re-export so pytest autodiscovers them
__all__ = [
    "mock_iceberg_catalog",
    "mock_trino",
    "mock_asset_context",
    "mock_resources",
    "sample_partition_date",
    "sample_partition_range",
    "sample_dlt_data",
    "sample_dataframe",
    "mock_dlt_source_fixture",
    "temp_staging_dir",
    "load_json_fixture",
    "project_root",
    "reset_test_env",
]


@pytest.fixture(autouse=True)
def reset_test_env(monkeypatch):
    """Reset environment variables before each test."""
    monkeypatch.setenv("PHLO_ENV", "test")
    monkeypatch.setenv("PHLO_LOG_LEVEL", "DEBUG")


@pytest.fixture
def project_root() -> Path:
    """Return path to project root."""
    return Path(__file__).parent.parent
```

**Available fixtures:**
- `mock_iceberg_catalog` - Mock Iceberg catalog (no Docker required)
- `mock_trino` - Mock Trino connection backed by DuckDB
- `mock_asset_context` - Mock Dagster asset context
- `sample_partition_date` - Standard test partition date ("2024-01-15")
- `sample_dlt_data` - Sample records for DLT source mocking
- `temp_staging_dir` - Temporary directory for staging files

### Schema Validation Tests

Test Pandera schema validation logic:

```python
# tests/test_github_user_events.py
"""
Tests for github user_events workflow.

Demonstrates phlo_testing fixtures for testing ingestion workflows
without Docker dependencies.
"""

import pandas as pd
import pytest
from workflows.schemas.github import RawUserEvents


class TestSchemaValidation:
    """Test Pandera schema validation for RawUserEvents."""

    def test_valid_data_passes_validation(self):
        """Test that valid data passes schema validation."""
        test_data = pd.DataFrame(
            [
                {
                    "id": "evt_12345678",
                    "type": "PushEvent",
                    "created_at": "2024-01-15T10:30:00Z",
                    "actor__login": "octocat",
                    "repo__name": "octocat/hello-world",
                },
                {
                    "id": "evt_87654321",
                    "type": "PullRequestEvent",
                    "created_at": "2024-01-15T11:00:00Z",
                    "actor__login": "octocat",
                    "repo__name": "octocat/hello-world",
                },
            ]
        )

        # Should not raise
        validated = RawUserEvents.validate(test_data)
        assert len(validated) == 2
        assert validated["id"].iloc[0] == "evt_12345678"
        assert validated["type"].iloc[1] == "PullRequestEvent"

    def test_unique_key_field_exists(self):
        """Test that unique_key field (id) exists in schema."""
        schema_fields = RawUserEvents.to_schema().columns.keys()
        assert "id" in schema_fields, f"unique_key 'id' not found. Available: {list(schema_fields)}"

    def test_nullable_fields_accept_none(self):
        """Test that str | None fields properly accept None values.

        PhloSchema auto-infers nullable=True from Optional type hints,
        so fields like `actor__login: str | None` will accept None.
        """
        test_data = pd.DataFrame(
            [
                {
                    "id": "evt_null_test",
                    "type": "IssuesEvent",
                    "created_at": "2024-01-15T12:00:00Z",
                    "actor__login": None,  # Nullable field
                    "repo__name": None,  # Nullable field
                },
            ]
        )

        validated = RawUserEvents.validate(test_data)
        assert len(validated) == 1
        assert pd.isna(validated["actor__login"].iloc[0])
        assert pd.isna(validated["repo__name"].iloc[0])

    def test_invalid_duplicate_ids_fails(self):
        """Test that duplicate IDs fail validation (unique constraint)."""
        test_data = pd.DataFrame(
            [
                {
                    "id": "duplicate_id",
                    "type": "PushEvent",
                    "created_at": "2024-01-15T10:00:00Z",
                    "actor__login": "user1",
                    "repo__name": "repo1",
                },
                {
                    "id": "duplicate_id",  # Duplicate!
                    "type": "PushEvent",
                    "created_at": "2024-01-15T11:00:00Z",
                    "actor__login": "user2",
                    "repo__name": "repo2",
                },
            ]
        )

        with pytest.raises(Exception):  # Pandera raises SchemaError
            RawUserEvents.validate(test_data)
```

### Merge Strategy Tests

Test merge strategies (append vs merge) and deduplication behavior:

```python
# tests/test_merge_strategies.py
"""
Comprehensive tests for phlo merge strategies.

Tests all combinations of:
- merge_strategy: append, merge
- deduplication: True, False
- deduplication_method: first, last, hash
"""

import tempfile
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pytest
from phlo_dlt.dlt_helpers import _deduplicate_arrow_table
from phlo_iceberg.resource import IcebergResource
from phlo_iceberg.tables import append_to_table, delete_table, ensure_table, merge_to_table
from pyiceberg.schema import Schema
from pyiceberg.types import IntegerType, NestedField, StringType


@pytest.fixture
def test_schema():
    """Create a test Iceberg schema."""
    return Schema(
        NestedField(1, "id", StringType(), required=True),
        NestedField(2, "value", IntegerType(), required=False),
        NestedField(3, "name", StringType(), required=False),
    )


@pytest.fixture
def sample_data_with_duplicates():
    """Create sample data with duplicate IDs."""
    return [
        {"id": "1", "value": 100, "name": "first"},
        {"id": "2", "value": 200, "name": "second"},
        {"id": "1", "value": 150, "name": "duplicate"},  # Duplicate ID
        {"id": "3", "value": 300, "name": "third"},
    ]


class TestDeduplicationMethods:
    """Test source-level deduplication methods."""

    def test_deduplication_method_first(self, sample_data_with_duplicates):
        """Test 'first' deduplication method keeps first occurrence."""
        df = pd.DataFrame(sample_data_with_duplicates)
        arrow_table = pa.Table.from_pandas(df)

        class MockLog:
            def info(self, msg):
                pass

        class MockContext:
            def __init__(self):
                self.log = MockLog()

        result = _deduplicate_arrow_table(
            arrow_table=arrow_table, unique_key="id", method="first", context=MockContext()
        )

        result_df = result.to_pandas()
        assert len(result_df) == 3, "Should have 3 unique IDs"

        # Should keep first occurrence of ID "1"
        first_row = result_df[result_df["id"] == "1"].iloc[0]
        assert first_row["value"] == 100, "Should keep first value"
        assert first_row["name"] == "first", "Should keep first name"

    def test_deduplication_method_last(self, sample_data_with_duplicates):
        """Test 'last' deduplication method keeps last occurrence."""
        df = pd.DataFrame(sample_data_with_duplicates)
        arrow_table = pa.Table.from_pandas(df)

        class MockLog:
            def info(self, msg):
                pass

        class MockContext:
            def __init__(self):
                self.log = MockLog()

        result = _deduplicate_arrow_table(
            arrow_table=arrow_table, unique_key="id", method="last", context=MockContext()
        )

        result_df = result.to_pandas()
        assert len(result_df) == 3, "Should have 3 unique IDs"

        # Should keep last occurrence of ID "1"
        last_row = result_df[result_df["id"] == "1"].iloc[0]
        assert last_row["value"] == 150, "Should keep last value"
        assert last_row["name"] == "duplicate", "Should keep last name"


class TestMergeStrategy:
    """Test merge strategy (upsert)."""

    @pytest.mark.integration
    def test_merge_idempotent(self, test_schema, test_table_name, sample_data_no_duplicates):
        """Test merge strategy is idempotent - running twice doesn't duplicate."""
        try:
            # Create table
            ensure_table(table_name=test_table_name, schema=test_schema)

            # Create parquet
            df = pd.DataFrame(sample_data_no_duplicates)
            with tempfile.TemporaryDirectory() as tmpdir:
                parquet_path = Path(tmpdir) / "data.parquet"
                df.to_parquet(parquet_path, index=False)

                # First merge
                result1 = merge_to_table(
                    table_name=test_table_name,
                    data_path=str(parquet_path),
                    unique_key="id",
                )
                assert result1["rows_inserted"] == 3

                # Second merge - should delete and re-insert
                result2 = merge_to_table(
                    table_name=test_table_name,
                    data_path=str(parquet_path),
                    unique_key="id",
                )
                # Should delete 3 existing rows and insert 3 new ones
                assert result2["rows_inserted"] == 3

        finally:
            # Cleanup
            try:
                delete_table(test_table_name)
            except Exception:
                pass
```

### Integration Tests with Fixtures

Test workflows using phlo_testing fixtures:

```python
class TestWithFixtures:
    """Tests demonstrating phlo_testing fixtures."""

    def test_with_partition_date(self, sample_partition_date):
        """Test using sample_partition_date fixture."""
        # Fixture provides a standard date for testing
        assert sample_partition_date == "2024-01-15"

    def test_with_mock_catalog(self, mock_iceberg_catalog):
        """Test using mock_iceberg_catalog fixture."""
        # Can create tables without Docker/real Iceberg
        # MockIcebergCatalog accepts dict schema: {"col_name": "type"}
        schema = {"id": "string", "type": "string"}
        table = mock_iceberg_catalog.create_table(
            identifier="raw.test_events",
            schema=schema,
        )
        assert table is not None

    def test_with_mock_trino(self, mock_trino):
        """Test using mock_trino fixture (DuckDB-backed)."""
        cursor = mock_trino.cursor()
        cursor.execute("SELECT 1 as id, 'test' as name")
        result = cursor.fetchall()
        assert result == [(1, "test")]

    def test_with_sample_dlt_data(self, sample_dlt_data):
        """Test using sample_dlt_data fixture."""
        # Fixture provides sample records for DLT source mocking
        assert len(sample_dlt_data) == 3
        assert "id" in sample_dlt_data[0]
```

## Best Practices

### Test Coverage Recommendations

**For every phlo project, you should have:**

1. **Ingestion layer (raw tables)**
   - `@phlo_quality` checks: Row counts, null checks on key fields, freshness
   - pytest: Schema validation tests for Pandera schemas

2. **Transformation layer (silver/gold tables)**
   - dbt tests: Column constraints, relationships, accepted values
   - `@phlo_quality` checks: Business rule validation, range checks
   - pytest: Custom transformation logic tests

3. **Publishing layer (marts)**
   - dbt tests: Final data quality validation
   - `@phlo_quality` checks: SLA monitoring, freshness checks
   - pytest: Integration tests for end-to-end flows

### CI/CD Integration

**Running tests in CI:**

```bash
# Run pytest tests
pytest tests/ -v

# Run dbt tests (within your dbt transform workflow)
cd workflows/transforms/dbt
dbt test --profiles-dir profiles

# Quality checks run automatically as part of Dagster materialization
# They can also be run standalone:
phlo quality run --asset silver.fct_glucose_readings
```

**GitHub Actions example:**

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run pytest
        run: pytest tests/ -v

      - name: Run dbt tests
        run: |
          cd workflows/transforms/dbt
          dbt deps
          dbt test --profiles-dir profiles
```

### Performance Considerations

**Optimize test execution:**

1. **Use appropriate test markers** for pytest:
   ```python
   @pytest.mark.unit
   def test_schema_validation():
       pass

   @pytest.mark.integration
   def test_merge_strategy():
       pass
   ```

   Run only unit tests: `pytest -m unit`

2. **Partition-aware quality checks** reduce runtime:
   - Quality checks with `partition_column` only validate changed partitions
   - Use `partition_aware=False` sparingly for aggregate checks

3. **dbt test selection**:
   ```bash
   # Test only changed models
   dbt test --select state:modified+

   # Test specific model
   dbt test --select fct_glucose_readings
   ```

4. **Mock dependencies in pytest** to avoid Docker:
   - Use `mock_trino` instead of real Trino container
   - Use `mock_iceberg_catalog` for catalog operations
   - Reserve integration tests with real services for critical paths

### Test Organization

**Recommended structure:**

```
your-phlo-project/
├── tests/                          # pytest tests
│   ├── conftest.py                # Shared fixtures
│   ├── test_schemas.py            # Pandera schema tests
│   ├── test_merge_strategies.py   # Merge behavior tests
│   └── test_workflows.py          # Integration tests
├── workflows/
│   ├── ingestion/                 # DLT workflows
│   │   └── schemas/               # Pandera schemas (tested with pytest)
│   ├── quality/                   # @phlo_quality checks
│   │   └── data_quality.py
│   └── transforms/
│       └── dbt/
│           └── models/
│               ├── silver/
│               │   ├── fct_glucose_readings.sql
│               │   └── fct_glucose_readings.yml  # dbt tests
│               └── marts/
│                   ├── mrt_glucose_overview.sql
│                   └── mrt_glucose_overview.yml  # dbt tests
```

### When to Use Blocking Checks

**Blocking checks** (`blocking=True`) prevent downstream assets from materializing if the check fails.

**Use blocking checks for:**
- Critical data quality issues (nulls in primary keys)
- Schema validation failures
- Referential integrity violations
- Data freshness SLA violations

**Use non-blocking checks for:**
- Warning-level issues (e.g., high null percentage but not 100%)
- Monitoring metrics
- Performance benchmarks
- Optional data quality improvements

```python
# Blocking: Critical validation
@phlo_quality(
    table="silver.fct_glucose_readings",
    checks=[
        NullCheck(columns=["entry_id"]),  # Critical
        UniqueCheck(columns=["entry_id"]),  # Critical
    ],
    blocking=True,
)
def critical_quality_checks():
    pass

# Non-blocking: Monitoring
@phlo_quality(
    table="silver.fct_glucose_readings",
    checks=[
        CountCheck(min_rows=100),  # Warning if low volume
    ],
    blocking=False,
)
def monitoring_checks():
    pass
```

## Summary

**Quick reference for choosing the right testing approach:**

| Test Type | Tool | When to Use | Example |
|-----------|------|-------------|---------|
| **Data quality validation** | `@phlo_quality` | Runtime checks on production data | Null checks, freshness, ranges |
| **SQL business rules** | dbt tests | Validation within dbt transformations | Column constraints, relationships |
| **Python unit tests** | pytest | Testing custom Python code | Schema validation, merge logic |
| **Integration tests** | pytest | End-to-end workflow validation | Full pipeline tests with mocks |

**All three approaches complement each other** to provide comprehensive test coverage across your data pipeline. Use the decision matrix at the top of this guide to choose the right tool for each testing need.

For more information:
- [phlo-quality package documentation](/packages/phlo-quality)
- [phlo-testing package documentation](/packages/phlo-testing)
- [dbt testing documentation](https://docs.getdbt.com/docs/build/tests)

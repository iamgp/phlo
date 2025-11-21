# Built-in Functionality Inventory

## Executive Summary

**Status**: EXCELLENT with opportunities for expansion
**Code Reduction**: 74% boilerplate eliminated by `@cascade_ingestion` decorator
**Declarative Coverage**: Ingestion (excellent), Jobs (good), Publishing (good), Transform/Quality (manual)
**Extensibility**: Limited (no plugin system yet)

### Key Findings

- Ingestion decorator is world-class: 270+ lines → 60 lines (74% reduction)
- Schema auto-generation (Pandera → PyIceberg) eliminates duplication
- YAML-driven job and publishing configuration reduces Python boilerplate
- dbt integration for transformations (excellent existing ecosystem)
- Opportunity to extend decorator pattern to quality checks and validations

### Quick Wins Identified

1. Create `@cascade_quality` decorator for data quality checks
2. Add plugin system via Python entry points
3. Expand YAML configuration for schedules and sensors
4. Provide helper functions for common transformation patterns

## Framework Components Inventory

### 1. Decorators

**`@cascade_ingestion`** (src/cascade/ingestion/decorator.py)
- **Lines of Code**: 220
- **Purpose**: Declarative ingestion asset creation
- **Capabilities**: 10+ automated operations
- **Boilerplate Reduction**: 74% (270 lines → 60 lines)

**Automated Operations**:
1. Branch extraction from Dagster context
2. DLT pipeline setup (directory structure)
3. Pandera schema validation
4. DLT staging to parquet
5. PyIceberg schema auto-generation (from Pandera)
6. Iceberg table creation (if not exists)
7. Merge to Iceberg with deduplication
8. Timing instrumentation
9. MaterializeResult generation
10. Freshness policy application
11. Cron schedule registration
12. Asset group assignment

**Parameters** (10):
- `table_name`: Iceberg table name
- `unique_key`: Deduplication column
- `group`: Dagster asset group
- `validation_schema`: Pandera DataFrameModel (optional but recommended)
- `iceberg_schema`: PyIceberg Schema (auto-generated from validation_schema)
- `partition_spec`: Iceberg partitioning (optional)
- `cron`: Cron schedule expression
- `freshness_hours`: (warn_hours, fail_hours) tuple
- `max_runtime_seconds`: Timeout (default: 300)
- `max_retries`: Retry attempts (default: 3)
- `retry_delay_seconds`: Delay between retries (default: 30)
- `validate`: Whether to run Pandera validation (default: True)

**Example Usage**:
```python
@cascade_ingestion(
    table_name="github_user_events",
    unique_key="id",
    validation_schema=RawGitHubUserEvents,
    group="github",
    cron="0 */1 * * *",
    freshness_hours=(1, 24),
)
def github_user_events(partition_date: str):
    return rest_api({...})  # Just return DLT source!
```

**Assessment**: ✅ EXCELLENT - Best-in-class decorator pattern

---

### 2. Schema Auto-Generation

**`pandera_to_iceberg()`** (src/cascade/schemas/converter.py)
- **Lines of Code**: 239
- **Purpose**: Convert Pandera schemas to PyIceberg schemas
- **Boilerplate Elimination**: 100% (no duplicate schema definitions)

**Type Mappings** (7):
- `str` → `StringType()`
- `int` → `LongType()`
- `float` → `DoubleType()`
- `bool` → `BooleanType()`
- `datetime` → `TimestamptzType()`
- `date` → `DateType()`
- `bytes` → `BinaryType()`

**Metadata Preservation**:
- Pandera `Field(description="...")` → PyIceberg `doc` parameter
- Pandera `Field(nullable=False)` → PyIceberg `required=True`
- Pandera `Field(nullable=True)` → PyIceberg `required=False`

**Field ID Management**:
- Data fields: IDs 1-99 (sequential)
- DLT metadata: IDs 100+ (`_dlt_load_id`, `_dlt_id`, `_cascade_ingested_at`)

**Example**:
```python
class RawData(DataFrameModel):
    id: str = Field(nullable=False, description="Unique ID")
    value: int = Field(ge=0, le=100)
    created_at: datetime

# Auto-generated PyIceberg schema (no manual duplication!)
iceberg_schema = pandera_to_iceberg(RawData)
```

**Assessment**: ✅ EXCELLENT - Eliminates schema duplication entirely

---

### 3. DLT Helper Functions

**`setup_dlt_pipeline()`** (src/cascade/ingestion/dlt_helpers.py)
- **Purpose**: Setup DLT pipeline with filesystem staging
- **Returns**: DLT pipeline + local staging path

**`stage_to_parquet()`**
- **Purpose**: Stage data to parquet using DLT
- **Returns**: Parquet file path + elapsed time

**`validate_with_pandera()`**
- **Purpose**: Validate data with Pandera schema
- **Features**: Lazy validation, detailed error reporting
- **Returns**: Boolean (continues on failure with warning)

**`merge_to_iceberg()`**
- **Purpose**: Merge parquet files to Iceberg table
- **Features**: Idempotent deduplication by unique_key
- **Returns**: Rows written + elapsed time

**`get_branch_from_context()`**
- **Purpose**: Extract branch name from Dagster context
- **Fallback**: Run tags → run config → "main"

**`add_cascade_timestamp()`**
- **Purpose**: Add `_cascade_ingested_at` timestamp to records

**Lines of Code**: 238 total
**Assessment**: ✅ GOOD - Comprehensive helper library

---

### 4. YAML-Driven Configuration

**Job Configuration** (src/cascade/defs/jobs/config.yaml)
- **Lines of Code**: 36
- **Purpose**: Declarative job definitions
- **Factory**: `create_jobs_from_config()` reads YAML and creates Dagster jobs

**Features**:
- Group-based asset selection (`type: group`)
- Key-based asset selection (`type: keys`)
- Mixed selection (groups + keys)
- Daily partitioning support
- Resource configuration

**Example**:
```yaml
jobs:
  weather:
    name: "weather_pipeline"
    description: "Weather data ingestion and processing"
    selection:
      type: "group"
      groups: ["weather"]
    partitions: "daily"
```

**Assessment**: ✅ GOOD - Reduces Python boilerplate for common patterns

---

**Publishing Configuration** (src/cascade/defs/publishing/config.yaml)
- **Lines of Code**: 34
- **Purpose**: Declarative publishing from Iceberg to Postgres
- **Factory**: `create_publishing_assets_from_config()` reads YAML

**Features**:
- Table mapping (Postgres name → Iceberg path)
- Dependency declaration (dbt models)
- Group assignment
- Automatic asset creation

**Example**:
```yaml
publishing:
  glucose:
    name: "publish_glucose_marts_to_postgres"
    group: "nightscout"
    description: "Publish glucose curated marts"
    dependencies:
      - "mrt_glucose_hourly_patterns"
    tables:
      mrt_glucose_hourly_patterns: "iceberg_dev.marts.mrt_glucose_hourly_patterns"
```

**Assessment**: ✅ GOOD - Declarative publishing reduces code

---

### 5. Resource Abstractions

**IcebergResource** (src/cascade/defs/resources/iceberg.py)
- **Purpose**: Unified Iceberg catalog interface
- **Features**: Branch-aware operations, transaction support

**TrinoResource** (src/cascade/defs/resources/trino.py)
- **Purpose**: Trino query engine interface
- **Features**: Context manager for cursors, schema selection

**Assessment**: ✅ GOOD - Clean abstractions over complex systems

---

### 6. dbt Integration

**Transform Assets** (src/cascade/defs/transform/dbt.py)
- **Purpose**: Wrap dbt CLI as Dagster assets
- **Features**: Automatic asset dependency graph from dbt manifest

**Layers**:
- Bronze: Staging models (`stg_*`)
- Silver: Fact tables (`fct_*`)
- Gold: Dimensions and aggregates (`dim_*`, `agg_*`)
- Marts: BI-ready tables (`mrt_*`)

**Assessment**: ✅ EXCELLENT - Leverages dbt ecosystem (1000+ packages)

## Comparison with Industry Frameworks

### Prefect: Task/Flow-Based

**Built-in Functionality**:
- `@task` decorator: Retry, cache, timeout
- `@flow` decorator: Orchestration, sub-flows
- Result persistence (local, S3, GCS)
- Deployment API (schedule, trigger)

**Code Example**:
```python
from prefect import flow, task

@task(retries=3, retry_delay_seconds=30)
def fetch_data():
    return requests.get("...").json()

@flow(name="ETL Pipeline")
def etl():
    data = fetch_data()
    return data
```

**Cascade Equivalent**: `@cascade_ingestion` provides similar retry/timeout but for full ingestion pipeline, not individual tasks.

**Gap**: Prefect's granular task-level control vs Cascade's asset-level control. Trade-off: Cascade is higher-level (less boilerplate), Prefect is more flexible.

---

### Dagster: Asset-Based

**Built-in Functionality**:
- `@asset` decorator: Partitions, dependencies
- `@multi_asset`: Multiple outputs from single function
- Asset checks (built-in)
- Metadata API (attach metadata to assets)

**Code Example**:
```python
from dagster import asset, AssetExecutionContext

@asset(
    group_name="github",
    partitions_def=daily_partitions,
)
def github_events(context: AssetExecutionContext):
    data = fetch_github_events()
    return data
```

**Cascade Comparison**:
- Cascade's `@cascade_ingestion` is more opinionated (includes DLT, Pandera, Iceberg)
- Dagster's `@asset` is more flexible (bring your own tools)
- Cascade provides higher-level abstraction

**Gap**: Dagster's `@multi_asset` for multiple outputs. Cascade currently limited to single table per decorator.

---

### dbt: SQL-First

**Built-in Functionality**:
- Jinja templating (` {{ ref('model') }}`)
- Macros library (date_spine, surrogate_key, etc.)
- Incremental materialization strategies
- Tests (unique, not_null, relationships, accepted_values)
- Documentation generation

**Code Example**:
```sql
-- models/staging/stg_customers.sql
WITH source AS (
    SELECT * FROM {{ source('raw', 'customers') }}
)
SELECT
    customer_id,
    customer_name,
    created_at
FROM source
WHERE deleted_at IS NULL
```

**Cascade Integration**: ✅ Excellent - Cascade wraps dbt, provides all dbt functionality

**Gap**: Cascade doesn't reinvent SQL transformations (good decision - leverage dbt)

## Functionality Coverage Matrix

| Capability | Cascade | Prefect | Dagster | dbt | Assessment |
|------------|---------|---------|---------|-----|------------|
| **Ingestion** | Decorator (excellent) | Manual | Manual | N/A | ✅ Best-in-class |
| **Schema Validation** | Pandera (built-in) | Manual | Manual | dbt tests | ✅ Excellent |
| **Schema Auto-Gen** | Pandera→PyIceberg | N/A | N/A | N/A | ✅ Unique feature |
| **Deduplication** | Built-in (unique_key) | Manual | Manual | Incremental | ✅ Excellent |
| **Transformations** | dbt (wrapped) | Manual | Manual | Native | ✅ Excellent (dbt) |
| **Data Quality** | Manual | Manual | Asset checks | dbt tests | ⚠️ Gap (no decorator) |
| **Publishing** | YAML-driven | Manual | Manual | Exposures | ✅ Good |
| **Retry/Timeout** | Built-in | Built-in | Built-in | N/A | ✅ Equivalent |
| **Partitioning** | Daily (built-in) | Manual | Built-in | Incremental | ✅ Good |
| **Metadata** | Automatic | Manual | Built-in | Built-in | ✅ Good |
| **Lineage** | Dagster graph | Prefect UI | Dagster graph | dbt docs | ✅ Excellent |
| **Time Travel** | Iceberg/Nessie | N/A | N/A | N/A | ✅ Unique feature |
| **Branching** | Nessie | N/A | N/A | N/A | ✅ Unique feature |
| **Extensibility** | Limited | Entry points | Entry points | Packages | ❌ Gap |

## Repetitive Code Patterns

### Pattern 1: Data Quality Checks (MANUAL)

**Current Approach**: Manual Dagster assets for quality checks

**Example** (src/cascade/defs/quality/nightscout.py):
```python
@asset(
    group_name="nightscout",
    deps=["glucose_entries"],
)
def glucose_quality_check_nulls(context, trino: TrinoResource):
    with trino.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) as null_count
            FROM raw.glucose_entries
            WHERE sgv IS NULL
        """)
        null_count = cursor.fetchone()[0]

    if null_count > 0:
        context.log.warning(f"Found {null_count} null glucose readings")

    return MaterializeResult(
        metadata={"null_count": null_count}
    )
```

**Boilerplate**:
- Asset decorator configuration
- Resource injection
- SQL query execution
- Threshold checking
- Metadata generation

**Opportunity**: Create `@cascade_quality` decorator

**Proposed**:
```python
@cascade_quality(
    table="raw.glucose_entries",
    group="nightscout",
    checks=[
        NullCheck(column="sgv", max_nulls=0),
        RangeCheck(column="sgv", min=20, max=600),
        FreshnessCheck(max_hours=24),
    ]
)
def glucose_quality():
    pass  # Decorator does everything!
```

**Impact**: 30-40 lines → 5-10 lines (70% reduction)

---

### Pattern 2: Publishing Assets (PARTIALLY AUTOMATED)

**Current Approach**: YAML config + factory function (good!)

**Remaining Boilerplate**:
- Factory function reads YAML
- Creates assets dynamically
- Handles errors

**Assessment**: ✅ Already well-automated via YAML

---

### Pattern 3: Simple Transformations (MANUAL, BUT SHOULD BE dbt)

**Current Pattern**: Some transformations still in Python

**Recommendation**: Move all SQL-based transformations to dbt models. Python should only be for:
- API calls (ingestion)
- Complex business logic (non-SQL)
- Publishing (Iceberg → Postgres)

**Assessment**: ✅ Good separation (Python for ingestion, dbt for transformation)

## YAML vs Python Configuration Balance

### Current Distribution

**YAML Configuration** (2 files):
1. `defs/jobs/config.yaml` (36 lines)
   - Job definitions (asset selection, partitions)
2. `defs/publishing/config.yaml` (34 lines)
   - Publishing table mappings

**Python Configuration**:
1. `config.py` (Pydantic settings) - Environment variables
2. Decorator parameters - Inline with assets
3. dbt project - `dbt_project.yml`

### Evaluation

**YAML Strengths**:
- Declarative (what, not how)
- Non-programmers can edit
- Version control friendly
- Hot-reload without restart (sometimes)

**YAML Weaknesses**:
- Limited logic (no conditionals, loops)
- Type safety issues (caught at runtime)
- Harder to refactor (no IDE support)

**Python Strengths**:
- Full programming language (conditionals, loops, functions)
- Type safety (Pydantic, type hints)
- IDE support (autocomplete, refactoring)
- Testable

**Python Weaknesses**:
- More verbose for simple cases
- Requires restart (no hot-reload)

### Assessment

**Current Balance**: ✅ GOOD
- YAML for declarative patterns (jobs, publishing)
- Python for logic (ingestion, quality, complex transforms)
- Pydantic Settings for environment config

**Recommendation**: Keep current balance. Consider YAML for:
- Schedule definitions (currently Python)
- Sensor definitions (currently Python)

Do NOT move complex logic to YAML (anti-pattern).

## Extensibility Analysis

### Current State: Limited Extensibility

**Internal Modules**:
- All functionality is internal to `cascade` package
- No external plugin system
- Users must fork to extend

**Gap**: No plugin mechanism for:
- Custom ingestion sources (beyond DLT)
- Custom validation checks
- Custom publishing destinations
- Custom quality checks

### Proposed: Python Entry Points

**Entry Point Categories**:

1. `cascade.ingestion` - Custom ingestion decorators
2. `cascade.quality` - Custom quality check decorators
3. `cascade.publishing` - Custom publishing destinations
4. `cascade.validation` - Custom validation schemas

**Example Plugin** (`cascade-plugin-salesforce`):

```python
# pyproject.toml
[project.entry-points."cascade.ingestion"]
salesforce = "cascade_salesforce:SalesforceIngestion"

# cascade_salesforce/__init__.py
from cascade.ingestion import cascade_ingestion

class SalesforceIngestion:
    @staticmethod
    def create_asset(table_name, **kwargs):
        @cascade_ingestion(table_name=table_name, **kwargs)
        def salesforce_data(partition_date: str):
            # Salesforce-specific logic
            return salesforce_api_call()
        return salesforce_data
```

**User Installation**:
```bash
uv add cascade-plugin-salesforce

# Auto-discovered, no code changes needed!
```

**Assessment**: ⚠️ Would significantly improve extensibility

## Missing Built-in Functionality

### Gap 1: Data Quality Decorator

**Current**: Manual quality check assets
**Proposed**: `@cascade_quality` decorator
**Impact**: 70% boilerplate reduction

---

### Gap 2: Validation Decorator

**Current**: Manual Dagster asset checks
**Proposed**: `@cascade_validation` decorator
**Impact**: Standardize validation patterns

Example:
```python
@cascade_validation(
    table="raw.glucose_entries",
    checks=[
        SchemaCheck(expected_schema=RawGlucoseEntries),
        RowCountCheck(min_rows=100),
        FreshnessCheck(max_hours=24),
    ]
)
def validate_glucose_entries():
    pass
```

---

### Gap 3: Transformation Decorator (LOW PRIORITY)

**Current**: dbt models (excellent)
**Proposed**: Optional Python decorator for non-SQL transforms

Example:
```python
@cascade_transform(
    input_table="silver.fct_glucose_readings",
    output_table="gold.agg_daily_stats",
    group="nightscout",
)
def daily_glucose_stats(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("date").agg({
        "sgv": ["mean", "std", "min", "max"]
    })
```

**Assessment**: ⚠️ Low priority - dbt handles most cases

---

### Gap 4: CLI Commands

**Current**: Docker exec commands
**Proposed**: `cascade` CLI with subcommands

Examples:
```bash
cascade materialize --select glucose_entries --partition 2024-01-15
cascade run-job weather_pipeline
cascade create-workflow --type ingestion --domain stripe
cascade validate-schema schemas/weather.py
```

**Assessment**: ❌ Major gap (see Phase 2 audit)

---

### Gap 5: Testing Utilities

**Current**: Manual testing (Docker exec)
**Proposed**: Test helpers for workflow developers

Example:
```python
from cascade.testing import mock_dlt_source, mock_iceberg

def test_glucose_ingestion():
    with mock_dlt_source(data=[...]) as source:
        with mock_iceberg() as catalog:
            result = glucose_entries("2024-01-15")
            assert result.rows_written == 100
```

**Assessment**: ⚠️ Would improve developer experience (see Phase 4)

## Recommendations

### Priority 1 (Quick Wins)

**1. Create `@cascade_quality` decorator**
- Automate data quality checks (null checks, range checks, freshness)
- Reduce boilerplate by 70%
- Standardize quality patterns

**2. Document all built-in helpers**
- Create API reference for dlt_helpers
- Document schema converter patterns
- Provide examples of each helper function

**3. Expand YAML configuration**
- Add schedule definitions to YAML (currently manual Python)
- Add sensor definitions to YAML (for simple patterns)

### Priority 2 (Medium-term)

**4. Implement plugin system via entry points**
- Define entry point categories
- Create plugin template/cookiecutter
- Document plugin development guide

**5. Create `@cascade_validation` decorator**
- Wrap Dagster asset checks
- Provide common validation patterns
- Integrate with Pandera schemas

**6. Add CLI commands**
- Start with `cascade materialize` (wrapper for docker exec)
- Add `cascade create-workflow` (see Phase 2)
- Add `cascade validate-schema`

### Priority 3 (Future)

**7. Testing utilities for workflow developers**
- Mock DLT sources
- Mock Iceberg catalog
- Example test patterns

**8. Transformation decorator (optional)**
- Only if significant demand
- dbt should handle most cases

## Conclusion

**Overall Assessment**: ✅ EXCELLENT with opportunities for expansion

**Strengths**:
1. Ingestion decorator is world-class (74% boilerplate reduction)
2. Schema auto-generation eliminates duplication (100%)
3. YAML-driven jobs and publishing reduce Python code
4. dbt integration leverages excellent ecosystem
5. Clean resource abstractions

**Gaps**:
1. No data quality decorator (opportunity for 70% reduction)
2. No plugin system (limits extensibility)
3. Limited CLI tooling (see Phase 2 audit)
4. No testing utilities for workflow developers

**Priority Actions**:
1. Create `@cascade_quality` decorator for quality checks
2. Implement plugin system via entry points
3. Expand YAML configuration to schedules/sensors
4. Add CLI commands for common operations
5. Create testing utilities package

**Impact**: Cascade already eliminates 74% of ingestion boilerplate. Extending decorator pattern to quality and validation would achieve similar reductions in those areas. Plugin system would enable community contributions without forking.

**Strategic Direction**: Continue decorator-driven approach (excellent), add extensibility for external contributions, maintain YAML/Python balance (good), leverage dbt for transformations (excellent decision).

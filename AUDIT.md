# Codebase Audit Report

**Project**: Lakehouse Kit - Data Lakehouse Platform
**Date**: 2025-10-11
**Total Python LOC**: ~1,076
**Files Analyzed**: 20 Python modules, Docker configs, dependencies

---

## Executive Summary

This is a well-structured data lakehouse platform using modern tools (Dagster, dbt, DuckDB). The code is generally clean and follows many best practices. However, there are critical security issues that need immediate attention, along with opportunities to improve reliability, maintainability, and scalability.

---

## Critical Priority (Fix Immediately)

### 1. Replace Great Expectations with Pandera
**Severity**: CRITICAL (Architecture & Performance)
**Files**: `lakehousekit/defs/quality/nightscout.py`, `definitions.py:33`, `dagster/pyproject.toml`

**Problem**: Great Expectations is causing major architectural compromises:
- Forces use of `in_process_executor` (line definitions.py:33), eliminating ALL parallelism in Dagster
- Requires 197 lines of boilerplate for basic validation (nightscout.py)
- Needs 27 lines just to work around numpy serialization issues (_sanitize_json)
- Causes subprocess crashes that forced the in-process workaround
- Poor integration with modern Dagster patterns

**Impact**:
- Zero parallelism across entire pipeline (huge performance hit)
- Massive maintenance burden (197 lines vs 20 lines)
- Fragile code prone to serialization errors

**Fix**: Migrate to Pandera (native Dagster integration, type-safe, 90% less code)

**Before** (197 lines):
```python
# Complex GE context setup, manual expectations, serialization hacks
context = EphemeralDataContext(project_config=project_config)
validator = context.sources.add_pandas("fact_glucose_readings").read_dataframe(df)
expectations.append(validator.expect_column_values_to_not_be_null(...))
# ... 180+ more lines
```

**After** (20 lines):
```python
import pandera as pa

class FactGlucoseReadings(pa.DataFrameModel):
    entry_id: str = pa.Field(nullable=False, unique=True)
    glucose_mg_dl: int = pa.Field(ge=20, le=600)
    reading_timestamp: pa.DateTime
    direction: str | None = pa.Field(isin=["Flat", "SingleUp", ...])
    is_in_range: bool

@asset_check(asset=AssetKey(["fact_glucose_readings"]))
def nightscout_glucose_quality_check(context) -> AssetCheckResult:
    df = duckdb.connect(str(DUCKDB_PATH)).execute(FACT_QUERY).df()
    try:
        FactGlucoseReadings.validate(df, lazy=True)
        return AssetCheckResult(passed=True)
    except pa.errors.SchemaErrors as err:
        return AssetCheckResult(passed=False, metadata={"failures": ...})
```

**Migration Steps**:
1. Add `pandera[dagster]>=0.18.0` to pyproject.toml
2. Create `lakehousekit/schemas/glucose.py` with Pandera models
3. Replace nightscout.py asset check (delete 180 lines)
4. Remove `executor=dg.in_process_executor` from definitions.py (restore parallelism!)
5. Remove great-expectations from dependencies
6. Delete `great_expectations/` directory

**Benefits**:
- ✅ Restore parallel execution (massive performance improvement)
- ✅ Reduce validation code by 90%
- ✅ Type-safe schemas with IDE support
- ✅ Better error messages
- ✅ No subprocess crashes
- ✅ Native Dagster integration

---

### 2. Hardcoded Credentials in Docker Compose
**Severity**: CRITICAL
**File**: `docker-compose.yml:104,230,263`

Hardcoded secrets in version control:
- `SUPERSET_SECRET_KEY: superset_secret_key_change_me`
- `DATAHUB_SECRET: YouKnowNothing`
- `DATAHUB_SYSTEM_CLIENT_SECRET: JohnSnowKnowsNothing`

**Impact**: Security vulnerability, credentials exposed in git history.

**Fix**:
- Move all secrets to `.env` file (infrastructure already supports this)
- Use `${VARIABLE}` syntax or `${VARIABLE:-}` with no default for secrets
- Update `.env.example` with placeholder values only
- Document that `.env` must be created before deployment

```yaml
# docker-compose.yml
SUPERSET_SECRET_KEY: ${SUPERSET_SECRET_KEY}
DATAHUB_SECRET: ${DATAHUB_SECRET}
```

---

### 3. Credentials Exposed in Web UI
**Severity**: CRITICAL
**File**: `app.py:117-152`

Passwords displayed in plaintext on the hub web interface for MinIO, Superset, and Postgres.

**Impact**: Anyone with network access to the hub can see all service passwords.

**Fix Options**:
1. **Remove password display entirely** (recommended for production)
2. Add authentication to the hub app (Flask-Login + basic auth)
3. Only show passwords in development mode via `FLASK_DEBUG` flag
4. Use "click to reveal" with warning message

```python
# Recommended fix:
if debug:
    # Only show credentials in debug mode
    credentials = {...}
else:
    credentials = None
```

---

### 4. Weak Default Passwords
**Severity**: HIGH
**File**: `.env.example:3,9,19`

Weak, predictable defaults: `lakepass`, `minio999`, `admin123`

**Impact**: Easy to brute force, especially if defaults aren't changed.

**Fix**:
1. Remove default passwords from `.env.example` (use placeholders)
2. Add setup script that generates strong random passwords
3. Document password requirements (min length, complexity)

```bash
# .env.example
POSTGRES_PASSWORD=<generate-strong-password-here>
MINIO_ROOT_PASSWORD=<generate-strong-password-here>
```

---

### 5. Dependency Mismatch: pyproject.toml vs requirements.txt
**Severity**: HIGH
**Files**: `dagster/pyproject.toml` vs `dagster/requirements.txt`

The `requirements.txt` is missing critical dependencies:
- `dagster-airbyte`
- `duckdb-engine`
- `requests`
- `pandas<2.0`
- Several others from pyproject.toml

**Impact**: Builds using `requirements.txt` will fail. Since you use `uv`, this creates confusion.

**Fix**: Remove `requirements.txt` entirely. Use only `pyproject.toml` with `uv`:
```dockerfile
# Dockerfile (already correct)
RUN uv pip install --system -r pyproject.toml
```

---

## High Priority (Fix This Sprint)

### 6. No Retry Logic for External API Calls
**Severity**: HIGH
**File**: `lakehousekit/defs/ingestion/airbyte.py:36-46,66-86`

HTTP requests to Airbyte API have no retry logic. Transient network issues cause failures.

**Impact**: Pipeline failures due to temporary network hiccups.

**Fix**: Add retry logic with exponential backoff:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _get_workspace_id() -> str | None:
    try:
        response = requests.post(
            _get_airbyte_url("/api/v1/workspaces/list"),
            json={},
            timeout=10,  # Also add timeout
        )
        # ... rest of logic
```

---

### 7. Bare Exception Catching Without Logging
**Severity**: HIGH
**File**: `lakehousekit/defs/ingestion/airbyte.py:45-46,85-87`

Silent exception swallowing makes debugging impossible:
```python
except Exception:
    pass
```

**Impact**: Failures happen silently, no visibility into issues.

**Fix**: Log all exceptions with context:
```python
except Exception as e:
    logger.exception(f"Failed to get workspace ID from Airbyte API: {e}")
    return None
```

---

### 8. subprocess.run Without Timeout
**Severity**: HIGH
**File**: `lakehousekit/defs/metadata/datahub.py:25`

DataHub ingestion subprocess can hang indefinitely.

**Impact**: Dagster run hangs, no auto-recovery.

**Fix**: Add timeout and better error handling:
```python
try:
    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=300,  # 5 minutes
        check=False
    )
except subprocess.TimeoutExpired:
    context.log.error("DataHub ingestion timed out after 5 minutes")
    raise
```

---

### 9. Hard-coded Paths Throughout Codebase
**Severity**: MEDIUM
**Files**: `dbt.py:10-11`, `nightscout.py:18`, `raw.py:15`, `duckdb_to_postgres.py:21`

Paths like `/dbt`, `/data/duckdb/warehouse.duckdb` are hardcoded.

**Impact**: Not flexible for different environments, testing is harder.

**Fix**: Use environment variables:
```python
import os
from pathlib import Path

# At module level
DUCKDB_PATH = Path(os.getenv("DUCKDB_WAREHOUSE_PATH", "/data/duckdb/warehouse.duckdb"))
DBT_PROJECT_DIR = Path(os.getenv("DBT_PROJECT_DIR", "/dbt"))
DBT_PROFILES_DIR = Path(os.getenv("DBT_PROFILES_DIR", "/dbt/profiles"))
```

---

### 10. Missing Type Hints
**Severity**: MEDIUM
**Files**: `airbyte.py:33-47`, `raw.py:12-29`, `dbt.py:40-77`

Inconsistent type hint usage. Some functions lack return types and parameter types.

**Impact**: Reduced IDE support, harder to catch bugs early, less maintainable.

**Fix**: Add complete type hints:
```python
from dagster import OpExecutionContext
from typing import Any

def raw_bioreactor_data(context: OpExecutionContext) -> dict[str, Any]:
    """Materialised bioreactor parquet files placed in the raw lake."""
    # ...

def _get_workspace_id() -> str | None:
    """Get the first available workspace ID."""
    # ...
```

Consider enabling strict type checking in `pyproject.toml`:
```toml
[tool.basedpyright]
typeCheckingMode = "strict"
```

---

### 11. No Configuration Management
**Severity**: MEDIUM
**Impact**: Environment variables scattered across multiple files, no validation.

**Fix**: Create centralized configuration module:
```python
# lakehousekit/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_user: str = "lake"
    postgres_password: str  # Required, no default
    postgres_db: str = "lakehouse"

    # Storage
    duckdb_warehouse_path: str = "/data/duckdb/warehouse.duckdb"

    # Services
    airbyte_host: str = "airbyte-server"
    airbyte_api_port: int = 8001

    # Paths
    dbt_project_dir: str = "/dbt"
    dbt_profiles_dir: str = "/dbt/profiles"

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

Usage:
```python
from lakehousekit.config import get_settings

settings = get_settings()
conn = connect(host=settings.postgres_host, port=settings.postgres_port)
```

---

### 12. Using 'latest' Tag for MinIO
**Severity**: MEDIUM
**File**: `docker-compose.yml:20`

`minio/minio:latest` can introduce breaking changes.

**Impact**: Unpredictable behavior on rebuilds, hard to reproduce issues.

**Fix**: Pin to specific release:
```yaml
minio:
  image: minio/minio:RELEASE.2024-10-02T17-50-41Z
```

---

### 13. No README or Documentation
**Severity**: MEDIUM
**Impact**: Hard for new developers to onboard, setup issues.

**Fix**: Create comprehensive `README.md`:
```markdown
# Lakehouse Kit

Modern data lakehouse platform built with Dagster, dbt, and DuckDB.

## Architecture
- Dagster: Orchestration
- dbt: Transformations
- DuckDB: Data warehouse
- Postgres: Metadata & marts
- MinIO: Object storage
- Airbyte: Data ingestion

## Quick Start
1. Copy `.env.example` to `.env` and configure
2. Run `docker-compose up -d`
3. Access services at http://localhost:54321

## Services
- Hub: http://localhost:54321
- Dagster: http://localhost:3000
- Superset: http://localhost:8088
[... etc ...]

## Development
[Setup instructions]

## Troubleshooting
[Common issues]
```

---

## Medium Priority (Next Sprint)

### 14. Missing Data Validation on Asset Outputs
**Severity**: MEDIUM
**Files**: `raw.py:12-29`, `duckdb_to_postgres.py:20-94`

Assets return unvalidated dictionaries. Schema changes could break downstream assets silently.

**Fix**: Use Pydantic for output validation:
```python
from pydantic import BaseModel

class RawDataOutput(BaseModel):
    status: str
    path: str
    file_count: int
    files: list[str]

@asset(group_name="raw_ingestion")
def raw_bioreactor_data(context) -> RawDataOutput:
    # ...
    return RawDataOutput(
        status="available",
        path=raw_path,
        file_count=len(files),
        files=files[:10]
    )
```

---

### 15. No Connection Pooling for Database Connections
**Severity**: MEDIUM
**Files**: `duckdb_to_postgres.py:49`, `nightscout.py:60`

Each asset opens new DuckDB connection. For frequent executions, this is inefficient.

**Fix**: Create DuckDB resource with connection pooling:
```python
# lakehousekit/defs/resources/__init__.py
from dagster import ConfigurableResource
import duckdb

class DuckDBResource(ConfigurableResource):
    database_path: str = "/data/duckdb/warehouse.duckdb"

    def get_connection(self):
        return duckdb.connect(database=self.database_path)

def build_defs() -> dg.Definitions:
    return dg.Definitions(
        resources={
            "airbyte": _build_airbyte_resource(),
            "dbt": _build_dbt_resource(),
            "duckdb": DuckDBResource(),
        }
    )
```

---

### 16. Inconsistent Error Handling Patterns
**Severity**: MEDIUM
**Files**: `airbyte.py`, `nightscout.py`

Mix of try/except with warnings, raising errors, returning None.

**Fix**: Establish conventions:
```python
# Convention guidelines:
# 1. Validation errors -> raise ValueError with clear message
# 2. External service failures -> log warning and return None/default
# 3. Critical failures -> raise RuntimeError
# 4. Always log context before raising

# Example:
def _resolve_connection_id(config: AirbyteConnectionConfig) -> str:
    """Resolve connection ID, raise if not found."""
    connection_id = _lookup_connection_by_name(config.connection_name)

    if connection_id:
        return connection_id

    if config.connection_id:
        logger.info(f"Using fallback ID for '{config.connection_name}'")
        return config.connection_id

    # Critical - can't proceed without connection ID
    raise ValueError(
        f"Cannot resolve Airbyte connection '{config.connection_name}'. "
        "Connection not found in workspace and no fallback ID provided."
    )
```

---

### 17. Magic Numbers in Code
**Severity**: LOW
**File**: `nightscout.py:122-128`

Hardcoded values like `20`, `600` for glucose ranges lack explanation.

**Fix**: Extract to named constants:
```python
# At module level
MIN_GLUCOSE_MG_DL = 20  # Minimum physiologically possible glucose reading
MAX_GLUCOSE_MG_DL = 600  # Maximum CGM meter reading
VALID_DIRECTIONS = [
    "Flat", "FortyFiveUp", "FortyFiveDown",
    "SingleUp", "SingleDown", "DoubleUp", "DoubleDown",
    "NONE", None
]

# In validation:
expectations.append(
    validator.expect_column_values_to_be_between(
        column="glucose_mg_dl",
        min_value=MIN_GLUCOSE_MG_DL,
        max_value=MAX_GLUCOSE_MG_DL
    )
)
```

---

### 18. Missing Docstrings for Public Functions
**Severity**: LOW
**Files**: `schedules/pipeline.py:6-19`, `resources/__init__.py:10-20`

Some public functions lack docstrings.

**Fix**: Add comprehensive docstrings:
```python
def build_asset_jobs() -> list[dg.UnresolvedAssetJobDefinition]:
    """
    Build Dagster job definitions for the lakehouse pipeline.

    Returns:
        List of job definitions:
        - ingest_raw_data: Syncs data from external sources via Airbyte
        - transform_dbt_models: Runs complete dbt transformation pipeline
    """
    # ...
```

---

### 19. DuckDB Version Pinned Without Comment
**Severity**: LOW
**File**: `dagster/pyproject.toml:11`

`duckdb==1.1.0` pinned without explanation.

**Fix**: Add comment or use `~=` for patch updates:
```toml
dependencies = [
    # Pinned to 1.1.x for stability with dbt-duckdb compatibility
    "duckdb~=1.1.0",
    # Or if specific version needed:
    "duckdb==1.1.0",  # Required for postgres extension compatibility
]
```

---

### 20. No Health Check for Hub Service
**Severity**: LOW
**File**: `docker-compose.yml:120-145`

Hub service lacks health check unlike other services.

**Fix**: Add health check:
```yaml
hub:
  # ... existing config ...
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:${APP_PORT:-54321}/"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 10s
```

---

### 21. Docker Volume Mounts Missing Read-Only Flag
**Severity**: LOW
**Files**: `docker-compose.yml:62-66,86-91`

Source code mounted as volumes without `:ro` (read-only) flag.

**Fix**: Add read-only where write access not needed:
```yaml
volumes:
  - ./dagster:/opt/dagster:ro
  - ./lakehousekit:/opt/dagster/lakehousekit:ro
  - ./dbt:/dbt  # Needs write for target/
  - ./data:/data  # Needs write
  - ./great_expectations:/great_expectations  # Needs write for validations
```

---

### 22. Unused or Unclear Pandas Dependency
**Severity**: LOW
**File**: `dagster/pyproject.toml:22`

`pandas<2.0` is pinned but only indirectly used via Great Expectations.

**Fix**: Document why it's needed:
```toml
dependencies = [
    # ... other deps ...
    "pandas<2.0",  # Required by great-expectations, pinned for stability
]
```

Or remove if Great Expectations handles it:
```bash
# Test if removal breaks anything:
uv pip install -r pyproject.toml --constraint pandas>=2.0
# Run tests
```

---

## Low Priority (Technical Debt)

### 23. In-Process Executor Used Globally
**Severity**: LOW
**File**: `definitions.py:33`

In-process executor prevents parallelism but avoids Great Expectations crashes (documented in comment).

**Impact**: Sequential execution, slower for large asset graphs.

**Fix**: Consider selective override:
```python
def _merged_definitions() -> dg.Definitions:
    merged = dg.Definitions.merge(...)

    return dg.Definitions(
        assets=merged.assets,
        asset_checks=merged.asset_checks,
        schedules=merged.schedules,
        resources=merged.resources,
        jobs=merged.jobs,
        # Default to multiprocess for parallelism
        executor=dg.multiprocess_executor,
        # Override for specific problematic assets
    )

# In nightscout.py asset check:
@asset_check(
    # ... other params ...
    op_tags={"dagster/executor": "in_process"}  # Force in-process for GE
)
```

---

### 24. No Asset Partitioning Strategy
**Severity**: LOW
**Impact**: All data processed at once, not scalable for growing datasets.

**Fix**: Implement time-based partitions for incremental processing:
```python
from dagster import DailyPartitionsDefinition

daily_partition = DailyPartitionsDefinition(start_date="2024-01-01")

@asset(
    partitions_def=daily_partition,
    group_name="staging"
)
def stg_glucose_readings(context, raw_nightscout_entries):
    partition_date = context.partition_key
    # Process only data for partition_date
    # ...
```

---

### 25. Schedule Runs All Assets
**Severity**: LOW
**File**: `schedules/pipeline.py:15`

Transform job uses `AssetSelection.all()` which includes raw ingestion.

**Impact**: Ingestion might be triggered unintentionally by transform schedule.

**Fix**: Create granular selections:
```python
def build_asset_jobs() -> list[dg.UnresolvedAssetJobDefinition]:
    ingest_job = dg.define_asset_job(
        name="ingest_raw_data",
        selection=dg.AssetSelection.groups("raw_ingestion"),
        description="Sync data from sources via Airbyte",
    )

    # Only transform layers, not ingestion
    transform_job = dg.define_asset_job(
        name="transform_dbt_models",
        selection=dg.AssetSelection.groups(
            "staging", "intermediate", "curated", "marts"
        ),
        description="Run dbt models only",
    )

    # Full pipeline including ingestion
    full_pipeline_job = dg.define_asset_job(
        name="full_pipeline",
        selection=dg.AssetSelection.all(),
        description="Complete end-to-end pipeline",
    )

    return [ingest_job, transform_job, full_pipeline_job]
```

---

### 26. Missing Monitoring and Alerting
**Severity**: LOW
**Impact**: No proactive notification of failures, must check Dagster UI.

**Fix**: Add Dagster monitoring features:
```python
# lakehousekit/defs/sensors/__init__.py
import dagster as dg

@dg.asset_sensor(
    asset_key=dg.AssetKey("fact_glucose_readings"),
    job=my_alert_job
)
def fact_glucose_freshness_sensor(context, asset_event):
    """Alert if fact table hasn't been updated in 24 hours."""
    # Check freshness logic
    pass

# Add to definitions.py:
def _merged_definitions() -> dg.Definitions:
    # ... existing merges ...
    return dg.Definitions(
        # ... existing ...
        sensors=[fact_glucose_freshness_sensor],
        # Add run failure hooks
    )
```

Add asset checks for freshness:
```python
@asset_check(
    asset=AssetKey("fact_glucose_readings"),
    description="Ensure data is no more than 24 hours old"
)
def check_data_freshness(context):
    # Query max timestamp from data
    # Compare to current time
    # Return AssetCheckResult
    pass
```

---

### 27. No Testing Infrastructure
**Severity**: LOW
**Impact**: Changes may break existing functionality without detection.

**Fix**: Add test structure:
```
lakehousekit/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # pytest fixtures
│   ├── unit/
│   │   ├── test_airbyte.py      # Unit tests for utility functions
│   │   ├── test_config.py
│   │   └── test_transforms.py
│   └── integration/
│       ├── test_assets.py        # Asset execution tests
│       └── test_resources.py     # Resource integration tests
```

Example test:
```python
# tests/unit/test_airbyte.py
import pytest
from lakehousekit.defs.ingestion.airbyte import _lookup_connection_by_name
from unittest.mock import patch, Mock

def test_lookup_connection_by_name_success():
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "connections": [
            {"name": "test-conn", "connectionId": "123"}
        ]
    }

    with patch('requests.post', return_value=mock_response):
        result = _lookup_connection_by_name("test-conn")
        assert result == "123"

def test_lookup_connection_by_name_not_found():
    # ... test not found case
```

Add to `pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]

[project.optional-dependencies]
dev = ["pytest", "pytest-cov", "pytest-mock"]
```

---

### 28. No Environment Variable Validation at Startup
**Severity**: LOW
**Impact**: Failures occur during execution rather than at startup.

**Fix**: Add validation in `definitions.py`:
```python
from lakehousekit.config import get_settings

def _merged_definitions() -> dg.Definitions:
    # Validate configuration at load time
    try:
        settings = get_settings()
        logger.info(f"Configuration loaded successfully for {settings.postgres_host}")
    except ValidationError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise

    # ... rest of definitions
```

---

### 29. Insufficient Inline Comments for Complex Logic
**Severity**: LOW
**File**: `nightscout.py:198-224`

JSON sanitization functions are complex but lack explanation.

**Fix**: Add detailed comments:
```python
def _sanitize_json(value):
    """
    Recursively sanitize values for JSON serialization.

    Great Expectations returns numpy types (np.int64, np.ndarray) which
    are not JSON serializable. This function converts:
    - numpy scalars -> Python primitives (via .item())
    - numpy arrays -> Python lists (via .tolist())
    - nested dicts/lists -> recursively sanitized

    This is necessary because Dagster metadata must be JSON-serializable
    for storage and API responses.
    """
    if isinstance(value, dict):
        return {k: _sanitize_json(v) for k, v in value.items()}
    # ... rest with comments
```

---

## Summary Checklist

### Immediate (This Week)
- [ ] **PRIORITY 1**: Migrate from Great Expectations to Pandera (restore parallelism, reduce 197 lines to 20)
- [ ] Remove hardcoded secrets from docker-compose.yml
- [ ] Remove/protect password display in web UI
- [ ] Generate strong default passwords
- [ ] Remove requirements.txt or sync with pyproject.toml

### Short Term (This Sprint)
- [ ] Add retry logic to API calls
- [ ] Add proper exception logging
- [ ] Add subprocess timeouts
- [ ] Extract hardcoded paths to environment variables
- [ ] Add comprehensive type hints
- [ ] Implement configuration management with Pydantic
- [ ] Pin MinIO to specific version
- [ ] Create README.md with setup instructions

### Medium Term (Next Sprint)
- [ ] Add Pydantic validation for asset outputs
- [ ] Implement DuckDB resource with connection pooling
- [ ] Standardize error handling patterns
- [ ] Extract magic numbers to named constants
- [ ] Add docstrings to all public functions
- [ ] Document/fix DuckDB version pin
- [ ] Add health check to hub service
- [ ] Add read-only flags to docker volumes
- [ ] Document or remove pandas<2.0 constraint

### Long Term (Technical Debt)
- [ ] Evaluate selective in-process executor usage
- [ ] Implement time-based partitioning for incremental processing
- [ ] Refine job/schedule granularity
- [ ] Add monitoring sensors and asset freshness checks
- [ ] Implement comprehensive test suite
- [ ] Add startup configuration validation
- [ ] Add detailed inline comments for complex logic

---

## Positive Observations

The codebase has many strengths worth noting:
- Clean modular structure with clear separation of concerns
- Good use of Dagster's modern features (asset-based definitions)
- Resilient Airbyte connection lookup by name (survives Docker restarts)
- Proper use of modern Python (3.11+, type hints where present)
- Good error handling in Great Expectations integration
- Comprehensive docker-compose setup with health checks
- Uses `uv` for fast dependency management
- Follows `ruff` and `basedpyright` tooling standards

The foundation is solid; these recommendations will make it production-ready.

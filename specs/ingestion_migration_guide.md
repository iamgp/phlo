# Cascade Ingestion Migration Guide

This guide helps you migrate from the old ingestion pattern to the new simplified decorator-based approach with automatic schema generation.

## Overview of Changes

### What Changed

1. **Schema Duplication Eliminated**: Define only Pandera schemas - PyIceberg schemas are auto-generated
2. **Decorator-Based Assets**: Use `@cascade_ingestion` decorator instead of manual boilerplate
3. **Automatic Discovery**: Assets are auto-registered, no manual imports needed
4. **DLT rest_api Integration**: Use DLT's rest_api source for API ingestion

### Benefits

- 74% reduction in code (270+ lines → 60-70 lines per asset)
- Single source of truth for schemas (Pandera only)
- No schema drift between validation and storage
- Automatic metadata handling (DLT fields, timestamps)
- Cleaner, more maintainable codebase

## Migration Steps

### Step 1: Update Pandera Schema (if needed)

Ensure your Pandera schema includes proper metadata for auto-generation:

**Before** (minimal metadata):
```python
class RawGlucoseEntries(DataFrameModel):
    _id: str
    sgv: int
    date: int
```

**After** (rich metadata):
```python
class RawGlucoseEntries(DataFrameModel):
    """Raw glucose entries from Nightscout API."""

    _id: str = Field(nullable=False, unique=True, description="Unique entry ID")
    sgv: int = Field(ge=1, le=1000, nullable=False, description="Sensor glucose value")
    date: int = Field(nullable=False, description="Unix timestamp")
    date_string: datetime = Field(nullable=False, description="ISO 8601 timestamp")
    direction: str | None = Field(nullable=True, description="Trend direction")
```

**Key Changes**:
- Add `Field()` with `nullable`, `description` for proper mapping
- Use type unions (`str | None`) for optional fields
- Add class docstring for documentation

### Step 2: Delete PyIceberg Schema Definition

**Remove** the duplicate PyIceberg schema from `src/phlo/iceberg/schema.py`:

```python
# DELETE THIS - no longer needed!
GLUCOSE_ENTRIES_SCHEMA = Schema(
    NestedField(1, "_id", StringType(), required=False, doc="Unique entry ID"),
    NestedField(2, "sgv", LongType(), required=False, doc="Sensor glucose value"),
    # ... etc
)
```

### Step 3: Migrate Asset to Decorator Pattern

#### Option A: Using DLT rest_api (Recommended for APIs)

**Before** (manual boilerplate):
```python
import dlt
import pandas as pd
import requests
from datetime import datetime, timezone

from phlo.config import config
from phlo.defs.partitions import daily_partition
from phlo.defs.resources.iceberg import IcebergResource
from phlo.iceberg.schema import GLUCOSE_ENTRIES_SCHEMA
from phlo.ingestion.dlt_helpers import (
    get_branch_from_context,
    merge_to_iceberg,
    setup_dlt_pipeline,
    stage_to_parquet,
    validate_with_pandera,
)
from phlo.schemas.glucose import RawGlucoseEntries
from phlo.schemas.registry import get_table_config

@dg.asset(
    name="dlt_glucose_entries",
    group_name="nightscout",
    partitions_def=daily_partition,
    compute_kind="dlt+pyiceberg",
)
def dlt_glucose_entries(context, iceberg: IcebergResource) -> dg.MaterializeResult:
    partition_date = context.partition_key
    pipeline_name = f"glucose_entries_{partition_date.replace('-', '_')}"
    branch_name = get_branch_from_context(context)
    table_config = get_table_config("glucose_entries")

    # Manual API call
    start_time_iso = f"{partition_date}T00:00:00.000Z"
    end_time_iso = f"{partition_date}T23:59:59.999Z"

    response = requests.get(
        f"{config.nightscout_url}/api/v1/entries.json",
        params={
            "count": 10000,
            "find[dateString][$gte]": start_time_iso,
            "find[dateString][$lt]": end_time_iso,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    # Convert to DataFrame
    df = pd.DataFrame(data)
    df["_cascade_ingested_at"] = datetime.now(timezone.utc)

    # Manual validation
    validate_with_pandera(context, df, RawGlucoseEntries, "glucose_entries")

    # Manual DLT setup
    pipeline, local_staging_root = setup_dlt_pipeline(
        pipeline_name=pipeline_name,
        dataset_name="nightscout",
    )

    # Manual staging
    @dlt.resource(name="entries", write_disposition="replace")
    def entries_resource():
        yield df.to_dict(orient="records")

    parquet_path, dlt_elapsed = stage_to_parquet(
        context=context,
        pipeline=pipeline,
        dlt_source=entries_resource(),
        local_staging_root=local_staging_root,
    )

    # Manual merge
    merge_metrics = merge_to_iceberg(
        context=context,
        iceberg=iceberg,
        table_config=table_config,
        parquet_path=parquet_path,
        branch_name=branch_name,
    )

    return dg.MaterializeResult(
        metadata={
            "rows_inserted": dg.MetadataValue.int(merge_metrics["rows_inserted"]),
            # ... more metadata
        }
    )
```

**After** (simplified with rest_api):
```python
from dlt.sources.rest_api import rest_api

from phlo.ingestion import cascade_ingestion
from phlo.schemas.glucose import RawGlucoseEntries

@cascade_ingestion(
    table_name="glucose_entries",
    unique_key="_id",
    validation_schema=RawGlucoseEntries,  # PyIceberg schema auto-generated!
    group="nightscout",
    cron="0 */1 * * *",
    freshness_hours=(1, 24),
)
def glucose_entries(partition_date: str):
    """
    Ingest Nightscout glucose entries using DLT rest_api source.

    Fetches CGM glucose readings from the Nightscout API for a specific partition date,
    stages to parquet, and merges to Iceberg with idempotent deduplication.
    """
    start_time_iso = f"{partition_date}T00:00:00.000Z"
    end_time_iso = f"{partition_date}T23:59:59.999Z"

    return rest_api({  # type: ignore[arg-type]
        "client": {
            "base_url": "https://your-nightscout.com/api/v1",
        },
        "resources": [{
            "name": "entries",
            "endpoint": {
                "path": "entries.json",
                "params": {
                    "count": 10000,
                    "find[dateString][$gte]": start_time_iso,
                    "find[dateString][$lt]": end_time_iso,
                },
            },
        }],
    })
```

**Eliminated**:
- Manual branch extraction
- Manual table config lookup
- Manual API requests
- Manual DataFrame conversion
- Manual validation
- Manual DLT pipeline setup
- Manual staging
- Manual merge
- Manual result generation
- Duplicate PyIceberg schema definition

#### Option B: Using Custom DLT Resource

**Before** (manual boilerplate):
```python
# Same 270+ lines as Option A above
```

**After** (custom resource):
```python
import dlt
import requests
from datetime import datetime, timezone

from phlo.config import config
from phlo.ingestion import cascade_ingestion
from phlo.schemas.github import RawGitHubRepoStats

@dlt.resource(name="repo_stats", write_disposition="replace")
def fetch_repo_stats(partition_date: str):
    """Fetch GitHub repository statistics."""
    # Custom fetch logic here
    repos = fetch_repos()

    for repo in repos:
        repo_stats = {
            "repo_name": repo["name"],
            "collection_date": partition_date,
            "_cascade_ingested_at": datetime.now(timezone.utc),
        }
        # Fetch stats...
        yield repo_stats

@cascade_ingestion(
    table_name="github_repo_stats",
    unique_key="_dlt_id",
    validation_schema=RawGitHubRepoStats,  # PyIceberg schema auto-generated!
    group="github",
    cron="0 2 * * *",
    freshness_hours=(24, 48),
    max_runtime_seconds=600,
)
def github_repo_stats(partition_date: str):
    """
    Ingest GitHub repository statistics using custom DLT resource.

    Fetches repository statistics for all user repos for a partition date,
    stages to parquet, and merges to Iceberg with idempotent deduplication.
    """
    return fetch_repo_stats(partition_date)
```

### Step 4: Update Domain __init__.py (if needed)

If you created a new domain directory, ensure it's imported in `src/phlo/defs/ingestion/__init__.py`:

```python
from phlo.defs.ingestion import github  # noqa: F401
from phlo.defs.ingestion import nightscout  # noqa: F401
# Add your new domain here if needed
```

### Step 5: Test Migration

Run tests to verify the migration:

```bash
# Run schema converter tests
uv run pytest tests/test_schema_converter.py -v

# Run decorator tests
uv run pytest tests/test_ingestion_decorator.py -v

# Run all tests
uv run pytest -v
```

## Common Migration Issues

### Issue 1: Type Mapping Errors

**Error**: `SchemaConversionError: Cannot map Pandera type 'list' for field 'tags'`

**Solution**: Pandera lists/arrays are not supported. Use JSON string instead:

```python
# Before
tags: list[str]  # Not supported

# After
tags: str = Field(description="JSON-encoded array of tags")
```

### Issue 2: Missing Field Metadata

**Error**: Field is required in Iceberg but should be optional

**Solution**: Add explicit `Field(nullable=True)`:

```python
# Before
direction: str | None  # Might not map correctly

# After
direction: str | None = Field(nullable=True, description="Trend direction")
```

### Issue 3: Custom PyIceberg Schema Needed

**Error**: Need custom partition spec or advanced Iceberg features

**Solution**: Provide explicit `iceberg_schema` alongside `validation_schema`:

```python
from phlo.schemas.converter import pandera_to_iceberg

# Generate base schema, then customize
base_schema = pandera_to_iceberg(RawMyData)

# Or provide fully custom schema
custom_schema = Schema(
    NestedField(1, "id", StringType(), required=True),
    # ... custom fields
)

@cascade_ingestion(
    table_name="my_table",
    unique_key="id",
    validation_schema=RawMyData,  # Still used for validation
    iceberg_schema=custom_schema,  # Custom schema used for table creation
    group="my_domain",
)
def my_asset(partition_date: str):
    return rest_api({...})
```

## Verification Checklist

After migration, verify:

- [ ] Pandera schema has proper metadata (nullable, description)
- [ ] PyIceberg schema is auto-generated correctly
- [ ] Asset is automatically discovered (check Dagster UI)
- [ ] Test ingestion completes successfully
- [ ] Iceberg table created with correct schema
- [ ] Data validation passes
- [ ] Deduplication works (run same partition twice)
- [ ] Branch-aware writes work correctly
- [ ] Monitoring/metrics are captured

## Migration Example: Complete Before/After

### Before (270 lines)

```
src/phlo/iceberg/schema.py (50 lines)
  - Manual PyIceberg schema definition

src/phlo/schemas/glucose.py (30 lines)
  - Pandera validation schema

src/phlo/defs/ingestion/dlt_assets.py (190 lines)
  - Manual branch extraction
  - Manual table config
  - Manual API requests
  - Manual validation
  - Manual DLT setup
  - Manual staging
  - Manual merge
  - Manual result generation
```

### After (60 lines)

```
src/phlo/schemas/glucose.py (30 lines)
  - Enhanced Pandera schema with metadata
  - PyIceberg schema auto-generated!

src/phlo/defs/ingestion/nightscout/glucose.py (30 lines)
  - @cascade_ingestion decorator
  - DLT rest_api source
  - Automatic everything!
```

## Getting Help

If you encounter issues during migration:

1. Check test files for examples: `tests/test_schema_converter.py`, `tests/test_ingestion_decorator.py`
2. Review existing migrated assets: `defs/ingestion/nightscout/glucose.py`, `defs/ingestion/github/events.py`
3. Read the PRD: `specs/schema_converter.md`
4. Check the README: `defs/ingestion/README.md`

## Next Steps

After successful migration:

1. Delete old PyIceberg schema definitions from `iceberg/schema.py`
2. Remove old boilerplate asset code
3. Update any documentation referencing old patterns
4. Consider migrating other assets to the new pattern

# Cascade Ingestion Assets

This directory contains data ingestion assets organized by domain. Assets are automatically discovered using the `@cascade_ingestion` decorator.

## Architecture

### Automatic Discovery

Assets are automatically registered when decorated with `@cascade_ingestion`. No manual registration required in `__init__.py`.

```python
from phlo.ingestion import cascade_ingestion

@cascade_ingestion(
    table="my_table",
    group="my_domain",
    cron="0 */1 * * *",
    freshness_hours=(1, 24),
)
def my_asset(partition_date: str):
    return dlt.resource(...)  # Just return DLT source/resource
```

### Directory Structure

```
ingestion/
  nightscout/
    glucose.py          # Nightscout glucose data ingestion
  github/
    events.py           # GitHub user events ingestion
    repos.py            # GitHub repository statistics ingestion
```

## Adding New Ingestion Assets

### 1. Define Pandera Schema (Single Source of Truth)

Define only a Pandera validation schema - the PyIceberg schema is auto-generated!

**Pandera Validation Schema** (`src/phlo/schemas/my_domain.py`):
```python
from datetime import datetime
from pandera.pandas import DataFrameModel, Field

class RawMyData(DataFrameModel):
    """Raw data from my API."""

    id: str = Field(nullable=False, unique=True, description="Unique identifier")
    created_at: datetime = Field(nullable=False, description="Record creation timestamp")
    value: int = Field(ge=0, le=100, description="Data value")
    status: str | None = Field(nullable=True, description="Optional status")
```

The PyIceberg schema is automatically generated from this Pandera schema with:
- Type mapping: str→StringType, int→LongType, datetime→TimestamptzType, etc.
- Field metadata: nullable→required, description→doc
- Automatic DLT metadata fields: `_dlt_load_id`, `_dlt_id`

### 2. Create Asset Module

Create a new file in the appropriate domain directory:

**Using DLT rest_api (Recommended)**:
```python
from dlt.sources.rest_api import rest_api

from phlo.ingestion import cascade_ingestion
from phlo.schemas.my_domain import RawMyData

@cascade_ingestion(
    table_name="my_table",
    unique_key="id",
    validation_schema=RawMyData,  # PyIceberg schema auto-generated!
    group="my_domain",
    cron="0 */1 * * *",
    freshness_hours=(1, 24),
)
def my_asset(partition_date: str):
    """Ingest my data from external API."""
    return rest_api({  # type: ignore[arg-type]
        "client": {
            "base_url": "https://api.example.com",
        },
        "resources": [{
            "name": "my_resource",
            "endpoint": {
                "path": "data",
                "params": {
                    "date": partition_date,
                },
            },
        }],
    })
```

**Using Custom DLT Resource**:
```python
import dlt

from phlo.ingestion import cascade_ingestion
from phlo.schemas.my_domain import RawMyData

@dlt.resource(name="my_resource", write_disposition="replace")
def fetch_my_data(partition_date: str):
    """Fetch data from custom source."""
    data = fetch_from_somewhere(partition_date)
    for record in data:
        yield record

@cascade_ingestion(
    table_name="my_table",
    unique_key="id",
    validation_schema=RawMyData,  # PyIceberg schema auto-generated!
    group="my_domain",
    cron="0 */1 * * *",
    freshness_hours=(1, 24),
)
def my_asset(partition_date: str):
    """Ingest my data using custom DLT resource."""
    return fetch_my_data(partition_date)
```

### 3. Add Domain Import (if new domain)

If creating a new domain directory, add it to `src/phlo/defs/ingestion/__init__.py`:

```python
from phlo.defs.ingestion import github  # noqa: F401
from phlo.defs.ingestion import nightscout  # noqa: F401
from phlo.defs.ingestion import my_domain  # noqa: F401  <-- Add this
```

### 4. That's It!

Your asset will be automatically discovered and registered. No need to manually add it to asset lists.

## Decorator Parameters

```python
@cascade_ingestion(
    # Required:
    table_name="my_table",             # Iceberg table name (without namespace)
    unique_key="id",                   # Column for deduplication
    validation_schema=RawMyData,       # Pandera DataFrameModel (PyIceberg auto-generated)
    group="nightscout",                # Dagster asset group name

    # Optional:
    iceberg_schema=None,               # Explicit PyIceberg Schema (optional, auto-generated from validation_schema)
    partition_spec=None,               # Iceberg partition spec (optional)
    cron="0 */1 * * *",               # Cron schedule (optional)
    freshness_hours=(1, 24),          # (warn_hours, fail_hours) (optional)
    max_runtime_seconds=300,          # Maximum runtime before timeout
    max_retries=3,                    # Retry attempts on failure
    retry_delay_seconds=30,           # Delay between retries
    validate=True,                    # Enable Pandera validation
)
```

**Note**: Either `validation_schema` (recommended) or `iceberg_schema` must be provided. If both are provided, `iceberg_schema` takes precedence over auto-generation.

## Schema Auto-Generation

The decorator automatically generates PyIceberg schemas from Pandera validation schemas, eliminating schema duplication.

### Type Mapping

| Pandera Type | PyIceberg Type |
|-------------|---------------|
| `str` | `StringType()` |
| `int` | `LongType()` |
| `float` | `DoubleType()` |
| `bool` | `BooleanType()` |
| `datetime` | `TimestamptzType()` |
| `date` | `DateType()` |
| `bytes` | `BinaryType()` |
| `Decimal` | `DoubleType()` |

### Metadata Mapping

- `Field(nullable=False)` → `required=True`
- `Field(nullable=True)` → `required=False`
- `Field(description="...")` → `doc="..."`

### DLT Metadata Fields

Auto-injected with special field IDs:
- `_dlt_load_id` (ID 100): DLT load identifier
- `_dlt_id` (ID 101): DLT record identifier
- `_cascade_ingested_at` (ID 102): Cascade ingestion timestamp (if present in schema)

## What the Decorator Handles Automatically

1. **Schema generation**: Auto-generates PyIceberg schema from Pandera
2. **Branch management**: Extracts branch from run tags/config
3. **Table naming**: Generates full table name from namespace
4. **Directory setup**: Creates DLT pipeline directories
5. **Timestamp injection**: Adds `_cascade_ingested_at` to records
6. **Validation**: Runs Pandera schema validation
7. **Staging**: Stages data to parquet via DLT
8. **Iceberg operations**: Creates table and merges with deduplication
9. **Instrumentation**: Timing, logging, and metrics
10. **Result generation**: Creates MaterializeResult with metadata

## Example: Complete Asset in 60 Lines

See `nightscout/glucose.py` for a complete example. The entire asset is ~60 lines including docstring, compared to 270+ lines of boilerplate before.

### Before (270+ lines):
```python
# Manual branch extraction
# Manual table name generation
# Manual DLT pipeline setup
# Manual Pandera validation
# Manual parquet staging
# Manual Iceberg merge
# Manual timing/logging
# Manual result generation
# Duplicate PyIceberg schema definition
```

### After (60 lines):
```python
@cascade_ingestion(
    table_name="glucose_entries",
    unique_key="_id",
    validation_schema=RawGlucoseEntries,  # Single schema definition!
    group="nightscout",
    cron="0 */1 * * *",
)
def glucose_entries(partition_date: str):
    return rest_api({...})  # Just return DLT source
```

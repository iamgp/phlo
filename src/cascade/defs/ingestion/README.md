# Cascade Ingestion Assets

This directory contains data ingestion assets organized by domain. Assets are automatically discovered using the `@cascade_ingestion` decorator.

## Architecture

### Automatic Discovery

Assets are automatically registered when decorated with `@cascade_ingestion`. No manual registration required in `__init__.py`.

```python
from cascade.ingestion import cascade_ingestion

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

### 1. Define Schemas (One-Time Setup)

Create Iceberg and Pandera schemas for your data:

**Iceberg Schema** (`src/cascade/iceberg/schema.py` or inline):
```python
from pyiceberg.schema import Schema
from pyiceberg.types import NestedField, StringType, TimestamptzType

MY_TABLE_SCHEMA = Schema(
    NestedField(1, "id", StringType(), required=False, doc="Unique ID"),
    NestedField(2, "created_at", TimestamptzType(), required=False),
    # ... more fields
)
```

**Pandera Validation Schema** (`src/cascade/schemas/my_domain.py` or inline):
```python
from pandera.pandas import DataFrameModel, Field

class RawMyData(DataFrameModel):
    id: str = Field(nullable=False, unique=True)
    created_at: datetime = Field(nullable=False)
    # ... more fields
```

### 2. Create Asset Module

Create a new file in the appropriate domain directory:

**Using DLT rest_api (Recommended)**:
```python
from dlt.sources.rest_api import rest_api

from cascade.iceberg.schema import MY_TABLE_SCHEMA
from cascade.ingestion import cascade_ingestion
from cascade.schemas.my_domain import RawMyData

@cascade_ingestion(
    table_name="my_table",
    unique_key="id",
    iceberg_schema=MY_TABLE_SCHEMA,
    validation_schema=RawMyData,
    group="my_domain",
    cron="0 */1 * * *",
    freshness_hours=(1, 24),
)
def my_asset(partition_date: str):
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

from cascade.iceberg.schema import MY_TABLE_SCHEMA
from cascade.ingestion import cascade_ingestion
from cascade.schemas.my_domain import RawMyData

@dlt.resource(name="my_resource", write_disposition="replace")
def fetch_my_data(partition_date: str):
    # Custom fetch logic
    data = fetch_from_somewhere(partition_date)
    for record in data:
        yield record

@cascade_ingestion(
    table_name="my_table",
    unique_key="id",
    iceberg_schema=MY_TABLE_SCHEMA,
    validation_schema=RawMyData,
    group="my_domain",
    cron="0 */1 * * *",
    freshness_hours=(1, 24),
)
def my_asset(partition_date: str):
    return fetch_my_data(partition_date)
```

### 3. Add Domain Import (if new domain)

If creating a new domain directory, add it to `src/cascade/defs/ingestion/__init__.py`:

```python
from cascade.defs.ingestion import github  # noqa: F401
from cascade.defs.ingestion import nightscout  # noqa: F401
from cascade.defs.ingestion import my_domain  # noqa: F401  <-- Add this
```

### 4. That's It!

Your asset will be automatically discovered and registered. No need to manually add it to asset lists.

## Decorator Parameters

```python
@cascade_ingestion(
    # Required:
    table_name="my_table",           # Iceberg table name (without namespace)
    unique_key="id",                 # Column for deduplication
    iceberg_schema=MY_SCHEMA,        # PyIceberg Schema
    group="nightscout",              # Dagster asset group name

    # Optional:
    validation_schema=MyValidator,   # Pandera DataFrameModel (optional)
    partition_spec=None,             # Iceberg partition spec (optional)
    cron="0 */1 * * *",             # Cron schedule (optional)
    freshness_hours=(1, 24),        # (warn_hours, fail_hours) (optional)
    max_runtime_seconds=300,        # Maximum runtime before timeout
    max_retries=3,                  # Retry attempts on failure
    retry_delay_seconds=30,         # Delay between retries
    validate=True,                  # Enable Pandera validation
)
```

## What the Decorator Handles Automatically

1. **Branch management**: Extracts branch from run tags/config
2. **Table naming**: Generates full table name from registry
3. **Directory setup**: Creates DLT pipeline directories
4. **Timestamp injection**: Adds `_cascade_ingested_at` to records
5. **Validation**: Runs Pandera schema validation
6. **Staging**: Stages data to parquet via DLT
7. **Iceberg operations**: Creates table and merges with deduplication
8. **Instrumentation**: Timing, logging, and metrics
9. **Result generation**: Creates MaterializeResult with metadata

## Example: Complete Asset in 60 Lines

See `nightscout/glucose.py` for a complete example. The entire asset is ~60 lines including docstring, compared to 270+ lines of boilerplate before.

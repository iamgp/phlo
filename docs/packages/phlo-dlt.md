# phlo-dlt

DLT (Data Load Tool) ingestion engine for Phlo.

## Overview

`phlo-dlt` provides the `@phlo_ingestion` decorator for defining data ingestion pipelines using DLT. It automatically materializes data into Iceberg tables with schema evolution and full lineage tracking.

## Installation

```bash
pip install phlo-dlt
# or
phlo plugin install dlt
```

## Configuration

| Variable                 | Default               | Description                |
| ------------------------ | --------------------- | -------------------------- |
| `ICEBERG_WAREHOUSE_PATH` | `s3://lake/warehouse` | Iceberg warehouse S3 path  |
| `ICEBERG_STAGING_PATH`   | `s3://lake/stage`     | Staging path for ingestion |
| `NESSIE_HOST`            | `nessie`              | Nessie catalog host        |
| `NESSIE_PORT`            | `19120`               | Nessie catalog port        |

## Features

### Auto-Configuration

| Feature                | How It Works                                                         |
| ---------------------- | -------------------------------------------------------------------- |
| **Asset Registration** | Ingestion assets published as capability specs via asset provider entry points |
| **Lineage Events**     | Emits `ingestion.start`, `ingestion.end` events for lineage tracking |
| **Schema Evolution**   | Automatically handles schema changes during ingestion                |
| **Hook Integration**   | Events captured by alerting, metrics, and OpenMetadata plugins       |

### Event Flow

```
@phlo_ingestion → IngestionEventEmitter → HookBus → [Alerting, Metrics, Lineage plugins]
```

## Usage

### Basic Ingestion

```python
from phlo import phlo_ingestion
from workflows.schemas.events import EventSchema

@phlo_ingestion(
    table_name="events",
    unique_key="id",
    validation_schema=EventSchema,
    group="api",
    cron="0 */1 * * *",
    freshness_hours=(1, 24),
)
def api_events(partition_date: str):
    """Ingest events from REST API."""
    from dlt.sources.rest_api import rest_api

    return rest_api({
        "client": {"base_url": "https://api.example.com"},
        "resources": [{"name": "events", "endpoint": "/events"}]
    })
```

### Decorator Options

| Option              | Type              | Description                       |
| ------------------- | ----------------- | --------------------------------- |
| `table_name`        | `str`             | Target Iceberg table name         |
| `unique_key`        | `str`             | Column for deduplication          |
| `validation_schema` | `DataFrameModel`  | Pandera schema for validation     |
| `group`             | `str`             | Asset group name                  |
| `cron`              | `str`             | Schedule expression               |
| `freshness_hours`   | `tuple[int, int]` | (warn, fail) freshness thresholds |
| `merge_strategy`    | `str`             | `merge` (default) or `append`     |
| `merge_config`      | `dict`            | Advanced merge configuration      |

### Merge Strategies

```python
# Default merge with deduplication
@phlo_ingestion(
    table_name="events",
    unique_key="id",
    merge_strategy="merge",
    merge_config={"deduplication_method": "last"}  # or "first", "hash"
)

# Append-only (no deduplication)
@phlo_ingestion(
    table_name="events",
    merge_strategy="append"
)
```

### Running Ingestion

```bash
# Via Phlo CLI
phlo materialize dlt_api_events

# Via Phlo CLI
phlo materialize api_events --partition 2025-01-15
```

## Data Flow

```
External API
     ↓
DLT Pipeline (extract + normalize)
     ↓
Parquet Staging (S3)
     ↓
Pandera Validation
     ↓
PyIceberg Merge
     ↓
Iceberg Table (on Nessie branch)
```

## Entry Points

| Entry Point            | Plugin                                  |
| ---------------------- | --------------------------------------- |
| `phlo.plugins.assets`  | `DltAssetProvider` for ingestion specs |

## Related Packages

- [phlo-dagster](phlo-dagster.md) - Dagster adapter for capability specs
- [phlo-iceberg](phlo-iceberg.md) - Iceberg table format
- [phlo-quality](phlo-quality.md) - Data validation
- [phlo-nessie](phlo-nessie.md) - Branch management

## Next Steps

- [Developer Guide](../guides/developer-guide.md) - Master decorators
- [Workflow Development](../guides/workflow-development.md) - Build pipelines
- [Core Concepts](../getting-started/core-concepts.md) - Understand patterns

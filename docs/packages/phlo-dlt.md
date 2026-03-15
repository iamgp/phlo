# phlo-dlt

DLT (Data Load Tool) ingestion engine for Phlo.

## Overview

`phlo-dlt` provides the `@phlo_ingestion` decorator for defining data ingestion pipelines using DLT. It materializes data into the active `table_store` with schema evolution and full lineage tracking.

When multiple `table_store` providers are installed, selection is deterministic:

- workflow/runtime tag via `phlo/capability/table_store=...`
- asset override via `capabilities={"table_store": "..."}`
- global default via `phlo.yaml` `capabilities.defaults` or `PHLO_DEFAULT_CAPABILITIES`

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
from phlo import Consumer, SLA
from phlo.ingestion import phlo_ingestion
from workflows.schemas.events import EventSchema

@phlo_ingestion(
    table_name="events",
    unique_key="id",
    validation_schema=EventSchema,
    group="api",
    cron="0 */1 * * *",
    freshness_hours=(1, 24),
    owner="platform-ingestion",
    consumers=[
        Consumer(name="analytics", usage="daily_reporting"),
        "fraud_team",
    ],
    sla=SLA(freshness_hours=2, quality_threshold=0.99),
)
def api_events(partition_date: str):
    """Ingest events from REST API."""
    from dlt.sources.rest_api import rest_api

    return rest_api(
        client={"base_url": "https://api.example.com"},
        resources=[{"name": "events", "endpoint": {"path": "events"}}],
    )
```

### Decorator Options

| Option              | Type              | Description                                         |
| ------------------- | ----------------- | --------------------------------------------------- |
| `table_name`        | `str`             | Target table-store table name                       |
| `unique_key`        | `str`             | Column for deduplication                            |
| `validation_schema` | `DataFrameModel`  | Pandera schema for validation                       |
| `table_schema`      | `Any`             | Explicit table-store schema (optional)              |
| `group`             | `str`             | Asset group name                                    |
| `cron`              | `str`             | Schedule expression                                 |
| `freshness_hours`   | `tuple[int, int]` | (warn, fail) freshness thresholds                   |
| `merge_strategy`    | `str`             | `merge` (default) or `append`                       |
| `merge_config`      | `dict`            | Advanced merge configuration                        |
| `owner`             | `str`             | Optional owner/team metadata for contracts          |
| `consumers`         | `list[Consumer \| str]` | Optional downstream consumer metadata         |
| `sla`               | `SLA`             | Optional freshness/quality contract metadata        |
| `capabilities`      | `dict[str, str]`  | Optional capability provider overrides for the asset |

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

When `table_schema` is omitted, the active `table_store` provider must implement
schema derivation from `validation_schema` (for example Iceberg provider conversion).

### Selecting a Table Store

```python
@phlo_ingestion(
    table_name="events",
    unique_key="id",
    validation_schema=EventSchema,
    group="api",
    capabilities={"table_store": "delta"},
)
def api_events(partition_date: str):
    ...
```

For workflow-wide selection, set the Dagster run tag
`phlo/capability/table_store=<provider>`.

### Running Ingestion

```bash
# Via Phlo CLI
phlo materialize dlt_api_events

# Via Phlo CLI
phlo materialize dlt_api_events --partition 2025-01-15
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
Table Store Merge
     ↓
Physical Table (for active store)
```

## Entry Points

| Entry Point            | Plugin                                  |
| ---------------------- | --------------------------------------- |
| `phlo.plugins.assets`  | `DltAssetProvider` for ingestion specs |

## Related Packages

- [phlo-dagster](phlo-dagster.md) - Dagster adapter for capability specs
- [phlo-iceberg](phlo-iceberg.md) - Iceberg table format
- [phlo-pandera](phlo-pandera.md) - Data validation
- [phlo-nessie](phlo-nessie.md) - Branch management

## Next Steps

- [Developer Guide](../guides/developer-guide.md) - Master decorators
- [Workflow Development](../guides/workflow-development.md) - Build pipelines
- [Core Concepts](../getting-started/core-concepts.md) - Understand patterns

# phlo-dlt

DLT (Data Load Tool) ingestion engine for Phlo.

## Description

Provides the `@phlo_ingestion` decorator for defining data ingestion pipelines using DLT. Automatically materializes data into Iceberg tables with schema evolution and lineage tracking.

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

## Auto-Configuration

This package is **fully auto-configured**:

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

### Defining Ingestion

```python
from phlo import phlo_ingestion

@phlo_ingestion(
    name="github_events",
    source="rest_api",
    destination="bronze.github_events"
)
def ingest_github_events():
    return {
        "client": {"base_url": "https://api.github.com"},
        "resources": ["events"]
    }
```

### Running Ingestion

Ingestion assets are automatically discovered and can be materialized via the active orchestrator:

```bash
phlo materialize dlt_github_events
```

## Entry Points

- `phlo.plugins.assets` - Provides `DltAssetProvider` for ingestion asset specs

# phlo-delta

Delta Lake table-store integration for Phlo.

## Overview

`phlo-delta` provides Delta Lake table-store resources using the `deltalake` (delta-rs) Python library. It enables ACID transactions, schema evolution, and time travel on the data lakehouse.

> **Alternative Table Store**: Delta Lake is an alternative table-store to [Apache Iceberg](phlo-iceberg.md). Choose the format that best fits your ecosystem — both integrate with Phlo's storage and query layers.

## Installation

```bash
pip install phlo-delta
# or
phlo plugin install delta
```

## Configuration

| Variable                       | Required | Default                     | Description                    |
| ------------------------------ | -------- | --------------------------- | ------------------------------ |
| `DELTA_WAREHOUSE_PATH`         | Yes      | `s3://lake/warehouse/delta` | S3 path for Delta tables       |
| `DELTA_STAGING_PATH`           | No       | `s3://lake/stage`           | S3 path for staging            |
| `DELTA_DEFAULT_NAMESPACE`      | No       | `raw`                       | Default namespace/schema       |
| `DELTA_S3_ENDPOINT`            | No       | `http://localhost:9000`     | S3 endpoint URL for Delta I/O  |
| `DELTA_S3_ACCESS_KEY`          | No       | `minio`                     | S3 access key                  |
| `DELTA_S3_SECRET_KEY`          | No       | `minio123`                  | S3 secret key                  |
| `DELTA_S3_REGION`              | No       | `us-east-1`                 | S3 region                      |
| `DELTA_S3_ALLOW_UNSAFE_RENAME` | No       | `true`                      | Allow unsafe rename for S3     |

> **S3 Access**: Configure AWS credentials via `~/.aws/credentials` or `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` env vars. When using MinIO, these are set automatically.

## Features

### Auto-Configuration

Works out-of-the-box when MinIO is running:

| Feature                  | How It Works                                               |
| ------------------------ | ---------------------------------------------------------- |
| **Resource Provider**    | `DeltaResource` published as runtime resource `table_store`|
| **Table Store Capability** | Registers `table_store:delta` capability                 |
| **Schema Migration**     | Registers `schema_migrator:delta` capability               |

## Usage

### Resource Usage

```python
from phlo_delta.resource import DeltaResource

delta = DeltaResource()
dt = delta.get_table("bronze.users")
df = dt.to_pandas()
```

### Helper Utilities

`phlo-delta` includes lightweight helpers for table inspection and maintenance planning:

```python
from phlo_delta import identity_partition, maintenance_recommendations, table_exists

if table_exists("bronze.users"):
    recommendations = maintenance_recommendations({"file_count": 1200, "total_size_mb": 2048})

partition_columns = identity_partition("event_date")
```

| Helper | Purpose |
| --- | --- |
| `table_exists` | Check whether a Delta table can be opened. |
| `load_table_schema` | Load the Delta schema as a PyArrow schema. |
| `identity_partition` | Build Delta partition column lists. |
| `maintenance_recommendations` | Recommend vacuum or optimize review from table stats. |

### Direct Usage

```python
from phlo_delta.settings import get_settings

opts = get_settings().get_storage_options()
# Use opts with deltalake
```

## Entry Points

| Entry Point              | Plugin                  |
| ------------------------ | ----------------------- |
| `phlo.plugins.resources` | `DeltaResourceProvider` |

## Related Packages

- [phlo-iceberg](phlo-iceberg.md) - Apache Iceberg table store
- [phlo-minio](phlo-minio.md) - Object storage
- [phlo-trino](phlo-trino.md) - Query engine
- [phlo-dlt](phlo-dlt.md) - Data ingestion

## Next Steps

- [Architecture Reference](../reference/architecture.md) - System design
- [Core Concepts](../getting-started/core-concepts.md) - Understand patterns
- [Integration Profiles](../guides/integration-profiles.md) - Profile configuration

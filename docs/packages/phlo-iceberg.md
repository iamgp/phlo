# phlo-iceberg

Apache Iceberg catalog integration for Phlo.

## Overview

`phlo-iceberg` provides PyIceberg resources for adapters and table-store/schema-migration capabilities. It enables ACID transactions, schema evolution, and time travel on the data lakehouse.

## Installation

```bash
pip install phlo-iceberg
# or
phlo plugin install iceberg
```

## Configuration

| Variable                    | Required | Default               | Description                   |
| --------------------------- | -------- | --------------------- | ----------------------------- |
| `ICEBERG_WAREHOUSE_PATH`    | Yes      | `s3://lake/warehouse` | S3 path for Iceberg warehouse |
| `ICEBERG_STAGING_PATH`      | No       | `s3://lake/stage`     | S3 path for staging           |
| `ICEBERG_DEFAULT_NAMESPACE` | No       | `raw`                 | Default namespace/schema      |
| `ICEBERG_DEFAULT_REF`       | No       | `main`                | Default catalog ref/branch    |
| `ICEBERG_CATALOG_URI`       | No       | `http://nessie:19120/iceberg` | Iceberg REST catalog URI |

> **S3 Access**: Configure AWS credentials via `~/.aws/credentials` or `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` env vars. When using MinIO, these are set automatically.

## Features

### Auto-Configuration

Works out-of-the-box when MinIO and Nessie are running:

| Feature                | How It Works                                                                     |
| ---------------------- | -------------------------------------------------------------------------------- |
| **Resource Provider**  | `IcebergResource` published via capability specs                                 |
| **Catalog Generation** | Trino catalog `.properties` files can be generated from catalog plugins owned by `phlo-nessie` |

## Usage

### Resource Usage

```python
from phlo_iceberg import IcebergResource

iceberg = IcebergResource()
catalog = iceberg.get_catalog()
table = catalog.load_table("bronze.users")
df = table.scan().to_pandas()
```

### Direct Usage

```python
from phlo_iceberg.settings import get_settings

# Get PyIceberg catalog configuration
config = get_settings().get_pyiceberg_catalog_config("main")

# Use with PyIceberg
from pyiceberg.catalog import load_catalog
catalog = load_catalog("iceberg_main", **config)
```

### Time Travel

```python
# Query specific snapshot
table = catalog.load_table("bronze.users")
snapshots = table.snapshots()

# Read from specific snapshot
df = table.scan().using(snapshot_id=snapshot_id).to_pandas()
```

### Branch-Aware Operations

```python
# Load catalog for specific branch
config = get_settings().get_pyiceberg_catalog_config("dev")
catalog = load_catalog("iceberg_dev", **config)

# All operations now target the 'dev' branch
table = catalog.load_table("bronze.users")
```

## Trino Integration

Once running, query Iceberg tables via Trino:

```sql
-- Query from main branch
SELECT * FROM iceberg.bronze.users LIMIT 10;

-- Query from dev branch (using iceberg_dev catalog)
SELECT * FROM iceberg_dev.bronze.users LIMIT 10;

-- Time travel
SELECT * FROM iceberg.bronze.users FOR VERSION AS OF 123456789;
```

## Entry Points

| Entry Point                   | Plugin                               |
| ----------------------------- | ------------------------------------ |
| `phlo.resource_providers`     | `IcebergResourceProvider`            |

## Related Packages

- [phlo-nessie](phlo-nessie.md) - Git-like catalog
- [phlo-trino](phlo-trino.md) - Query engine
- [phlo-minio](phlo-minio.md) - Object storage
- [phlo-dlt](phlo-dlt.md) - Data ingestion

## Next Steps

- [Architecture Reference](../reference/architecture.md) - System design
- [DuckDB Queries](../reference/duckdb-queries.md) - Ad-hoc analysis
- [Core Concepts](../getting-started/core-concepts.md) - Understand patterns

# phlo-iceberg

Apache Iceberg catalog integration for Phlo.

## Overview

`phlo-iceberg` provides PyIceberg resources for Dagster and Trino catalog configuration. It enables ACID transactions, schema evolution, and time travel on the data lakehouse.

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
| `ICEBERG_NESSIE_REF`        | No       | `main`                | Default Nessie branch/tag     |
| `NESSIE_HOST`               | No       | `nessie`              | Nessie catalog host           |
| `NESSIE_PORT`               | No       | `19120`               | Nessie REST API port          |

> **S3 Access**: Configure AWS credentials via `~/.aws/credentials` or `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` env vars. When using MinIO, these are set automatically.

## Features

### Auto-Configuration

Works out-of-the-box when MinIO and Nessie are running:

| Feature                | How It Works                                                                     |
| ---------------------- | -------------------------------------------------------------------------------- |
| **Dagster Resource**   | `IcebergResource` auto-registered via entry points                               |
| **Trino Catalogs**     | Registers `iceberg` and `iceberg_dev` catalogs via `phlo.plugins.trino_catalogs` |
| **Catalog Generation** | Catalog `.properties` files auto-generated at Trino startup                      |

### Trino Catalog Entry Points

```toml
[project.entry-points."phlo.plugins.trino_catalogs"]
iceberg = "phlo_iceberg.catalog_plugin:IcebergCatalogPlugin"
iceberg_dev = "phlo_iceberg.catalog_plugin:IcebergDevCatalogPlugin"
```

## Usage

### Dagster Resource

```python
from dagster import asset
from phlo_iceberg.resource import IcebergResource

@asset
def my_asset(iceberg: IcebergResource):
    catalog = iceberg.load_catalog()
    table = catalog.load_table("bronze.users")
    return table.scan().to_pandas()
```

### Direct Usage

```python
from phlo.config import get_settings

# Get PyIceberg catalog configuration
config = get_settings().get_pyiceberg_catalog_config("main")

# Use with PyIceberg
from pyiceberg.catalog import load_catalog
catalog = load_catalog("nessie", **config)
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
catalog = load_catalog("nessie", **config)

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

| Entry Point                   | Plugin                                        |
| ----------------------------- | --------------------------------------------- |
| `phlo.plugins.dagster`        | `IcebergDagsterPlugin` with `IcebergResource` |
| `phlo.plugins.trino_catalogs` | Iceberg catalog configurations                |

## Related Packages

- [phlo-nessie](phlo-nessie.md) - Git-like catalog
- [phlo-trino](phlo-trino.md) - Query engine
- [phlo-minio](phlo-minio.md) - Object storage
- [phlo-dlt](phlo-dlt.md) - Data ingestion

## Next Steps

- [Architecture Reference](../reference/architecture.md) - System design
- [DuckDB Queries](../reference/duckdb-queries.md) - Ad-hoc analysis
- [Core Concepts](../getting-started/core-concepts.md) - Understand patterns

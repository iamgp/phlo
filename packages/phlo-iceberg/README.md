# phlo-iceberg

Apache Iceberg catalog integration for Phlo.

## Description

Provides PyIceberg resources for Dagster and Trino catalog configuration. Enables ACID transactions, schema evolution, and time travel on the data lakehouse.

## Installation

```bash
pip install phlo-iceberg
# or
phlo plugin install iceberg
```

## Configuration

| Variable                    | Default               | Description                   |
| --------------------------- | --------------------- | ----------------------------- |
| `ICEBERG_WAREHOUSE_PATH`    | `s3://lake/warehouse` | S3 path for Iceberg warehouse |
| `ICEBERG_STAGING_PATH`      | `s3://lake/stage`     | S3 path for staging           |
| `ICEBERG_DEFAULT_NAMESPACE` | `raw`                 | Default namespace/schema      |
| `ICEBERG_NESSIE_REF`        | `main`                | Default Nessie branch/tag     |
| `NESSIE_HOST`               | `nessie`              | Nessie catalog host           |
| `NESSIE_PORT`               | `19120`               | Nessie REST API port          |

## Auto-Configuration

This package is **fully auto-configured**:

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

config = get_settings().get_pyiceberg_catalog_config("main")
# Use config with pyiceberg
```

## Entry Points

- `phlo.plugins.dagster` - Provides `IcebergDagsterPlugin` with `IcebergResource`
- `phlo.plugins.trino_catalogs` - Provides Iceberg catalog configurations

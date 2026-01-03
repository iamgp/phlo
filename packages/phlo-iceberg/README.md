# phlo-iceberg

Apache Iceberg catalog integration for Phlo.

## Description

Provides PyIceberg resources for adapters and Trino catalog configuration. Enables ACID transactions, schema evolution, and time travel on the data lakehouse.

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

## Auto-Configuration

Works out-of-the-box when MinIO and Nessie are running:

| Feature                | How It Works                                                                     |
| ---------------------- | -------------------------------------------------------------------------------- |
| **Resource Provider**  | `IcebergResource` published via capability specs                                 |
| **Trino Catalogs**     | Registers `iceberg` and `iceberg_dev` catalogs via `phlo.plugins.trino_catalogs` |
| **Catalog Generation** | Catalog `.properties` files auto-generated at Trino startup                      |

### Trino Catalog Entry Points

```toml
[project.entry-points."phlo.plugins.trino_catalogs"]
iceberg = "phlo_iceberg.catalog_plugin:IcebergCatalogPlugin"
iceberg_dev = "phlo_iceberg.catalog_plugin:IcebergDevCatalogPlugin"
```

## Usage

### Resource Usage

```python
from phlo_iceberg.resource import IcebergResource

iceberg = IcebergResource()
catalog = iceberg.get_catalog()
table = catalog.load_table("bronze.users")
df = table.scan().to_pandas()
```

### Direct Usage

```python
from phlo.config import get_settings

config = get_settings().get_pyiceberg_catalog_config("main")
# Use config with pyiceberg
```

## Entry Points

- `phlo.plugins.resources` - Provides `IcebergResourceProvider`
- `phlo.plugins.trino_catalogs` - Provides Iceberg catalog configurations

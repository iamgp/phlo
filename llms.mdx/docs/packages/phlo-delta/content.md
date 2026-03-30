# phlo-delta (/docs/packages/phlo-delta)



Overview [#overview]

`phlo-delta` provides Delta Lake table-store resources using the `deltalake` (delta-rs) Python library. It enables ACID transactions, schema evolution, and time travel on the data lakehouse.

> **Alternative Table Store**: Delta Lake is an alternative table-store to [Apache Iceberg](phlo-iceberg.md). Choose the format that best fits your ecosystem — both integrate with Phlo's storage and query layers.

Installation [#installation]

```bash
pip install phlo-delta
# or
phlo plugin install delta
```

Configuration [#configuration]

| Variable                       | Required | Default                     | Description                   |
| ------------------------------ | -------- | --------------------------- | ----------------------------- |
| `DELTA_WAREHOUSE_PATH`         | Yes      | `s3://lake/warehouse/delta` | S3 path for Delta tables      |
| `DELTA_STAGING_PATH`           | No       | `s3://lake/stage`           | S3 path for staging           |
| `DELTA_DEFAULT_NAMESPACE`      | No       | `raw`                       | Default namespace/schema      |
| `DELTA_S3_ENDPOINT`            | No       | `http://localhost:9000`     | S3 endpoint URL for Delta I/O |
| `DELTA_S3_ACCESS_KEY`          | No       | `minio`                     | S3 access key                 |
| `DELTA_S3_SECRET_KEY`          | No       | `minio123`                  | S3 secret key                 |
| `DELTA_S3_REGION`              | No       | `us-east-1`                 | S3 region                     |
| `DELTA_S3_ALLOW_UNSAFE_RENAME` | No       | `true`                      | Allow unsafe rename for S3    |

> **S3 Access**: Configure AWS credentials via `~/.aws/credentials` or `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` env vars. When using MinIO, these are set automatically.

Features [#features]

Auto-Configuration [#auto-configuration]

Works out-of-the-box when MinIO is running:

| Feature                    | How It Works                                                |
| -------------------------- | ----------------------------------------------------------- |
| **Resource Provider**      | `DeltaResource` published as runtime resource `table_store` |
| **Table Store Capability** | Registers `table_store:delta` capability                    |
| **Schema Migration**       | Registers `schema_migrator:delta` capability                |

Usage [#usage]

Resource Usage [#resource-usage]

```python
from phlo_delta.resource import DeltaResource

delta = DeltaResource()
dt = delta.get_table("bronze.users")
df = dt.to_pandas()
```

Direct Usage [#direct-usage]

```python
from phlo_delta.settings import get_settings

opts = get_settings().get_storage_options()
# Use opts with deltalake
```

Entry Points [#entry-points]

| Entry Point              | Plugin                  |
| ------------------------ | ----------------------- |
| `phlo.plugins.resources` | `DeltaResourceProvider` |

Related Packages [#related-packages]

* [phlo-iceberg](phlo-iceberg.md) - Apache Iceberg table store
* [phlo-minio](phlo-minio.md) - Object storage
* [phlo-trino](phlo-trino.md) - Query engine
* [phlo-dlt](phlo-dlt.md) - Data ingestion

Next Steps [#next-steps]

* [Architecture Reference](../reference/architecture.md) - System design
* [Core Concepts](../getting-started/core-concepts.md) - Understand patterns
* [Integration Profiles](../reference/integration-profiles.md) - Profile configuration

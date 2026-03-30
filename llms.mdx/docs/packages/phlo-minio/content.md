# phlo-minio (/docs/packages/phlo-minio)



Overview [#overview]

`phlo-minio` provides S3-compatible object storage for the data lake. It stores Iceberg table data, staging files, and backups.

Installation [#installation]

```bash
pip install phlo-minio
# or
phlo plugin install minio
```

Configuration [#configuration]

| Variable                | Default    | Description              |
| ----------------------- | ---------- | ------------------------ |
| `MINIO_ROOT_USER`       | `minio`    | Root username            |
| `MINIO_ROOT_PASSWORD`   | `minio123` | Root password            |
| `MINIO_API_PORT`        | `10001`    | S3 API port              |
| `MINIO_CONSOLE_PORT`    | `10002`    | Web console port         |
| `MINIO_SERVER_URL`      | -          | TLS server URL           |
| `MINIO_OIDC_CONFIG_URL` | -          | OIDC provider config URL |
| `MINIO_AUTO_ENCRYPTION` | `off`      | Auto-encryption mode     |
| `MINIO_AUDIT_ENABLED`   | `off`      | Audit logging            |

Features [#features]

Auto-Configuration [#auto-configuration]

| Feature                 | How It Works                                         |
| ----------------------- | ---------------------------------------------------- |
| **Metrics Labels**      | Exposes MinIO metrics at `/minio/v2/metrics/cluster` |
| **Prometheus Scraping** | Auto-scraped by Prometheus via Docker labels         |
| **Volume Mounting**     | Persists data to `./volumes/minio`                   |

Default Buckets [#default-buckets]

| Bucket           | Purpose                |
| ---------------- | ---------------------- |
| `lake`           | Main data lake storage |
| `lake/warehouse` | Iceberg table data     |
| `lake/stage`     | Ingestion staging area |

Usage [#usage]

Starting the Service [#starting-the-service]

```bash
phlo services start --service minio
```

Web Console [#web-console]

Access the MinIO console at `http://localhost:10002`:

* Username: `minio` (or `MINIO_ROOT_USER`)
* Password: `minio123` (or `MINIO_ROOT_PASSWORD`)

AWS CLI [#aws-cli]

```bash
# Run MinIO client inside the service
phlo minio ls local/
phlo minio ls --recursive local/warehouse/
phlo minio admin info --json local/

# Pass through to raw mc commands
phlo minio cp local/data.parquet local/lake/stage/data.parquet
```

Python (boto3) [#python-boto3]

```python
import boto3

s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:10001',
    aws_access_key_id='minio',
    aws_secret_access_key='minio123'
)

# List objects
response = s3.list_objects_v2(Bucket='lake', Prefix='warehouse/')
for obj in response.get('Contents', []):
    print(obj['Key'])
```

Endpoints [#endpoints]

| Endpoint    | URL                                               |
| ----------- | ------------------------------------------------- |
| **S3 API**  | `http://localhost:10001`                          |
| **Console** | `http://localhost:10002`                          |
| **Metrics** | `http://localhost:10001/minio/v2/metrics/cluster` |

Metrics Integration [#metrics-integration]

MinIO metrics are automatically scraped by Prometheus:

```yaml
compose:
  labels:
    phlo.metrics.enabled: "true"
    phlo.metrics.port: "minio:10001"
    phlo.metrics.path: "/minio/v2/metrics/cluster"
```

Entry Points [#entry-points]

| Entry Point                       | Plugin                                          |
| --------------------------------- | ----------------------------------------------- |
| `phlo.plugins.services`           | `MinioServicePlugin`, `MinioSetupServicePlugin` |
| `phlo.plugins.resource_providers` | `MinioResourceProvider`                         |

Related Packages [#related-packages]

* [phlo-iceberg](phlo-iceberg.md) - Table format
* [phlo-nessie](phlo-nessie.md) - Catalog service
* [phlo-prometheus](phlo-prometheus.md) - Metrics collection

Next Steps [#next-steps]

* [Installation Guide](../getting-started/installation.md) - Complete setup
* [Architecture Reference](../reference/architecture.md) - System design
* [Operations Guide](../operations/operations-guide.md) - Backup and maintenance

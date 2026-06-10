# phlo-minio

MinIO S3-compatible object storage for Phlo.

## Overview

`phlo-minio` provides S3-compatible object storage for the data lake. It stores Iceberg table data, staging files, and backups.

## Installation

```bash
pip install phlo-minio
# or
phlo plugin install minio
```

## Configuration

| Variable                | Default    | Description              |
| ----------------------- | ---------- | ------------------------ |
| `MINIO_ROOT_USER`       | `minio`    | Root username            |
| `MINIO_ROOT_PASSWORD`   | `minio123` | Root password            |
| `MINIO_API_PORT`        | `10001`    | S3 API host port in generated projects |
| `MINIO_CONSOLE_PORT`    | `10002`    | Web console host port in generated projects |
| `MINIO_SERVER_URL`      | -          | TLS server URL           |
| `MINIO_OIDC_CONFIG_URL` | -          | OIDC provider config URL |
| `MINIO_AUTO_ENCRYPTION` | `off`      | Auto-encryption mode     |
| `MINIO_AUDIT_ENABLED`   | `off`      | Audit webhook delivery   |

## Features

### Auto-Configuration

| Feature                 | How It Works                                         |
| ----------------------- | ---------------------------------------------------- |
| **Metrics Labels**      | Exposes MinIO metrics at `/minio/v2/metrics/cluster` |
| **Prometheus Scraping** | Auto-scraped by Prometheus via Docker labels         |
| **Volume Mounting**     | Persists data to `./volumes/minio`                   |

### Default Buckets

| Bucket           | Purpose                |
| ---------------- | ---------------------- |
| `lake`           | Main data lake storage |
| `lake/warehouse` | Iceberg table data     |
| `lake/stage`     | Ingestion staging area |

## Usage

### Starting the Service

```bash
phlo services start --service minio
```

### Web Console

Access the MinIO console at `http://localhost:10002`:

- Username: `minio` (or `MINIO_ROOT_USER`)
- Password: `minio123` (or `MINIO_ROOT_PASSWORD`)

### AWS CLI

```bash
# Run MinIO client inside the service
phlo minio ls local/
phlo minio ls --recursive local/warehouse/
phlo minio admin info --json local/

# Pass through to raw mc commands
phlo minio cp local/data.parquet local/lake/stage/data.parquet
```

### Python (boto3)

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

## Endpoints

| Endpoint    | URL                                               |
| ----------- | ------------------------------------------------- |
| **S3 API**  | `http://localhost:10001`                          |
| **Console** | `http://localhost:10002`                          |
| **Metrics** | `http://localhost:10001/minio/v2/metrics/cluster` |

## Metrics Integration

MinIO metrics are automatically scraped by Prometheus:

```yaml
compose:
  labels:
    phlo.metrics.enabled: "true"
    phlo.metrics.port: "minio:9000"
    phlo.metrics.path: "/minio/v2/metrics/cluster"
```

## Audit Logging

`phlo-minio` is the Phlo-owned audit-log integration point for storage access events.

```bash
MINIO_AUDIT_ENABLED=on
MINIO_AUDIT_ENDPOINT=http://loki:3100/loki/api/v1/push
```

Keep MinIO audit logs in a durable backend. Do not treat container-local logs as the only audit record for production environments.

## Entry Points

| Entry Point                     | Plugin                                  |
| ------------------------------- | --------------------------------------- |
| `phlo.plugins.services`         | `MinioServicePlugin`, `MinioSetupServicePlugin` |
| `phlo.plugins.resource_providers` | `MinioResourceProvider`                |

## Related Packages

- [phlo-iceberg](phlo-iceberg.md) - Table format
- [phlo-nessie](phlo-nessie.md) - Catalog service
- [phlo-prometheus](phlo-prometheus.md) - Metrics collection
- [Audit Logging](../operations/audit-logging.md) - Production audit-log posture

## Next Steps

- [Installation Guide](../getting-started/installation.md) - Complete setup
- [Architecture Reference](../reference/architecture.md) - System design
- [Operations Guide](../operations/operations-guide.md) - Backup and maintenance

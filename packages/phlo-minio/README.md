# phlo-minio

MinIO S3-compatible object storage plugin for Phlo.

## Description

Provides S3-compatible object storage for the data lake. Stores Iceberg table data, staging files, and backups.

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
| `MINIO_API_PORT`        | `9000`     | S3 API port              |
| `MINIO_CONSOLE_PORT`    | `9001`     | Web console port         |
| `MINIO_SERVER_URL`      | -          | TLS server URL           |
| `MINIO_OIDC_CONFIG_URL` | -          | OIDC provider config URL |
| `MINIO_AUTO_ENCRYPTION` | `off`      | Auto-encryption mode     |
| `MINIO_AUDIT_ENABLED`   | `off`      | Audit logging            |

## Auto-Configuration

This package is **fully auto-configured**:

| Feature                 | How It Works                                         |
| ----------------------- | ---------------------------------------------------- |
| **Metrics Labels**      | Exposes MinIO metrics at `/minio/v2/metrics/cluster` |
| **Prometheus Scraping** | Auto-scraped by Prometheus via Docker labels         |
| **Volume Mounting**     | Persists data to `./volumes/minio`                   |

### Metrics Labels

```yaml
compose:
  labels:
    phlo.metrics.enabled: "true"
    phlo.metrics.port: "minio:9000"
    phlo.metrics.path: "/minio/v2/metrics/cluster"
```

## Usage

```bash
phlo services start --service minio
```

## Endpoints

- **S3 API**: `http://localhost:9000`
- **Console**: `http://localhost:9001`

## Entry Points

- `phlo.plugins.services` - Provides `MinioServicePlugin`

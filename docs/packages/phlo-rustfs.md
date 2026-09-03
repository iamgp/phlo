# phlo-rustfs

RustFS S3-compatible object storage for Phlo.

## Overview

`phlo-rustfs` provides S3-compatible object storage for the data lake using [RustFS](https://github.com/rustfs/rustfs), an Apache 2.0 licensed, Rust-built, 100% S3-compatible object storage server. It stores Iceberg table data, staging files, and backups.

## Installation

```bash
pip install phlo-rustfs
# or
phlo plugin install rustfs
```

## Configuration

| Variable                              | Default       | Description                  |
| ------------------------------------- | ------------- | ---------------------------- |
| `RUSTFS_HOST`                        | `rustfs`      | RustFS service hostname      |
| `RUSTFS_ACCESS_KEY`                   | `rustfsadmin` | Access key (username)        |
| `RUSTFS_SECRET_KEY`                   | `rustfsadmin` | Secret key (password)        |
| `RUSTFS_API_PORT`                     | `9000`        | S3 API port                 |
| `RUSTFS_CONSOLE_PORT`                 | `9001`        | Web console port            |
| `S3_REGION`                          | `us-east-1`   | S3 region identifier         |

## Features

### Default Layout

| Bucket / Prefix  | Purpose                |
| ---------------- | ---------------------- |
| `lake`           | Main data lake storage |
| `lake/warehouse` | Iceberg table data     |
| `lake/stage`     | Ingestion staging area |

## Usage

### Starting the Service

```bash
phlo services start --service rustfs
```

This targeted start now bootstraps the writable `./volumes/rustfs` bind mount and initializes the
default `lake`, `lake/warehouse`, and `lake/stage` layout automatically.

### Web Console

Access the RustFS console at `http://localhost:9001`:

- Username: `rustfsadmin` (or `RUSTFS_ACCESS_KEY`)
- Password: `rustfsadmin` (or `RUSTFS_SECRET_KEY`)

### AWS CLI

```bash
# Configure AWS CLI for RustFS
aws configure set aws_access_key_id rustfsadmin
aws configure set aws_secret_access_key rustfsadmin

# List buckets
aws --endpoint-url http://localhost:9000 s3 ls

# List warehouse contents
aws --endpoint-url http://localhost:9000 s3 ls s3://lake/warehouse/

# Copy file to staging
aws --endpoint-url http://localhost:9000 s3 cp data.parquet s3://lake/stage/
```

### Python (boto3)

```python
import boto3

s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='rustfsadmin',
    aws_secret_access_key='rustfsadmin'
)

# List objects
response = s3.list_objects_v2(Bucket='lake', Prefix='warehouse/')
for obj in response.get('Contents', []):
    print(obj['Key'])
```

## Endpoints

| Endpoint    | URL                        |
| ----------- | -------------------------- |
| **S3 API**  | `http://localhost:9000`   |
| **Console** | `http://localhost:9001`   |

## Migration from MinIO

If you're switching from MinIO to RustFS:

1. Update environment variables:

```bash
# Before (MinIO)
AWS_S3_ENDPOINT=http://minio:9000
AWS_ACCESS_KEY_ID=minio
AWS_SECRET_ACCESS_KEY=minio123

# After (RustFS)
AWS_S3_ENDPOINT=http://rustfs:9000
AWS_ACCESS_KEY_ID=rustfsadmin
AWS_SECRET_ACCESS_KEY=rustfsadmin
```

2. Data migration options:

**Option A: Mirror via mc**
```bash
# Export from MinIO
mc alias set myminio http://localhost:9000 minio minio123
mc mirror myminio/lake ./backup/

# Import to RustFS
mc alias set myrustfs http://localhost:9000 rustfsadmin rustfsadmin
mc mirror ./backup/ myrustfs/lake/
```

**Option B: Direct volume copy**
```bash
cp -r ./volumes/minio/* ./volumes/rustfs/
chown -R 10001:10001 ./volumes/rustfs
```

## Entry Points

| Entry Point             | Plugin                      |
| ----------------------- | --------------------------- |
| `phlo.plugins.services` | `RustfsServicePlugin`       |
| `phlo.plugins.services` | `RustfsSetupServicePlugin` |

## Related Packages

- [phlo-minio](phlo-minio.md) - Alternative S3 storage (MinIO)
- [phlo-iceberg](phlo-iceberg.md) - Table format
- [phlo-nessie](phlo-nessie.md) - Catalog service

## Next Steps

- [Installation Guide](../getting-started/installation.md) - Complete setup
- [Architecture Reference](../reference/architecture.md) - System design
- [Operations Guide](../operations/operations-guide.md) - Backup and maintenance

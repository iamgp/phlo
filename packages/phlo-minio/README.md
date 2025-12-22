# phlo-minio

MinIO S3-compatible object storage plugin for Phlo.

## Description

Provides S3-compatible object storage for the data lake.

## Installation

```bash
pip install phlo-minio
# or
phlo plugin install minio
```

## Configuration

| Variable              | Default    | Description      |
| --------------------- | ---------- | ---------------- |
| `MINIO_ROOT_USER`     | `minio`    | Root username    |
| `MINIO_ROOT_PASSWORD` | `minio123` | Root password    |
| `MINIO_API_PORT`      | `9000`     | S3 API port      |
| `MINIO_CONSOLE_PORT`  | `9001`     | Web console port |

## Usage

```bash
phlo services start --service minio
```

## Endpoints

- **API**: `http://localhost:9000`
- **Console**: `http://localhost:9001`

# MinIO (S3-Compatible Object Storage)

## Overview

MinIO provides S3-compatible object storage for the data lake, storing all raw and processed data files in open formats (primarily Parquet).

## Configuration

**Image**: `minio/minio:latest`
**Container**: `minio`
**API Port**: `9000`
**Console Port**: `9001`

### Environment Variables
```bash
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=minio999
MINIO_API_PORT=9000
MINIO_CONSOLE_PORT=9001
```

## Access

### Web Console
- **URL**: http://localhost:9001
- **Username**: `minio`
- **Password**: `minio999`

### S3 API
- **Endpoint**: http://localhost:9000
- **Region**: `eu-west-1` (configured)

## Bucket Structure

### Recommended Layout
```
lake/
├── raw/              # Landing zone for raw data
│   ├── bioreactor/   # Raw bioreactor parquet files
│   ├── lims/         # Raw LIMS exports
│   └── instruments/  # Raw instrument data
├── staging/          # Cleaned/standardized data
├── curated/          # Business logic applied
└── archive/          # Historical/backup data
```

## Data Formats

### Primary: Parquet
- **Columnar format** - optimal for analytics
- **Compression** - smaller storage footprint
- **Schema evolution** - add/modify columns over time
- **DuckDB native** - read directly without loading

### Also Supported
- CSV (raw imports)
- JSON (API responses)
- Avro (streaming data)

## Connecting from Applications

### Python (boto3)
```python
import boto3

s3 = boto3.client(
    's3',
    endpoint_url='http://minio:9000',
    aws_access_key_id='minio',
    aws_secret_access_key='minio999',
    region_name='eu-west-1'
)

# List buckets
s3.list_buckets()

# Upload file
s3.upload_file('/local/file.parquet', 'lake', 'raw/bioreactor/batch_001.parquet')
```

### DuckDB
```sql
-- Configure S3 settings
SET s3_endpoint='minio:9000';
SET s3_use_ssl=false;
SET s3_url_style='path';
SET s3_access_key_id='minio';
SET s3_secret_access_key='minio999';

-- Read parquet from MinIO
SELECT * FROM read_parquet('s3://lake/raw/bioreactor/*.parquet');
```

### dbt (via DuckDB)
Configuration in `dbt/profiles/profiles.yml`:
```yaml
config:
  s3_endpoint: minio:9000
  s3_use_ssl: false
  s3_url_style: path
  s3_access_key_id: "{{ env_var('MINIO_ROOT_USER') }}"
  s3_secret_access_key: "{{ env_var('MINIO_ROOT_PASSWORD') }}"
```

### Airbyte
When configuring Airbyte destinations:
- **Type**: S3
- **Endpoint**: `http://minio:9000`
- **Bucket**: `lake`
- **Path**: `raw/{source_name}/`
- **Access Key**: `minio`
- **Secret Key**: `minio999`

## CLI Access

### MinIO Client (mc)
```bash
# Install mc
brew install minio/stable/mc

# Configure alias
mc alias set local http://localhost:9000 minio minio999

# List buckets
mc ls local

# Create bucket
mc mb local/lake

# Copy file
mc cp /local/file.parquet local/lake/raw/bioreactor/

# List files
mc ls local/lake/raw/bioreactor/
```

## Versioning

MinIO supports object versioning for immutability and audit trails:

```bash
# Enable versioning on bucket
mc version enable local/lake

# List versions of an object
mc version list local/lake/raw/bioreactor/batch_001.parquet
```

## Data Lifecycle

### Typical Flow
1. **Ingest**: Airbyte lands data → `raw/`
2. **Stage**: dbt reads from `raw/`, writes to DuckDB
3. **Curate**: dbt applies business logic in DuckDB
4. **Marts**: dbt materializes to Postgres for BI

### Retention Policies
Configure lifecycle rules via MinIO console or CLI:
```bash
# Delete objects older than 90 days in archive/
mc ilm add local/lake --prefix "archive/" --expiry-days 90
```

## Performance Tuning

### Partitioning
Organize data for efficient querying:
```
raw/bioreactor/
├── year=2025/
│   ├── month=01/
│   │   ├── batch_001.parquet
│   │   └── batch_002.parquet
│   └── month=02/
└── year=2024/
```

### File Sizes
- **Optimal**: 100MB - 1GB per parquet file
- **Avoid**: Many small files (< 10MB)
- **Combine**: Use dbt to consolidate fragmented data

## Monitoring

### Disk Usage
```bash
# Check bucket sizes
mc du local/lake --recursive

# Specific prefix
mc du local/lake/raw/bioreactor/
```

### Health Check
```bash
# API health
curl http://localhost:9000/minio/health/ready

# Container health
docker compose exec minio mc admin info local
```

## Backup & Disaster Recovery

### Mirror to Another MinIO/S3
```bash
# Mirror bucket to remote S3
mc mirror local/lake s3-remote/backup-lake
```

### Export to Local
```bash
# Download entire bucket
mc mirror local/lake /backup/lake-$(date +%Y%m%d)
```

### Snapshot Volumes
```bash
# Backup Docker volume
docker run --rm -v cascade_minio:/data -v $(pwd):/backup \
  alpine tar czf /backup/minio-backup.tar.gz /data
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker compose logs minio

# Verify volume permissions
ls -la volumes/minio/
```

### Can't Connect from Containers
- Ensure using `http://minio:9000` (not localhost)
- Check network: `docker network ls`
- Verify environment variables are set

### Bucket Not Found
```bash
# Create missing bucket
mc mb local/lake

# Set public policy (if needed)
mc policy set download local/lake/raw/bioreactor
```

### Performance Issues
- Check disk I/O: `docker stats minio`
- Increase resources in Docker Desktop settings
- Consider NVMe/SSD for volumes

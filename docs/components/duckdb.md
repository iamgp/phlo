# DuckDB (Analytical Engine)

> **Note:** Cascade now mounts DuckDB through the DuckLake extension, using PostgreSQL for the catalog and MinIO for table storage. The settings below still apply because DuckLake is implemented as a DuckDB extension.

## Overview

DuckDB is an in-process analytical database optimized for OLAP queries. It serves as the primary query engine for the lakehouse, executing SQL directly on Parquet files without requiring data loading.

## Architecture

### Embedded Database
- No separate server process
- Runs inside dbt/Python processes
- File-based: `warehouse.duckdb` at `/data/duckdb/`

### Key Features
- **Zero-copy reads**: Query parquet directly from MinIO/disk
- **Columnar execution**: Optimized for analytical queries
- **Extensions**: httpfs (S3), parquet, json support
- **ACID transactions**: Full consistency guarantees

## Configuration

### In dbt profiles.yml
```yaml
duckdb:
  type: duckdb
  path: /data/duckdb/warehouse.duckdb
  threads: 8
  extensions: ["httpfs", "json", "parquet"]
  config:
    s3_endpoint: minio:9000
    s3_use_ssl: false
    s3_url_style: path
    s3_access_key_id: "{{ env_var('MINIO_ROOT_USER') }}"
    s3_secret_access_key: "{{ env_var('MINIO_ROOT_PASSWORD') }}"
```

## Usage Patterns

### 1. External Tables (Staging Layer)
Read parquet without importing:
```sql
-- dbt staging model: stg_bioreactor.sql
{{ config(materialized='view') }}

SELECT
  cast(batch_id as varchar) as batch_id,
  equipment_id,
  ts::timestamp as ts,
  cast(tag as varchar) as tag,
  cast(value as double) as value,
  site
FROM read_parquet('/data/lake/raw/bioreactor/*.parquet');
```

### 2. Materialized Tables (Curated Layer)
Store aggregated/transformed data:
```sql
-- dbt curated model: fact_bioreactor_batch_stats.sql
{{ config(materialized='table') }}

SELECT
  batch_id,
  equipment_id,
  min(ts) as batch_start,
  max(ts) as batch_end,
  avg(value) as avg_value,
  count(*) as record_count
FROM {{ ref('stg_bioreactor') }}
GROUP BY batch_id, equipment_id;
```

### 3. Incremental Models
Process only new data:
```sql
{{ config(
    materialized='incremental',
    unique_key='batch_id'
) }}

SELECT * FROM {{ ref('stg_bioreactor') }}
{% if is_incremental() %}
  WHERE ts > (SELECT max(ts) FROM {{ this }})
{% endif %}
```

## Direct SQL Access

### From Container
```bash
docker compose exec dagster-web duckdb /data/duckdb/warehouse.duckdb
```

### Interactive Queries
```sql
-- List all tables
SHOW TABLES;

-- Table schema
DESCRIBE staging.stg_bioreactor;

-- Query staging data
SELECT batch_id, count(*)
FROM staging.stg_bioreactor
GROUP BY batch_id;

-- Query from parquet directly
SELECT * FROM read_parquet('/data/lake/raw/bioreactor/*.parquet')
LIMIT 10;
```

### Python Integration
```python
import duckdb

# Connect to warehouse
conn = duckdb.connect('/data/duckdb/warehouse.duckdb')

# Query
result = conn.execute("""
    SELECT batch_id, avg(value) as avg_value
    FROM staging.stg_bioreactor
    GROUP BY batch_id
""").fetchdf()

print(result)
```

## Performance Optimization

### 1. Partitioned Parquet Files
Organize by date/batch for partition pruning:
```
raw/bioreactor/
├── batch_id=001/
│   └── data.parquet
├── batch_id=002/
│   └── data.parquet
```

Query with partition filter:
```sql
SELECT * FROM read_parquet('/data/lake/raw/bioreactor/**/*.parquet',
    hive_partitioning=true)
WHERE batch_id = '001';
```

### 2. Aggregation Pushdown
DuckDB pushes filters/aggregations to parquet readers:
```sql
-- Efficient: filter pushed to parquet scan
SELECT avg(value)
FROM read_parquet('/data/lake/raw/bioreactor/*.parquet')
WHERE batch_id = '001';
```

### 3. Parallel Execution
Control parallelism:
```sql
-- Set thread count
SET threads = 8;

-- Query uses all threads
SELECT batch_id, count(*)
FROM staging.stg_bioreactor
GROUP BY batch_id;
```

### 4. Indexes (for tables)
```sql
-- Create index on materialized tables
CREATE INDEX idx_batch ON curated.fact_bioreactor_batch_stats(batch_id);
```

## Schema Management

### Schemas in dbt_project.yml
```yaml
models:
  cg_lakehouse:
    staging:
      +schema: staging
      +materialized: view
    intermediate:
      +schema: intermediate
    curated:
      +schema: curated
```

### Manual Schema Creation
```sql
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS intermediate;
CREATE SCHEMA IF NOT EXISTS curated;
```

## Extensions

### Load Extensions
```sql
-- Install extension
INSTALL httpfs;
INSTALL parquet;
INSTALL json;

-- Load extension
LOAD httpfs;
LOAD parquet;
```

### S3/MinIO Configuration
```sql
SET s3_endpoint='minio:9000';
SET s3_use_ssl=false;
SET s3_url_style='path';
SET s3_access_key_id='minio';
SET s3_secret_access_key='minio999';
```

## Data Export

### To Parquet
```sql
-- Export query results to parquet
COPY (
    SELECT * FROM curated.fact_bioreactor_batch_stats
) TO '/data/lake/curated/batch_stats.parquet' (FORMAT PARQUET);
```

### To CSV
```sql
COPY staging.stg_bioreactor TO '/data/exports/bioreactor.csv' (FORMAT CSV, HEADER);
```

### To Postgres (via dbt)
Use dbt's multi-target approach:
```bash
# Run models targeting postgres
dbt run --select tag:mart --target postgres
```

## Monitoring & Debugging

### Query Profiling
```sql
-- Enable profiling
PRAGMA enable_profiling;

-- Run query
SELECT batch_id, count(*) FROM staging.stg_bioreactor GROUP BY batch_id;

-- View profile
PRAGMA show_tables_expanded;
```

### Explain Plans
```sql
EXPLAIN SELECT batch_id, avg(value)
FROM staging.stg_bioreactor
WHERE batch_id = '001';
```

### Database Size
```sql
-- Table sizes
SELECT
    schema_name,
    table_name,
    pg_size_pretty(estimated_size) as size
FROM duckdb_tables()
ORDER BY estimated_size DESC;
```

## Backup & Recovery

### Export Database
```bash
# Backup all tables to parquet
duckdb /data/duckdb/warehouse.duckdb << EOF
EXPORT DATABASE '/data/backup/duckdb-export' (FORMAT PARQUET);
EOF
```

### Import Database
```bash
duckdb /data/duckdb/warehouse_new.duckdb << EOF
IMPORT DATABASE '/data/backup/duckdb-export';
EOF
```

### Copy File
```bash
# Simple file copy (when DB is not in use)
cp /data/duckdb/warehouse.duckdb /backup/warehouse-$(date +%Y%m%d).duckdb
```

## Troubleshooting

### Lock File Issues
```bash
# Database locked
# Solution: Ensure no dbt/Python processes are using it
docker compose exec dagster-web pkill -f duckdb
rm /data/duckdb/warehouse.duckdb.wal
```

### Memory Issues
```sql
-- Reduce memory usage
SET memory_limit='2GB';
SET max_memory='2GB';
```

### Extension Not Found
```sql
-- Reinstall extension
FORCE INSTALL httpfs;
LOAD httpfs;
```

## Comparison: DuckDB vs Postgres

| Feature | DuckDB | Postgres |
|---------|--------|----------|
| **Use Case** | OLAP / Analytics | OLTP / Transactional |
| **Data Location** | File / Parquet | Database tables |
| **Concurrency** | Read-heavy | Read-write balanced |
| **Performance** | Fast aggregations | Fast lookups |
| **Best For** | Data transformation | Data serving (BI) |

## When to Use What

- **DuckDB**: Data transformation, exploration, aggregations on large datasets
- **Postgres**: Final marts for dashboards, transactional workloads, multi-user access

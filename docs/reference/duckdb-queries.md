# DuckDB Iceberg Extension for Ad-hoc Analysis

This guide explains how to query Phlo's Iceberg tables directly using DuckDB's Iceberg extension, enabling fast ad-hoc analysis without going through Trino.

## Why DuckDB + Iceberg?

- **Fast ad-hoc queries**: DuckDB is optimized for analytical queries on local machines
- **Direct Iceberg access**: Read Iceberg tables directly from MinIO/S3
- **No server required**: Runs entirely on your laptop
- **Perfect for exploration**: Jupyter notebooks, scripts, and interactive analysis
- **Compatible**: Same data as Trino/dbt pipeline, different query engine

## Prerequisites

- DuckDB v1.1.0 or later (supports Iceberg extension)
- Access to MinIO endpoint (default: `localhost:10001`)
- MinIO credentials from `.phlo/.env.local`

## Installation

### 1. Install DuckDB

```bash
# macOS (Homebrew)
brew install duckdb

# or download from https://duckdb.org/docs/installation/

# Verify installation
duckdb --version
```

### 2. Install Iceberg Extension

```sql
-- Start DuckDB CLI
$ duckdb

-- Install and load the iceberg extension
D INSTALL iceberg;
D LOAD iceberg;
```

## Configuration

### Option 1: Interactive Configuration (DuckDB CLI)

```sql
-- Start DuckDB CLI
$ duckdb

-- Load extension
D LOAD iceberg;

-- Configure S3/MinIO connection
D SET s3_endpoint = 'localhost:10001';
D SET s3_use_ssl = false;
D SET s3_url_style = 'path';
D SET s3_access_key_id = 'minio';
D SET s3_secret_access_key = 'minio123';
```

### Option 2: Python Script Configuration

```python
import duckdb

# Create connection
conn = duckdb.connect()

# Install and load extension
conn.execute("INSTALL iceberg")
conn.execute("LOAD iceberg")

# Configure S3/MinIO
conn.execute("SET s3_endpoint = 'localhost:10001'")
conn.execute("SET s3_use_ssl = false")
conn.execute("SET s3_url_style = 'path'")
conn.execute("SET s3_access_key_id = 'minio'")
conn.execute("SET s3_secret_access_key = 'minio123'")
```

### Option 3: Environment Variables (Recommended for Scripts)

```bash
# Set environment variables
export S3_ENDPOINT=localhost:10001
export S3_USE_SSL=false
export S3_URL_STYLE=path
export AWS_ACCESS_KEY_ID=minio
export AWS_SECRET_ACCESS_KEY=minio123
```

```python
import duckdb

conn = duckdb.connect()
conn.execute("INSTALL iceberg")
conn.execute("LOAD iceberg")

# S3 config automatically picked up from environment variables
```

## Querying Iceberg Tables

### Method 1: Direct S3 Path (Recommended)

Query Iceberg tables using their S3/MinIO paths:

```sql
-- Query raw entries table
SELECT *
FROM iceberg_scan('s3://lake/warehouse/raw/entries')
LIMIT 10;

-- Query bronze staging table
SELECT *
FROM iceberg_scan('s3://lake/warehouse/bronze/stg_entries')
WHERE date_partition >= CURRENT_DATE - INTERVAL 7 DAY;

-- Query silver fact table
SELECT *
FROM iceberg_scan('s3://lake/warehouse/silver/fct_glucose_readings')
WHERE date >= CURRENT_DATE - INTERVAL 30 DAY;

-- Query gold dimension table
SELECT *
FROM iceberg_scan('s3://lake/warehouse/gold/dim_date')
ORDER BY date DESC
LIMIT 100;
```

### Method 2: Nessie Catalog Integration (Advanced)

For branch-aware queries, you can query specific Nessie branches:

```sql
-- Query from main branch (production)
SELECT *
FROM iceberg_scan(
    's3://lake/warehouse/raw/entries',
    metadata_location='s3://lake/warehouse/raw/entries/metadata/v1.metadata.json'
);

-- Note: Nessie catalog integration requires knowing the metadata file location
-- This is more complex and typically not needed for ad-hoc analysis
```

## Example Use Cases

### 1. Quick Data Exploration

```sql
-- See latest glucose readings
SELECT
    date_string,
    sgv,
    direction,
    device
FROM iceberg_scan('s3://lake/warehouse/raw/entries')
ORDER BY date DESC
LIMIT 20;
```

### 2. Data Quality Checks

```sql
-- Check for null values in critical fields
SELECT
    COUNT(*) as total_rows,
    COUNT(sgv) as non_null_sgv,
    COUNT(date) as non_null_date,
    COUNT(*) - COUNT(sgv) as null_sgv_count
FROM iceberg_scan('s3://lake/warehouse/raw/entries')
WHERE date_partition >= CURRENT_DATE - INTERVAL 7 DAY;
```

### 3. Aggregations and Analysis

```sql
-- Daily glucose statistics
SELECT
    date_trunc('day', timestamp) as day,
    COUNT(*) as reading_count,
    AVG(sgv) as avg_glucose,
    MIN(sgv) as min_glucose,
    MAX(sgv) as max_glucose,
    STDDEV(sgv) as std_glucose
FROM iceberg_scan('s3://lake/warehouse/silver/fct_glucose_readings')
WHERE date >= CURRENT_DATE - INTERVAL 30 DAY
GROUP BY day
ORDER BY day DESC;
```

### 4. Time-Based Filtering

```sql
-- Readings from last hour
SELECT *
FROM iceberg_scan('s3://lake/warehouse/raw/entries')
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 1 HOUR
ORDER BY timestamp DESC;
```

### 5. Export to CSV

```sql
-- Export analysis results to CSV
COPY (
    SELECT
        date_partition,
        AVG(sgv) as avg_glucose,
        COUNT(*) as reading_count
    FROM iceberg_scan('s3://lake/warehouse/silver/fct_glucose_readings')
    WHERE date >= CURRENT_DATE - INTERVAL 90 DAY
    GROUP BY date_partition
) TO 'glucose_analysis.csv' (HEADER, DELIMITER ',');
```

## Python Integration Examples

### Pandas Integration

```python
import duckdb
import pandas as pd

# Configure connection
conn = duckdb.connect()
conn.execute("INSTALL iceberg")
conn.execute("LOAD iceberg")
conn.execute("SET s3_endpoint = 'localhost:10001'")
conn.execute("SET s3_use_ssl = false")
conn.execute("SET s3_url_style = 'path'")
conn.execute("SET s3_access_key_id = 'minio'")
conn.execute("SET s3_secret_access_key = 'minio123'")

# Query to DataFrame
df = conn.execute("""
    SELECT *
    FROM iceberg_scan('s3://lake/warehouse/silver/fct_glucose_readings')
    WHERE date >= CURRENT_DATE - INTERVAL 7 DAY
""").df()

print(df.head())
print(df.describe())
```

### Jupyter Notebook Integration

```python
# In Jupyter notebook
import duckdb
import plotly.express as px

# Setup
conn = duckdb.connect()
conn.execute("INSTALL iceberg")
conn.execute("LOAD iceberg")
conn.execute("SET s3_endpoint = 'localhost:10001'")
conn.execute("SET s3_use_ssl = false")
conn.execute("SET s3_url_style = 'path'")
conn.execute("SET s3_access_key_id = 'minio'")
conn.execute("SET s3_secret_access_key = 'minio123'")

# Query and visualize
df = conn.execute("""
    SELECT
        timestamp,
        sgv
    FROM iceberg_scan('s3://lake/warehouse/silver/fct_glucose_readings')
    WHERE date >= CURRENT_DATE - INTERVAL 7 DAY
    ORDER BY timestamp
""").df()

# Plot with Plotly
fig = px.line(df, x='timestamp', y='sgv', title='Glucose Readings (Last 7 Days)')
fig.show()
```

## Performance Tips

### 1. Use Partition Filters

Iceberg tables are partitioned by date. Always filter by partition when possible:

```sql
-- GOOD: Uses partition filtering
SELECT *
FROM iceberg_scan('s3://lake/warehouse/raw/entries')
WHERE date_partition >= '2025-10-01';

-- LESS EFFICIENT: Full table scan
SELECT *
FROM iceberg_scan('s3://lake/warehouse/raw/entries')
WHERE timestamp >= '2025-10-01'::TIMESTAMP;
```

### 2. Limit Result Sets

For exploration, use LIMIT to avoid pulling large datasets:

```sql
SELECT *
FROM iceberg_scan('s3://lake/warehouse/raw/entries')
LIMIT 1000;
```

### 3. Use Aggregations

Push aggregations down to DuckDB instead of pulling all data:

```sql
-- GOOD: Aggregation in DuckDB
SELECT date_partition, COUNT(*)
FROM iceberg_scan('s3://lake/warehouse/raw/entries')
GROUP BY date_partition;

-- LESS EFFICIENT: Pull all data then aggregate in Python
```

## Available Tables

Query these Iceberg tables based on your pipeline layer:

### Raw Layer

- `s3://lake/warehouse/raw/entries` - Nightscout CGM entries (raw ingestion)

### Bronze Layer (via dbt)

- `s3://lake/warehouse/bronze/stg_entries` - Staged entries with basic transformations

### Silver Layer (via dbt)

- `s3://lake/warehouse/silver/fct_glucose_readings` - Cleaned glucose facts

### Gold Layer (via dbt)

- `s3://lake/warehouse/gold/dim_date` - Date dimension table
- `s3://lake/warehouse/gold/mrt_glucose_readings` - Glucose mart (materialized)

## Troubleshooting

### Issue: Cannot connect to MinIO

```
Error: Connection failed to localhost:10001
```

**Solution**: Ensure MinIO is running and accessible:

```bash
# Check if MinIO is running
docker compose ps minio

# Verify MinIO endpoint
curl http://localhost:10001/minio/health/ready
```

### Issue: Authentication failed

```
Error: Access Denied
```

**Solution**: Verify credentials match your `.phlo/.env.local` file:

```bash
# Check .phlo/.env.local
grep MINIO .phlo/.env.local

# Use matching credentials in DuckDB
SET s3_access_key_id = 'minio';
SET s3_secret_access_key = 'minio123';
```

### Issue: Table not found

```
Error: Failed to read Iceberg table metadata
```

**Solution**:

1. Verify the table path exists in MinIO
2. Check that ingestion pipeline has run successfully
3. Ensure you're using the correct warehouse path

```sql
-- List files in MinIO using AWS CLI or MinIO console
-- Correct path should be: s3://lake/warehouse/<schema>/<table>/
```

### Issue: SSL/TLS errors

```
Error: SSL peer certificate validation failed
```

**Solution**: Ensure SSL is disabled for MinIO:

```sql
SET s3_use_ssl = false;
```

## Comparison: DuckDB vs Trino

| Feature           | DuckDB + Iceberg             | Trino (via dbt/Dagster)               |
| ----------------- | ---------------------------- | ------------------------------------- |
| **Use Case**      | Ad-hoc analysis, exploration | Production pipelines, transformations |
| **Setup**         | Local CLI/Python             | Requires Trino service                |
| **Performance**   | Fast for local queries       | Distributed queries                   |
| **Branching**     | Manual metadata paths        | Full Nessie integration               |
| **Write Support** | Read-only                    | Read and write                        |
| **Best For**      | Analysts, data scientists    | Data engineers, pipelines             |

## Best Practices

1. **Use DuckDB for**:
   - Quick data exploration
   - Ad-hoc analysis
   - Jupyter notebook workflows
   - Export to CSV/Parquet
   - Local development/testing

2. **Use Trino for**:
   - Production pipelines
   - Branch-aware workflows (dev/prod)
   - Writing to Iceberg tables
   - Complex multi-table joins
   - dbt transformations

3. **Security**:
   - Never commit credentials to git
   - Use environment variables for automation
   - DuckDB is read-only for Iceberg by default (safe for exploration)

4. **Performance**:
   - Always use partition filters when possible
   - Limit result sets during exploration
   - Use aggregations to reduce data transfer

## Further Reading

- [DuckDB Iceberg Extension Docs](https://duckdb.org/docs/extensions/iceberg.html)
- [Apache Iceberg Documentation](https://iceberg.apache.org/)
- [DuckDB S3 Configuration](https://duckdb.org/docs/extensions/httpfs.html)
- [Project Nessie Documentation](https://projectnessie.org/)

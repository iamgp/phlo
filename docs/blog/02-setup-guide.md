# Part 2: Getting Started with Phlo—Setup Guide

In this post, we'll get Phlo running on your machine. By the end, you'll have:

- All services running (Postgres, MinIO, Nessie, Trino, Dagster)
- Sample data ingested
- Your first data pipeline executed
- A dashboard showing results

## Prerequisites

### What You Need

1. **Docker & Docker Compose** (required)

   ```bash
   # Verify installation
   docker --version
   docker compose --version
   ```

   [Install Docker](https://docs.docker.com/get-docker/) if you don't have it

2. **uv** (Python package manager, optional but recommended)

   ```bash
   # Install uv (10x faster than pip)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Python 3.11+** with Phlo installed
   ```bash
   # Install Phlo (with uv, recommended)
   uv pip install phlo[defaults]
   # or with pip
   pip install phlo[defaults]
   ```

### System Requirements

| Component | Minimum           | Recommended |
| --------- | ----------------- | ----------- |
| CPU       | 2 cores           | 4+ cores    |
| RAM       | 4 GB              | 8+ GB       |
| Disk      | 10 GB             | 20+ GB      |
| OS        | Linux/Mac/Windows | Mac/Linux   |

If you have less than 4GB RAM, you can start a minimal setup (Postgres + MinIO only) and add services gradually.

## Step 1: Initialize Your Project

```bash
# Create a new Phlo project
phlo init my-lakehouse
cd my-lakehouse

# This creates:
# - phlo.yaml (project configuration)
# - .env (environment variables)
# - workflows/ (your data pipelines)
# - transforms/ (dbt models)
```

### What's in .env?

```env
# Database
POSTGRES_USER=lake
POSTGRES_PASSWORD=phlo
POSTGRES_DB=lakehouse

# Storage
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=minio123

# Ports (all on 10xxx range)
POSTGRES_PORT=10000
MINIO_API_PORT=10001
MINIO_CONSOLE_PORT=10002
NESSIE_PORT=10003
TRINO_PORT=10005
DAGSTER_PORT=10006
```

**For local development**: Use the defaults as-is.
**For production**: Change all passwords to strong values.

> **SECURITY WARNING**: The default configuration uses weak passwords (`admin/admin`, `minioadmin/minioadmin123`, etc.) and has no authentication enabled on most services. This is fine for local development, but **NEVER expose these services to a network or the internet** without:
>
> - Changing all default passwords to strong, unique values
> - Enabling authentication on all services (Dagster, Trino, MinIO, Superset)
> - Using TLS/SSL for encrypted connections
> - Implementing proper network security (firewall rules, VPNs)
>
> See [Part 12: Production Deployment](12-production-deployment.md) for production hardening guidance.

## Step 2: Install Phlo Packages

Phlo uses a modular architecture. Install the core framework, then add services as needed.

### Option A: Install All Defaults (Quick Start)

```bash
# Install Phlo with all default services at once
uv pip install phlo[defaults]
```

This installs:

- `phlo` - Core framework
- `phlo-dagster` - Data orchestration platform
- `phlo-postgres` - PostgreSQL database
- `phlo-trino` - Distributed SQL query engine
- `phlo-nessie` - Git-like catalog for Iceberg
- `phlo-minio` - S3-compatible object storage

### Option B: Install Incrementally (Recommended for Learning)

```bash
# Start with core framework
uv pip install phlo

# Add data orchestration
uv add phlo-dagster

# Add storage layer
uv add phlo-postgres phlo-minio

# Add Iceberg catalog
uv add phlo-nessie

# Add query engine
uv add phlo-trino

# Add transformations
uv add phlo-dbt

# Add data quality
uv add phlo-quality
```

This modular approach lets you:

- Understand each component's role
- Start with minimal resources
- Add features as you need them

### Option C: Add Optional Services Later

```bash
# Add observability (monitoring, logging)
uv add phlo-prometheus phlo-grafana phlo-loki phlo-alloy

# Add API layer (REST, GraphQL)
uv add phlo-api phlo-postgrest phlo-hasura

# Add data catalog
uv add phlo-openmetadata

# Add Observatory UI (web interface)
uv add phlo-observatory
```

## Step 3: Start Services

### Option A: Start Everything at Once (Recommended)

```bash
# Start all services
phlo services start

# View service status
phlo services status
```

### Option B: Start Specific Services

```bash
# Start only what you need
phlo services start --service postgres --service dagster

# Add more services later
phlo services start --service trino --service observatory
```

### Verify Services Are Running

```bash
# Check all services
phlo services status

# View logs
phlo services logs -f

# Or for a specific service
phlo services logs dagster
```

If any show errors, check logs:

```bash
phlo services logs dagster
```

## Step 4: Access the Services

Each service runs on its own port:

```bash
# Open services in browser
phlo services open dagster
phlo services open observatory
phlo services open minio
```

| Service       | URL                    | Purpose             |
| ------------- | ---------------------- | ------------------- |
| Dagster       | http://localhost:10006 | Orchestration UI    |
| Observatory   | http://localhost:3001  | Data exploration UI |
| Trino         | http://localhost:10005 | Query engine UI     |
| MinIO Console | http://localhost:10002 | Object storage      |
| PostgreSQL    | http://localhost:10000 | Database            |
| Nessie        | http://localhost:10003 | Catalog API         |

## Step 5: First Data Ingestion

Now let's ingest some real glucose monitoring data and run the pipeline.

### 5a: Trigger Data Ingestion

Open **Dagster** at http://localhost:10006

You should see the asset graph:

```
glucose_entries
  ↓
stg_glucose_entries (dbt)
  ↓
fct_glucose_readings (dbt)
  ↓
fct_daily_glucose_metrics
  ↓
postgres_marts
```

Click on `glucose_entries` → Click **Materialize this asset**

In the modal, select **Date range**: pick yesterday's date (or any recent date)

Click **Materialize** and watch the pipeline run.

### 5b: Monitor in Logs

```bash
# Watch service logs
phlo services logs -f

# Or just Dagster logs
phlo services logs dagster

# Watch asset progress in Dagster UI (it updates live)
# Open http://localhost:10006
```

The ingestion does:

1. Fetches glucose entries from Nightscout API
2. Validates with Pandera schemas
3. Stages to MinIO as parquet
4. Merges to Iceberg with deduplication

You should see output like:

```
2024-10-15 10:30:45 - Successfully fetched 288 entries from API
2024-10-15 10:30:46 - Raw data validation passed for 288 entries
2024-10-15 10:30:48 - DLT staging completed in 1.23s
2024-10-15 10:30:50 - Merged 288 rows to raw.glucose_entries
```

### 5c: Run Transformations

Once ingestion completes, run dbt transforms:

In Dagster, click **Materialize this asset** on `stg_glucose_entries`

This will:

1. Run dbt bronze layer (staging)
2. Run dbt silver layer (fact tables with business logic)
3. Run dbt gold layer (dimensions)
4. Publish to Postgres marts

Watch it propagate through the graph:

```
glucose_entries [SUCCESS]
  ↓
stg_glucose_entries ⏳ (running)
  ↓
fct_glucose_readings ⏳ (waiting)
  ↓
postgres_marts ⏳ (waiting)
```

### 5d: Check Results

Once complete, verify data in the databases:

**Option 1: Observatory UI**

Open http://localhost:3001 in your browser:

1. Click **Data Explorer** in the sidebar
2. Select `silver.fct_glucose_readings` table
3. View schema, preview data, and run queries

**Option 2: Trino CLI**

```bash
docker exec -it trino trino \
  --catalog iceberg \
  --schema silver \
  --execute "SELECT COUNT(*) as row_count FROM fct_glucose_readings;"

# Output:
# row_count
# ─────────
#      288
```

**Option 3: DuckDB (Local Analysis)**

```bash
# If you have DuckDB installed locally
duckdb

-- Connect to MinIO data
D SELECT COUNT(*) FROM read_parquet('s3://lake/warehouse/silver/fct_glucose_readings/**/*.parquet');
```

## Step 6: Explore with Observatory

Phlo includes Observatory, a web UI for exploring your lakehouse.

### 6a: Open Observatory

```bash
phlo services open observatory
# Opens http://localhost:3001
```

### 6b: Explore Data

1. Click **Data Explorer** in the sidebar
2. Browse schemas: `raw`, `bronze`, `silver`, `gold`
3. Click any table to see:
   - Schema and column types
   - Data preview
   - Statistics

### 6c: View Lineage

1. Click **Lineage** in the sidebar
2. See how data flows from source → bronze → silver → gold
3. Click nodes to see details

### 6d: Run Queries

1. Click **SQL Workbench**
2. Run ad-hoc queries against your Iceberg tables:

```sql
SELECT
  date_trunc('hour', reading_timestamp) as hour,
  avg(glucose_mg_dl) as avg_glucose
FROM silver.fct_glucose_readings
GROUP BY 1
ORDER BY 1 DESC
LIMIT 24
```

### 6c: Create a Chart

1. Click **+ Data** → **Create Chart**
2. Choose Dataset: `mrt_glucose_overview` (Postgres table)
3. Chart type: **Line Chart**
4. Drag columns:
   - X-Axis: `reading_date`
   - Y-Axis: `avg_glucose_mg_dl`
5. Click **Update Chart**
6. Click **Save Chart**

Congratulations! You've visualized real glucose data from a lakehouse.

## Troubleshooting

### Services Won't Start

```bash
# Check service status
phlo services status

# View specific service logs
phlo services logs postgres
phlo services logs dagster

# Restart all services
phlo services restart
```

### Out of Disk Space

```bash
# Clean up Docker resources
docker system prune
docker volume prune

# Reset services (WARNING: deletes all data)
phlo services reset
```

### Nessie Connection Error

```bash
# Check Nessie status
phlo services status nessie

# View Nessie logs
phlo services logs nessie

# Verify Nessie is healthy
curl http://localhost:10003/api/v1/config
```

### Trino Can't Find Iceberg Connector

```bash
# Check Trino logs
phlo services logs trino

# Verify catalog is configured (once Trino is running)
docker exec trino trino --execute "SHOW CATALOGS;"

# Should output:
# catalog
# ─────────
# iceberg
# system
```

### Dagster Assets Not Appearing

```bash
# Restart Dagster services
phlo services restart dagster

# Wait 10 seconds, refresh http://localhost:10006
```

## What's Next?

You now have a working lakehouse! Next steps:

1. **Explore the Data** (Part 3): Understand Iceberg and Nessie
2. **Understand Ingestion** (Part 4): How DLT + PyIceberg works
3. **Learn dbt** (Part 5): SQL transformations
4. **Master Dagster** (Part 6): Orchestration and dependencies

But first, let's make sure everything works by running a quick health check.

## Quick Health Check

```bash
# Check all services at once
phlo services status

# Or use the health endpoint
curl http://localhost:10005/v1/info     # Trino
curl http://localhost:10003/api/v1/config  # Nessie
curl http://localhost:10006/graphql     # Dagster
```

Or run the CLI check:

```bash
phlo services status --json
```

## Summary

You've successfully:

- Set up Phlo with all services
- Ingested real glucose data
- Ran transformations
- Created a dashboard

In Part 3, we'll dive deep into **Apache Iceberg**—the magic that makes this lakehouse work.

**Next**: [Part 3: Apache Iceberg—The Table Format That Changed Everything](03-apache-iceberg-explained.md)

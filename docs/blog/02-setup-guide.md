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

3. **Git** (to clone the repo)
   ```bash
   git clone https://github.com/iamgp/lakehousekit.git phlo
   cd phlo
   ```

### System Requirements

| Component | Minimum           | Recommended |
| --------- | ----------------- | ----------- |
| CPU       | 2 cores           | 4+ cores    |
| RAM       | 4 GB              | 8+ GB       |
| Disk      | 10 GB             | 20+ GB      |
| OS        | Linux/Mac/Windows | Mac/Linux   |

If you have less than 4GB RAM, you can start a minimal setup (Postgres + MinIO only) and add services gradually.

## Step 1: Clone and Configure

```bash
# Clone the repository
git clone https://github.com/iamgp/lakehousekit.git phlo
cd phlo

# Copy example environment file
cp .env.example .env

# Edit .env with your choices (or use defaults)
# For local development, defaults are fine
vim .env  # or open in your editor
```

### What's in .env?

```env
# Database
POSTGRES_USER=phlo
POSTGRES_PASSWORD=localpass123
POSTGRES_DB=lakehouse

# Storage
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123

# Services
NESSIE_VERSION=0.85.1
TRINO_VERSION=434
DAGSTER_VERSION=1.8.0
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

## Step 2: Install Python Dependencies (Optional)

If you want to run local commands (linting, type checking), install Python deps:

```bash
# This is optional—services run in Docker anyway
cd packages/phlo-dagster
uv pip install -e .
cd ../..
```

If you don't have `uv` and don't want to install it, you can skip this. Docker will handle everything.

## Step 3: Start Services

### Option A: Start Everything at Once (Recommended)

```bash
# Start all services
make up-all

# Or with docker compose directly
docker compose up -d
```

### Option B: Start in Stages (If RAM is Limited)

```bash
# Core services first
make up-core
# Output:
# ✓ postgres
# ✓ minio
# ✓ nessie
# ✓ dagster

# Add query engines
make up-query
# ✓ trino

# Add BI
make up-bi
# ✓ superset
```

### Verify Services Are Running

```bash
# Check all containers
docker compose ps

# Output should show:
# NAME              STATUS
# pg                Up 2 minutes (healthy)
# minio             Up 2 minutes (healthy)
# nessie            Up 2 minutes (healthy)
# trino             Up 2 minutes
# dagster-webserver Up 2 minutes
# dagster-daemon    Up 2 minutes
```

If any show "Exited", check logs:

```bash
docker compose logs <service-name>
```

## Step 4: Access the Services

Each service runs on its own port for easy access:

```bash
# Service Dashboard (overview of all services)
make hub
# Opens: http://localhost:54321

# Dagster UI (data orchestration)
make dagster
# Opens: http://localhost:3000

# MinIO Console (object storage)
make minio
# Opens: http://localhost:9001
# Login: minioadmin / minioadmin123

# Superset (dashboards)
make superset
# Opens: http://localhost:8088
# (First login requires setup—see below)

# Postgres Web UI (database browser)
make pgweb
# Opens: http://localhost:8081
```

Or open them manually:
| Service | URL | Purpose |
|---------|-----|---------|
| Hub | http://localhost:54321 | Service overview |
| Dagster | http://localhost:3000 | Orchestration UI |
| Trino | http://localhost:8080 | Query engine UI |
| MinIO Console | http://localhost:9001 | Object storage |
| Superset | http://localhost:8088 | Dashboards |
| Postgres Web | http://localhost:8081 | Database browser |

## Step 5: First Data Ingestion

Now let's ingest some real glucose monitoring data and run the pipeline.

### 5a: Trigger Data Ingestion

Open **Dagster** at http://localhost:3000

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
# Watch Dagster logs
docker compose logs -f dagster-daemon

# Watch asset progress in Dagster UI (it updates live)
# Open http://localhost:3000
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

**Option 1: Postgres Web UI**

```bash
make pgweb
# Opens http://localhost:8081
# Click "lakehouse" database
# Browse to "public" schema
# View tables: mrt_glucose_overview, mrt_glucose_hourly_patterns
```

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

## Step 6: Create a Dashboard

Now let's visualize the data in Superset.

### 6a: Set Up Superset

```bash
make superset
# Opens http://localhost:8088
```

First-time setup:

1. Click **Create Account**
2. Fill in details (username: `admin`, password: `admin123`)
3. Click **Next**

### 6b: Add Data Source

1. In Superset menu, click **+ Data** → **Add Database**
2. Select **PostgreSQL**
3. Fill in connection:
   - Engine: `postgresql`
   - Username: `phlo`
   - Password: (from .env)
   - Host: `postgres`
   - Port: `5432`
   - Database: `lakehouse`
4. Click **Test Connection** (should succeed)
5. Click **Save**

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
# Check container status
docker compose ps

# View specific service logs
docker compose logs postgres
docker compose logs nessie
docker compose logs trino

# Restart all services
docker compose restart
```

### Out of Disk Space

```bash
# Clean up old volumes
docker system prune
docker volume prune

# Start fresh (WARNING: deletes all data)
docker compose down -v
docker compose up -d
```

### Nessie Connection Error

```bash
# Nessie needs Postgres to be ready first
docker compose down
docker compose up postgres
# Wait 30 seconds
docker compose up -d

# Verify Nessie is healthy
curl http://localhost:19120/api/v1/config
```

### Trino Can't Find Iceberg Connector

```bash
# Check Trino logs
docker compose logs trino

# Verify catalog is configured
docker exec trino trino --execute "SHOW CATALOGS;"

# Should output:
# catalog
# ─────────
# iceberg
# system
```

### Dagster Assets Not Appearing

```bash
# Dagster needs to discover assets from code
# Restart the daemon
docker compose restart dagster-daemon

# Wait 10 seconds, refresh http://localhost:3000
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
#!/bin/bash
# Save as: health-check.sh

echo " Checking Phlo services..."

# Postgres
echo -n "Postgres: "
docker exec pg pg_isready -U phlo && echo "OK" || echo "FAIL"

# MinIO
echo -n "MinIO: "
curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/minio/health/ready | grep 200 > /dev/null && echo "OK" || echo "FAIL"

# Nessie
echo -n "Nessie: "
curl -s -o /dev/null -w "%{http_code}" http://localhost:19120/api/v1/config | grep 200 > /dev/null && echo "OK" || echo "FAIL"

# Trino
echo -n "Trino: "
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/v1/info | grep 200 > /dev/null && echo "OK" || echo "FAIL"

# Dagster
echo -n "Dagster: "
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/graphql | grep 200 > /dev/null && echo "OK" || echo "FAIL"

echo "All systems ready for data engineering!"
```

Run it:

```bash
chmod +x health-check.sh
./health-check.sh
```

## Summary

You've successfully:

- Set up Phlo with all services
- Ingested real glucose data
- Ran transformations
- Created a dashboard

In Part 3, we'll dive deep into **Apache Iceberg**—the magic that makes this lakehouse work.

**Next**: [Part 3: Apache Iceberg—The Table Format That Changed Everything](03-apache-iceberg-explained.md)

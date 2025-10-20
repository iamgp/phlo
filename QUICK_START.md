# Quick Start Guide

This guide will get you up and running with Cascade in under 10 minutes.

## Prerequisites

- **Docker Desktop** (or Docker Engine + Docker Compose)
  - Minimum 8GB RAM allocated to Docker
  - 20GB free disk space
- **`uv`** (for Python development): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Git** (to clone the repository)

## Step 1: Clone and Configure

```bash
# Clone the repository
git clone https://github.com/your-username/cascade.git
cd cascade

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# At minimum, set passwords for security:
# - POSTGRES_PASSWORD
# - MINIO_ROOT_PASSWORD
nano .env  # or use your preferred editor
```

## Step 2: Install Python Dependencies (Optional)

This step is only needed for local development outside Docker.

```bash
# Install main package
cd services/dagster
uv pip install -e .
cd ../..

# Verify installation
uv run python -c "from cascade import config; print('Installation successful!')"
```

## Step 3: Start Services

Cascade uses Docker Compose profiles to start services in groups.

### Option A: Start All Services (Recommended for First Run)

```bash
make up-all
```

This starts:
- **Core**: PostgreSQL, MinIO, Dagster, Hub
- **Query**: Trino, Nessie
- **BI**: Superset, pgweb

### Option B: Start Service Groups Individually

```bash
# Core services (required)
make up-core

# Query services (Trino + Nessie)
make up-query

# BI services (optional)
make up-bi
```

### Option C: Use Docker Compose Directly

```bash
# Start all services
docker compose --profile all up -d

# Or start specific profiles
docker compose --profile core --profile query up -d
```

## Step 4: Verify Services

Wait about 30 seconds for all services to start, then check:

```bash
# Check service health
docker compose ps

# Should see all services as "healthy" or "running"
```

Access the web interfaces using the provided make targets:

- **Hub**: `make hub` - Service status dashboard (localhost:10009)
- **Dagster**: `make dagster` - Orchestration UI (localhost:10006)
- **Documentation**: `make docs` - MkDocs documentation (localhost:10012)
- **Superset**: `make superset` - BI dashboards (localhost:10007)
- **MinIO Console**: `make minio` - Object storage (localhost:10002)
- **API Docs**: `make api` - REST API documentation (localhost:10010/docs)
- **Grafana**: `make grafana` - Observability dashboards (localhost:10016)

No additional setup required - all services use sequential ports (10000-10017).

## Step 5: Initialize Nessie Branches

Nessie branches are automatically created on first startup. Verify:

```bash
# Check branches
docker exec dagster-webserver python -c "
from cascade.defs.resources.nessie import NessieClient
nessie = NessieClient()
branches = nessie.list_branches()
print('Branches:', [b.name for b in branches])
"

# Should output: Branches: ['main', 'dev']
```

## Step 6: Run Your First Pipeline

### 6.1 Ingest Raw Data

```bash
# Materialize the Nightscout entries asset
docker exec dagster-webserver dagster asset materialize \
  --select entries

# Check logs in Dagster UI
open http://localhost:10006
```

This will:
1. Fetch data from Nightscout API
2. Stage as Parquet files in MinIO
3. Register Iceberg table via PyIceberg
4. Append data to `iceberg.raw.entries`

### 6.2 Run dbt Transformations

```bash
# Run all dbt models (bronze → silver → gold)
docker exec dagster-webserver dagster asset materialize \
  --select "dbt:*"
```

This will:
1. Create `bronze.stg_entries` (staging layer)
2. Create `silver.fct_glucose_readings` (fact table)
3. Create `gold.dim_date` (dimension table)

All tables are Iceberg tables on the `dev` branch by default.

### 6.3 Promote to Main (Production)

```bash
# Merge dev branch to main
docker exec dagster-webserver dagster asset materialize \
  --select promote_dev_to_main
```

This atomically promotes all validated data from `dev` to `main`.

### 6.4 Publish to PostgreSQL Marts

```bash
# Publish curated marts to Postgres for BI
docker exec dagster-webserver dagster asset materialize \
  --select "postgres_*"
```

This creates:
- `marts.mrt_glucose_overview` (7-day summary)
- `marts.mrt_glucose_hourly_patterns` (hourly patterns)

### 6.5 View in Superset

1. Open http://localhost:10007
2. Login: `admin` / `admin`
3. Navigate to **Charts** or **Dashboards**
4. Create new chart from `marts.mrt_glucose_overview`

## Step 7: Query Your Data

### Query via Trino CLI

```bash
# Connect to Trino
docker exec -it trino trino

# List catalogs
SHOW CATALOGS;

# List schemas
SHOW SCHEMAS FROM iceberg;

# Query raw data
SELECT * FROM iceberg.raw.entries LIMIT 10;

# Query transformed data
SELECT * FROM iceberg.silver.fct_glucose_readings LIMIT 10;
```

### Query via DuckDB (Ad-hoc Analysis)

See [docs/duckdb-iceberg-queries.md](./docs/duckdb-iceberg-queries.md) for detailed instructions.

```bash
# Install DuckDB CLI
brew install duckdb  # macOS
# or download from https://duckdb.org/

# Query Iceberg table
duckdb -c "
INSTALL iceberg;
LOAD iceberg;
INSTALL httpfs;
LOAD httpfs;
SET s3_endpoint='localhost:10001';
SET s3_use_ssl=false;
SET s3_access_key_id='minioadmin';
SET s3_secret_access_key='password123';
SELECT * FROM iceberg_scan('s3://lake/warehouse/raw/entries/metadata/v1.metadata.json') LIMIT 10;
"
```

### Query via Python

```python
from cascade.iceberg.catalog import get_catalog

# Get catalog
cat = get_catalog(ref='main')

# List tables
print(cat.list_tables('raw'))

# Load table
table = cat.load_table('raw.entries')

# Scan to DataFrame
df = table.scan().to_pandas()
print(df.head())
```

## Step 8: Schedule Automated Runs

Cascade includes pre-configured schedules:

1. Open Dagster UI: http://localhost:10006
2. Navigate to **Automation** → **Schedules**
3. Enable **"dev_pipeline_schedule"** (runs daily at 02:00)
4. Enable **"manual_promotion_trigger"** (run manually)

Or use the CLI:

```bash
# Enable schedule
docker exec dagster-webserver dagster schedule start dev_pipeline_schedule

# Trigger manual run
docker exec dagster-webserver dagster schedule trigger dev_pipeline_schedule
```

## Common Tasks

### View Logs

```bash
# Dagster daemon (runs assets)
docker logs -f dagster-daemon

# Dagster webserver (UI)
docker logs -f dagster-webserver

# Trino (queries)
docker logs -f trino

# Nessie (catalog operations)
docker logs -f nessie
```

### Restart Services

```bash
# Restart single service
docker compose restart dagster-webserver

# Restart all services
docker compose restart

# Restart with fresh state (destroys data)
make clean-all
make fresh-start
```

### Access MinIO Files

```bash
# List buckets
docker exec minio mc ls local/

# List warehouse
docker exec minio mc ls local/lake/warehouse/ --recursive

# Download metadata file
docker exec minio mc cp local/lake/warehouse/raw/entries/metadata/v1.metadata.json /tmp/
```

### Run dbt Manually

```bash
# Run specific model
docker exec dagster-webserver dbt run \
  --project-dir /dbt \
  --profiles-dir /dbt/profiles \
  --select stg_entries \
  --target dev

# Run tests
docker exec dagster-webserver dbt test \
  --project-dir /dbt \
  --profiles-dir /dbt/profiles \
  --target dev

# Debug connection
docker exec dagster-webserver dbt debug \
  --project-dir /dbt \
  --profiles-dir /dbt/profiles
```

### Inspect PostgreSQL

```bash
# Connect to Postgres
docker exec -it postgres psql -U lake -d lakehouse

# List schemas
\dn

# List tables in marts
\dt marts.*

# Query marts
SELECT * FROM marts.mrt_glucose_overview LIMIT 10;
```

## Troubleshooting

### Services Won't Start

**Check Docker resources:**
```bash
docker stats

# If memory usage is high, increase Docker memory limit
# Docker Desktop → Settings → Resources → Memory → 8GB+
```

**Check ports:**
```bash
# Ensure no conflicts with ports 3000, 8080, 8088, 9000, 9001, 19120
lsof -i :3000
lsof -i :8080
```

### Nessie API Not Responding

```bash
# Check Nessie logs
docker logs nessie

# Test API
curl http://localhost:19120/api/v2/config

# If 404, wait 30 seconds for Nessie to start
# If still failing, restart Nessie
docker compose restart nessie
```

### Trino Can't Connect to Nessie

```bash
# Check Trino catalog config
docker exec trino cat /etc/trino/catalog/iceberg.properties

# Should include:
# iceberg.rest-catalog.uri=http://nessie:19120/iceberg

# Test from Trino container
docker exec trino curl http://nessie:19120/iceberg/v1/config
```

### PyIceberg Can't Write Tables

```bash
# Check MinIO access
docker exec dagster-webserver python -c "
import boto3
s3 = boto3.client(
    's3',
    endpoint_url='http://minio:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='password123'
)
print(s3.list_buckets())
"

# Check Nessie connection
docker exec dagster-webserver python -c "
from cascade.iceberg.catalog import get_catalog
cat = get_catalog()
print(cat.list_namespaces())
"
```

### Dagster Assets Failing

```bash
# View asset details in Dagster UI
open http://localhost:10006

# Check environment variables
docker exec dagster-webserver env | grep -E 'NESSIE|TRINO|MINIO'

# Verify configuration
docker exec dagster-webserver python -c "
from cascade.config import config
print(config.model_dump_json(indent=2))
"
```

### Fresh Start (Nuclear Option)

```bash
# WARNING: This destroys all data, containers, and volumes
make clean-all

# Start fresh
make fresh-start

# Or manually:
docker compose down -v
docker system prune -af --volumes
make up-all
```

## Next Steps

Now that you have Cascade running:

1. **Read the Architecture Guide**: [ARCHITECTURE.md](./ARCHITECTURE.md)
2. **Learn Nessie Workflows**: [NESSIE_WORKFLOW.md](./NESSIE_WORKFLOW.md)
3. **Explore DuckDB Queries**: [docs/duckdb-iceberg-queries.md](./docs/duckdb-iceberg-queries.md)
4. **Add Your Own Data Sources**: See `src/cascade/defs/ingestion/`
5. **Create New dbt Models**: See `transforms/dbt/models/`
6. **Build Superset Dashboards**: http://localhost:8088

## Getting Help

- **Architecture Questions**: See [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Branching Workflow**: See [NESSIE_WORKFLOW.md](./NESSIE_WORKFLOW.md)
- **Issues**: Open an issue on GitHub

Happy data engineering!

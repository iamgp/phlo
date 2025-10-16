# Quick Start: Nightscout Glucose Pipeline

5-minute guide to run the complete pipeline locally.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ with `uv` installed
- 10GB free disk space

## Step 1: Start Infrastructure (2 minutes)

```bash
cd /path/to/cascade

# Start all services
docker-compose up -d postgres minio dagster-daemon marquez

# Verify services are running
docker-compose ps
```

Expected output:
```
postgres          Up
minio             Up
dagster-daemon    Up
marquez           Up
```

## Step 2: Initialize Storage (1 minute)

```bash
# Create data directories
mkdir -p data/lake/raw/nightscout
mkdir -p data/lake/curated

# Create Postgres schemas
docker-compose exec postgres psql -U lakehouse -d lakehouse -c "
  CREATE SCHEMA IF NOT EXISTS staging;
  CREATE SCHEMA IF NOT EXISTS intermediate;
  CREATE SCHEMA IF NOT EXISTS curated;
  CREATE SCHEMA IF NOT EXISTS marts;
"
```

## Step 3: Install Dependencies (1 minute)

```bash
cd dagster
uv pip install -e .
```

## Step 4: Run Pipeline (1 minute)

```bash
# Start Dagster UI
dagster dev

# Open browser: http://localhost:3070
```

In Dagster UI:
1. Click **Assets** tab
2. Search for `nightscout`
3. Select all Nightscout assets
4. Click **Materialize selected**

Watch the pipeline execute:
```
raw_nightscout_entries → processed_nightscout_entries →
stg_nightscout_glucose → int_glucose_enriched →
fact_glucose_readings → mart_glucose_overview
```

## Step 5: View Results

### Check Data in DuckDB

```bash
duckdb

D SELECT count(*) FROM read_parquet('data/lake/raw/nightscout/*.parquet');
D SELECT * FROM read_parquet('data/lake/raw/nightscout/*.parquet') LIMIT 5;
```

### Check Marts in Postgres

```bash
docker-compose exec postgres psql -U lakehouse -d lakehouse

lakehouse=# SELECT * FROM marts.mart_glucose_overview ORDER BY reading_date DESC LIMIT 5;
```

### View Lineage in Marquez

Open http://localhost:3000 and search for `nightscout` namespace.

## What Just Happened?

1. **Ingestion**: Fetched 2016 glucose readings (7 days) from Nightscout API
2. **Storage**: Converted JSON → Parquet, compressed with ZSTD (90% size reduction)
3. **Staging**: Created typed view over raw Parquet files
4. **Transformation**: Enriched with time-based dimensions and glucose categories
5. **Aggregation**: Calculated daily metrics (time in range, estimated A1C)
6. **Marts**: Loaded denormalized tables into Postgres for BI

## Next Steps

- **Schedule Pipeline**: See `dagster/schedules/nightscout.py` for 30-minute refresh
- **Add Validations**: Run `validate_glucose_enriched` asset to check data quality
- **Build Dashboard**: Import `superset/dashboards/glucose_monitoring.json` into Superset
- **Read Full Guide**: See `NIGHTSCOUT_GLUCOSE_PIPELINE.md` for detailed explanation

## Troubleshooting

### "Cannot connect to Postgres"
```bash
# Check Postgres is running
docker-compose ps postgres

# Check connection
docker-compose exec postgres psql -U lakehouse -d lakehouse -c "SELECT 1;"
```

### "No Parquet files found"
```bash
# Check raw data exists
ls -lh data/lake/raw/nightscout/

# Re-run ingestion asset
dagster asset materialize -m dagster.repository -a raw_nightscout_entries
```

### "dbt models fail"
```bash
# Test dbt connection
cd dbt
dbt debug --profiles-dir profiles/

# Run single model
dbt run --select stg_nightscout_glucose --profiles-dir profiles/
```

## Cleanup

```bash
# Stop services
docker-compose down

# Remove data (optional)
rm -rf data/lake/raw/nightscout
rm -rf volumes/postgres
```

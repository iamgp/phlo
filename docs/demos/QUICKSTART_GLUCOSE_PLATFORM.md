# Glucose Platform Quick Start

**Get your phlo-powered glucose monitoring platform running in 15 minutes**

---

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Git

---

## Step 1: Clone and Setup (2 minutes)

```bash
# Clone the repository
git clone https://github.com/yourusername/phlo.git
cd phlo

# Install phlo
pip install -e ".[dev]"

# Verify installation
phlo --version
```

---

## Step 2: Start Services (3 minutes)

```bash
# Start all required services
docker compose up -d

# Services started:
# ✓ MinIO (S3 storage) - http://localhost:9001
# ✓ Nessie (catalog) - http://localhost:19120
# ✓ Trino (query engine) - http://localhost:8080
# ✓ PostgreSQL (BI layer) - localhost:5432
# ✓ Dagster (orchestration) - http://localhost:3000
# ✓ PostgREST (API) - http://localhost:3001
# ✓ Superset (dashboards) - http://localhost:8088

# Check services are healthy
docker compose ps
```

---

## Step 3: Initialize Catalog (1 minute)

```bash
# Create dev and main branches
dagster asset materialize -m phlo --select create_dev_branch
dagster asset materialize -m phlo --select create_main_branch

# Verify branches exist
curl http://localhost:19120/api/v1/trees
```

---

## Step 4: Run Ingestion (5 minutes)

```bash
# Open Dagster UI
open http://localhost:3000

# Or use CLI to materialize the glucose ingestion asset
dagster asset materialize -m phlo \
    --select glucose_entries \
    --partition $(date -d "yesterday" +%Y-%m-%d)

# This will:
# 1. Fetch glucose data from Nightscout API
# 2. Validate with Pandera schema
# 3. Stage to S3/MinIO
# 4. Merge to Iceberg table on 'dev' branch
```

**Dagster UI Flow:**
1. Navigate to: Assets → nightscout → glucose_entries
2. Click "Materialize"
3. Select partition: yesterday's date
4. Click "Materialize selected"
5. Watch the run in real-time

---

## Step 5: Transform Data (3 minutes)

```bash
# Run dbt transformations
cd transforms/dbt

# Bronze layer (staging)
dbt run --models bronze.stg_glucose_entries

# Silver layer (facts)
dbt run --models silver.fct_glucose_readings

# Gold layer (aggregates)
dbt run --models gold.fct_daily_glucose_metrics

# Marts (PostgreSQL)
dbt run --models marts_postgres.mrt_glucose_overview

# Or run all layers at once
dbt run --models +mrt_glucose_overview
```

---

## Step 6: Access the Data (1 minute)

### Via REST API (PostgREST)

```bash
# Get latest 5 days of glucose data
curl 'http://localhost:3001/mrt_glucose_overview?order=reading_date.desc&limit=5'

# Response:
[
  {
    "reading_date": "2024-01-20",
    "avg_glucose_mg_dl": 138.4,
    "time_in_range_pct": 72.5,
    "estimated_a1c_pct": 6.62,
    "diabetes_management_rating": "Good"
  },
  ...
]
```

### Via GraphQL (Hasura)

```bash
# Open Hasura console
open http://localhost:8081

# Run this query:
query {
  mrt_glucose_overview(order_by: {reading_date: desc}, limit: 5) {
    reading_date
    avg_glucose_mg_dl
    time_in_range_pct
    diabetes_management_rating
  }
}
```

### Via DuckDB (Analysts)

```python
import duckdb

con = duckdb.connect()
con.execute("INSTALL iceberg; LOAD iceberg;")

# Query Iceberg tables directly
result = con.execute("""
    SELECT
        date_trunc('day', reading_timestamp) as date,
        avg(glucose_mg_dl) as avg_glucose,
        count(*) as readings
    FROM iceberg_scan('s3://phlo-data/iceberg/glucose_entries')
    WHERE reading_timestamp >= current_date - interval '7 days'
    GROUP BY date
    ORDER BY date DESC
""").df()

print(result)
```

### Via Superset Dashboard

```bash
# Open Superset
open http://localhost:8088

# Login (default):
# Username: admin
# Password: admin

# Navigate to:
# Dashboards → Glucose Monitoring
```

---

## Architecture Overview

```
Nightscout API
    ↓
[DLT Pipeline] ← @phlo_ingestion decorator
    ↓
S3/MinIO (staging)
    ↓
Iceberg Table (dev branch)
    ↓
dbt Transformations
  ├─ Bronze: stg_glucose_entries
  ├─ Silver: fct_glucose_readings
  ├─ Gold: fct_daily_glucose_metrics
  └─ Marts: mrt_glucose_overview
    ↓
PostgreSQL
    ↓
┌────────┬──────────┬──────────┬───────────┐
PostgREST  Hasura   Superset   DuckDB
(REST)   (GraphQL) (Dashboards) (Analysts)
```

---

## Understanding the Pipeline

### 1. Ingestion Asset (60 lines)

**File:** `src/phlo/defs/ingestion/nightscout/glucose.py`

```python
@phlo_ingestion(
    table_name="glucose_entries",
    unique_key="_id",
    validation_schema=RawGlucoseEntries,
    group="nightscout",
    cron="0 */1 * * *",  # Hourly
)
def glucose_entries(partition_date: str):
    """Ingest glucose data from Nightscout API."""
    source = rest_api({
        "client": {"base_url": "https://gwp-diabetes.fly.dev/api/v1"},
        "resources": [{
            "name": "entries",
            "endpoint": {
                "path": "entries.json",
                "params": {
                    "count": 10000,
                    "find[dateString][$gte]": f"{partition_date}T00:00:00.000Z",
                    "find[dateString][$lt]": f"{partition_date}T23:59:59.999Z",
                },
            },
        }],
    })
    return source
```

**What the decorator handles:**
- ✅ Creates Iceberg table from Pandera schema
- ✅ Validates all incoming data
- ✅ Manages dev/main branches
- ✅ Handles deduplication
- ✅ Tracks metadata and lineage

### 2. Validation Schema

**File:** `src/phlo/schemas/glucose.py`

```python
class RawGlucoseEntries(DataFrameModel):
    _id: str = Field(nullable=False, unique=True)
    sgv: int = Field(ge=1, le=1000, nullable=False)
    date: int = Field(nullable=False)
    direction: str | None = Field(
        isin=["Flat", "FortyFiveUp", "SingleUp", "DoubleUp",
              "FortyFiveDown", "SingleDown", "DoubleDown", "NONE"],
        nullable=True
    )
```

### 3. dbt Transformations

**Silver Layer:** Add business logic

```sql
-- transforms/dbt/models/silver/fct_glucose_readings.sql
select
    entry_id,
    glucose_mg_dl,
    reading_timestamp,

    -- Time dimensions
    extract(hour from reading_timestamp) as hour_of_day,
    day_of_week(reading_timestamp) as day_of_week,

    -- Glucose categories (ADA guidelines)
    case
        when glucose_mg_dl < 70 then 'hypoglycemia'
        when glucose_mg_dl between 70 and 180 then 'in_range'
        when glucose_mg_dl > 180 then 'hyperglycemia'
    end as glucose_category,

    -- Time in range flag
    case when glucose_mg_dl between 70 and 180 then 1 else 0 end as is_in_range

from {{ ref('stg_glucose_entries') }}
```

**Gold Layer:** Daily aggregates

```sql
-- transforms/dbt/models/gold/fct_daily_glucose_metrics.sql
select
    reading_date,
    count(*) as reading_count,
    avg(glucose_mg_dl) as avg_glucose_mg_dl,

    -- Time in range (key diabetes metric)
    round(100.0 * sum(is_in_range) / count(*), 1) as time_in_range_pct,

    -- Estimated A1C (GMI formula)
    round(3.31 + (0.02392 * avg(glucose_mg_dl)), 2) as estimated_a1c_pct

from {{ ref('fct_glucose_readings') }}
group by reading_date
```

---

## Run the Interactive Demo

```bash
# Install demo dependencies
pip install rich requests

# Run the full demo
python examples/glucose_platform_demo.py

# Or run specific sections
python examples/glucose_platform_demo.py --demo ingestion
python examples/glucose_platform_demo.py --demo analytics
python examples/glucose_platform_demo.py --demo api
```

---

## Daily Operations

### Schedule Automatic Runs

```bash
# Using Dagster schedules (already configured)
# Glucose ingestion runs hourly automatically

# Or manually trigger for a specific date
dagster asset materialize -m phlo \
    --select glucose_entries \
    --partition 2024-01-20
```

### Run dbt Incrementally

```bash
cd transforms/dbt

# Only process new/modified data
dbt run --select fct_daily_glucose_metrics+ --full-refresh false
```

### Merge dev → main

```bash
# After validating data quality on dev branch
dagster asset materialize -m phlo --select merge_dev_to_main

# Now publish to PostgreSQL from main branch
dagster asset materialize -m phlo --select publish_glucose_to_postgres
```

### Monitor Pipeline Health

```bash
# Open Dagster UI
open http://localhost:3000

# Check:
# - Asset freshness (is data up to date?)
# - Data quality checks (are validations passing?)
# - Run history (any failures?)
```

---

## Common Queries

### Get Weekly Summary

```bash
curl 'http://localhost:3001/mrt_glucose_overview?reading_date=gte.2024-01-14&reading_date=lte.2024-01-20&order=reading_date.desc'
```

### Find Best Days

```bash
# Days with >70% time in range
curl 'http://localhost:3001/mrt_glucose_overview?time_in_range_pct=gte.70&order=time_in_range_pct.desc'
```

### Check Recent A1C Trend

```bash
curl 'http://localhost:3001/mrt_glucose_overview?select=reading_date,estimated_a1c_pct&order=reading_date.desc&limit=30'
```

---

## Extending the Platform

### Add a New Data Source

1. **Define schema** (`src/phlo/schemas/medications.py`)

```python
class RawMedicationEntries(DataFrameModel):
    _id: str = Field(nullable=False, unique=True)
    medication_name: str = Field(nullable=False)
    dosage_mg: float = Field(ge=0)
    administered_at: datetime = Field(nullable=False)
```

2. **Create ingestion asset** (`src/phlo/defs/ingestion/nightscout/medications.py`)

```python
@phlo_ingestion(
    table_name="medication_entries",
    unique_key="_id",
    validation_schema=RawMedicationEntries,
    group="nightscout",
)
def medication_entries(partition_date: str):
    # Your ingestion logic
    pass
```

3. **Add dbt models** (`transforms/dbt/models/silver/fct_medications.sql`)

```sql
select
    _id as medication_id,
    medication_name,
    dosage_mg,
    administered_at
from {{ ref('stg_medication_entries') }}
```

4. **Run the pipeline**

```bash
dagster asset materialize -m phlo --select medication_entries
dbt run --models fct_medications
```

---

## Troubleshooting

### Services won't start

```bash
# Check for port conflicts
docker compose ps
docker compose logs

# Restart specific service
docker compose restart minio
```

### Ingestion fails

```bash
# Check Dagster run logs
# Navigate to: Assets → glucose_entries → Recent runs → View logs

# Common issues:
# - Network connectivity to Nightscout API
# - MinIO credentials incorrect
# - Nessie catalog not initialized
```

### dbt models fail

```bash
# Check dbt logs
cd transforms/dbt
dbt run --models fct_glucose_readings --full-refresh

# Common issues:
# - Source table doesn't exist (run ingestion first)
# - Catalog not configured properly
# - Schema mismatch
```

### API returns no data

```bash
# Verify data exists in PostgreSQL
docker compose exec postgres psql -U postgres -c "SELECT count(*) FROM mrt_glucose_overview"

# If empty, run publishing step
dagster asset materialize -m phlo --select publish_glucose_to_postgres
```

---

## Next Steps

1. **Read the comprehensive guide**
   - `docs/demos/GLUCOSE_PLATFORM_DEMO.md` - Full deep dive

2. **Explore the codebase**
   - `src/phlo/ingestion/decorator.py` - How @phlo_ingestion works
   - `src/phlo/schemas/glucose.py` - Validation schemas
   - `transforms/dbt/models/` - All dbt transformations

3. **Build your own pipeline**
   - Follow the "Extending the Platform" pattern
   - Add medications, meals, exercise, etc.
   - Join multiple data sources

4. **Deploy to production**
   - Configure cloud storage (AWS S3, GCS, Azure Blob)
   - Set up authentication (JWT for PostgREST)
   - Enable monitoring and alerting
   - Implement backup strategies

---

## Key Takeaways

✅ **60 lines of code** (vs 270+ traditional)
✅ **Built-in validation** with Pandera schemas
✅ **Git-like branching** for safe development
✅ **Auto-generated APIs** from dbt models
✅ **Production-ready** with quality gates

**You just built a modern data lakehouse in 15 minutes!** 🎉

---

## Resources

- **Documentation:** `/docs/`
- **Blog Series:** `/docs/blog/` (12 articles)
- **Workflow Guide:** `/docs/guides/workflow-development.md`
- **Package Plan:** `/INSTALLABLE_PACKAGE_PLAN.md`

---

**Questions?** Check the full demo guide or explore the example code!

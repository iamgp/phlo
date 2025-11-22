# Building a Phlo-Powered Glucose Monitoring Platform

**A Complete Demonstration of Modern Data Platform Engineering**

This guide demonstrates how to build a production-ready glucose monitoring platform using Phlo's modern data lakehouse architecture. We'll transform raw API data into actionable insights with just ~60 lines of code per pipeline component.

---

## Table of Contents

1. [Platform Overview](#platform-overview)
2. [Architecture Deep Dive](#architecture-deep-dive)
3. [Component Breakdown](#component-breakdown)
4. [Setting Up the Platform](#setting-up-the-platform)
5. [Data Flow Walkthrough](#data-flow-walkthrough)
6. [Extending the Platform](#extending-the-platform)
7. [Best Practices](#best-practices)

---

## Platform Overview

### What We're Building

A **complete glucose monitoring platform** that:
- Ingests CGM (Continuous Glucose Monitor) data from Nightscout API
- Validates data quality at every stage
- Transforms raw readings into actionable metrics
- Provides SQL/GraphQL APIs for data access
- Powers real-time dashboards for diabetes management

### The Phlo Advantage

**Traditional Approach:** 270+ lines of boilerplate per ingestion asset
**Phlo Approach:** ~60 lines with declarative decorators

**What Phlo Handles for You:**
- ✅ Schema generation (Pandera → PyIceberg)
- ✅ Data validation and quality checks
- ✅ Git-like branching for data (dev/prod isolation)
- ✅ ACID transactions with Apache Iceberg
- ✅ Automatic deduplication
- ✅ Metadata tracking and lineage
- ✅ Error handling and retries

---

## Architecture Deep Dive

### Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Ingestion Layer                     │
├─────────────────────────────────────────────────────────────┤
│ Nightscout API → DLT (rest_api) → S3/MinIO (Parquet)        │
│ Validation: Pandera schemas enforce data quality            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Storage Layer                           │
├─────────────────────────────────────────────────────────────┤
│ Apache Iceberg Tables (ACID, Time Travel, Schema Evolution) │
│ Project Nessie Catalog (Git-like branching: dev/main)       │
│ MinIO Object Storage (S3-compatible)                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Transformation Layer (dbt)                  │
├─────────────────────────────────────────────────────────────┤
│ Bronze → Staging (stg_glucose_entries)                      │
│ Silver → Facts (fct_glucose_readings) + enrichment          │
│ Gold → Aggregates (fct_daily_glucose_metrics)               │
│ Marts → Business views (mrt_glucose_overview)               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Publishing Layer                         │
├─────────────────────────────────────────────────────────────┤
│ PostgreSQL (for BI tools and APIs)                          │
│ Quality Gates: Pandera validation before publish            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      API & Analytics Layer                   │
├─────────────────────────────────────────────────────────────┤
│ PostgREST → Auto-generated REST API                         │
│ Hasura → GraphQL API with real-time subscriptions           │
│ Superset → Interactive dashboards                           │
│ DuckDB → Ad-hoc analyst queries (direct Iceberg access)     │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Diagram

```
External System          Phlo Platform                   End Users
─────────────────       ───────────────────             ──────────

Nightscout API
     │
     │ HTTP GET
     ↓
┌─────────────────┐
│  DLT Pipeline   │  ← @phlo_ingestion decorator
│  (rest_api)     │    Handles: fetch, stage, validate
└────────┬────────┘
         │
         │ Write Parquet
         ↓
┌─────────────────┐
│ S3/MinIO Staging│  ← Temporary landing zone
└────────┬────────┘
         │
         │ PyIceberg Merge
         ↓
┌─────────────────┐
│  Iceberg Table  │  ← glucose_entries (raw)
│   (dev branch)  │    ACID transactions, deduplication
└────────┬────────┘
         │
         │ dbt models
         ↓
┌─────────────────┐
│ Silver Tables   │  ← fct_glucose_readings
│  (enriched)     │    + time dimensions
│                 │    + glucose categories
│                 │    + rate of change
└────────┬────────┘
         │
         │ dbt aggregations
         ↓
┌─────────────────┐
│  Gold Tables    │  ← fct_daily_glucose_metrics
│  (aggregated)   │    Daily averages, time in range
└────────┬────────┘
         │
         │ Publish to PostgreSQL
         ↓
┌─────────────────┐
│  Mart Tables    │  ← mrt_glucose_overview
│   (PostgreSQL)  │    Business-ready views
└────────┬────────┘
         │
         ├──────────────┬──────────────┬──────────────┐
         ↓              ↓              ↓              ↓
    PostgREST      Hasura         Superset      Analysts
    (REST API)   (GraphQL)      (Dashboards)   (DuckDB)
```

---

## Component Breakdown

### 1. Ingestion Layer (60 lines)

**File:** `src/phlo/defs/ingestion/nightscout/glucose.py`

```python
@phlo_ingestion(
    table_name="glucose_entries",
    unique_key="_id",
    validation_schema=RawGlucoseEntries,  # Pandera schema
    group="nightscout",
    cron="0 */1 * * *",  # Run hourly
    freshness_hours=(1, 24),
)
def glucose_entries(partition_date: str):
    """
    Ingest glucose data from Nightscout API.

    The @phlo_ingestion decorator handles:
    - Creating Iceberg table schema from Pandera
    - Branch management (writes to dev branch)
    - DLT pipeline orchestration
    - Validation execution
    - Idempotent merges (safe to re-run)
    - Automatic deduplication by _id
    """
    start_time_iso = f"{partition_date}T00:00:00.000Z"
    end_time_iso = f"{partition_date}T23:59:59.999Z"

    source = rest_api({
        "client": {
            "base_url": "https://gwp-diabetes.fly.dev/api/v1",
        },
        "resources": [{
            "name": "entries",
            "endpoint": {
                "path": "entries.json",
                "params": {
                    "count": 10000,
                    "find[dateString][$gte]": start_time_iso,
                    "find[dateString][$lt]": end_time_iso,
                },
            },
        }],
    })

    return source
```

**What happens behind the scenes:**

1. **Schema Creation** (first run only)
   - Decorator reads `RawGlucoseEntries` Pandera schema
   - Converts to PyIceberg schema
   - Creates table in Nessie catalog on `dev` branch

2. **Data Fetch**
   - DLT calls Nightscout API with date filters
   - Fetches all glucose readings for the partition date

3. **Validation**
   - Pandera validates against `RawGlucoseEntries` schema
   - Checks: glucose range (1-1000), valid directions, non-null IDs
   - **Blocks bad data before it reaches the lake**

4. **Staging**
   - DLT writes validated data to S3 as Parquet
   - Path: `s3://phlo-data/dlt_staging/glucose_entries/YYYY-MM-DD/`

5. **Merge to Iceberg**
   - PyIceberg reads staged Parquet
   - Merges to `glucose_entries` table using `_id` as unique key
   - Deduplicates: if `_id` exists, updates the row
   - ACID transaction ensures consistency

6. **Metadata Tracking**
   - Adds `_phlo_ingested_at` timestamp
   - Records lineage in Dagster
   - Updates table statistics in Nessie

### 2. Data Validation Layer

**File:** `src/phlo/schemas/glucose.py`

Three schemas for different pipeline stages:

#### Raw Schema (Ingestion)
```python
class RawGlucoseEntries(DataFrameModel):
    """Validates data at ingestion time."""

    _id: str = Field(
        nullable=False,
        unique=True,
        description="Nightscout entry ID"
    )

    sgv: int = Field(
        ge=1,
        le=1000,  # Wide range for raw data
        nullable=False,
        description="Sensor glucose value in mg/dL"
    )

    date: int = Field(
        nullable=False,
        description="Unix timestamp in milliseconds"
    )

    direction: str | None = Field(
        isin=["Flat", "FortyFiveUp", "SingleUp",
              "DoubleUp", "FortyFiveDown", "SingleDown",
              "DoubleDown", "NONE"],
        nullable=True,
    )
```

#### Fact Schema (Transformed)
```python
class FactGlucoseReadings(DataFrameModel):
    """Validates enriched data with business logic."""

    glucose_mg_dl: int = Field(
        ge=20,   # Physiologically valid minimum
        le=600,  # Maximum CGM reading
        nullable=False,
        metadata={"severity": "error"}  # Blocks promotion
    )

    glucose_category: str = Field(
        isin=["hypoglycemia", "in_range",
              "hyperglycemia_mild", "hyperglycemia_severe"],
        nullable=False,
        metadata={"severity": "warning"}
    )

    is_in_range: int = Field(
        isin=[0, 1],
        nullable=False,
        description="70-180 mg/dL target range"
    )
```

#### Daily Metrics Schema (Aggregated)
```python
class FactDailyGlucoseMetrics(DataFrameModel):
    """Validates daily aggregations."""

    time_in_range_pct: float | None = Field(
        ge=0,
        le=100,
        nullable=True,
        metadata={"severity": "error"}
    )

    estimated_a1c_pct: float | None = Field(
        ge=0,
        le=20,
        nullable=True,
        description="GMI approximation"
    )
```

**Severity Levels:**
- `error` → Blocks promotion from dev to main branch
- `warning` → Logs alert but allows promotion

### 3. Transformation Layer (dbt)

#### Bronze → Staging
**File:** `transforms/dbt/models/bronze/stg_glucose_entries.sql`

```sql
-- Clean and standardize raw data
select
    _id as entry_id,
    sgv as glucose_mg_dl,
    cast(from_unixtime(date / 1000) as timestamp) as reading_timestamp,
    date_string as timestamp_iso,
    direction,
    coalesce(direction, 'NONE') as trend,
    device
from {{ source('raw_iceberg', 'glucose_entries') }}
where sgv is not null
```

#### Silver → Facts (Business Logic)
**File:** `transforms/dbt/models/silver/fct_glucose_readings.sql`

```sql
-- Enrich with calculated fields
select
    entry_id,
    glucose_mg_dl,
    reading_timestamp,

    -- Time dimensions
    date_trunc('day', reading_timestamp) as reading_date,
    extract(hour from reading_timestamp) as hour_of_day,
    day_of_week(reading_timestamp) as day_of_week,
    format_datetime(reading_timestamp, 'EEEE') as day_name,

    -- Blood sugar categories (ADA guidelines)
    case
        when glucose_mg_dl < 70 then 'hypoglycemia'
        when glucose_mg_dl between 70 and 180 then 'in_range'
        when glucose_mg_dl between 181 and 250 then 'hyperglycemia_mild'
        when glucose_mg_dl > 250 then 'hyperglycemia_severe'
    end as glucose_category,

    -- Time in range flag
    case
        when glucose_mg_dl between 70 and 180 then 1
        else 0
    end as is_in_range,

    -- Rate of change (vs. previous reading)
    glucose_mg_dl - lag(glucose_mg_dl) over (
        partition by device
        order by reading_timestamp
    ) as glucose_change_mg_dl

from {{ ref('stg_glucose_entries') }}
```

#### Gold → Aggregates
**File:** `transforms/dbt/models/gold/fct_daily_glucose_metrics.sql`

```sql
-- Daily rollups and KPIs
select
    reading_date,
    format_datetime(reading_date, 'EEEE') as day_name,

    -- Daily statistics
    count(*) as reading_count,
    round(avg(glucose_mg_dl), 1) as avg_glucose_mg_dl,
    min(glucose_mg_dl) as min_glucose_mg_dl,
    max(glucose_mg_dl) as max_glucose_mg_dl,
    round(stddev(glucose_mg_dl), 1) as stddev_glucose_mg_dl,

    -- Time in range metrics (key diabetes management metric)
    round(100.0 * sum(is_in_range) / count(*), 1) as time_in_range_pct,
    round(100.0 * sum(case when glucose_mg_dl < 70 then 1 else 0 end) / count(*), 1)
        as time_below_range_pct,
    round(100.0 * sum(case when glucose_mg_dl > 180 then 1 else 0 end) / count(*), 1)
        as time_above_range_pct,

    -- Glucose Management Indicator (GMI)
    -- Approximates A1C from average glucose
    -- Formula: GMI = 3.31 + 0.02392 * avg_glucose
    round(3.31 + (0.02392 * avg(glucose_mg_dl)), 2) as estimated_a1c_pct

from {{ ref('fct_glucose_readings') }}
group by reading_date
order by reading_date desc
```

#### Marts → PostgreSQL (BI Layer)
**File:** `transforms/dbt/models/marts_postgres/mrt_glucose_overview.sql`

```sql
-- Business-ready view for dashboards
select
    reading_date,
    day_name,
    reading_count,
    avg_glucose_mg_dl,
    time_in_range_pct,
    estimated_a1c_pct,

    -- Contextual indicators
    case
        when time_in_range_pct >= 70 then 'Excellent'
        when time_in_range_pct >= 50 then 'Good'
        when time_in_range_pct >= 30 then 'Needs Improvement'
        else 'Critical'
    end as diabetes_management_rating

from {{ ref('fct_daily_glucose_metrics') }}
where reading_count > 12  -- At least 1 hour of data
```

### 4. Publishing & API Layer

#### PostgreSQL Publishing
**Dagster Asset:** Publishes curated marts to PostgreSQL

```python
@asset(
    deps=[AssetKey("mrt_glucose_overview")],
    group_name="publishing",
)
def publish_glucose_to_postgres():
    """
    Publish glucose marts to PostgreSQL for BI tools.

    Flow:
    1. Read from Iceberg (mrt_glucose_overview)
    2. Validate with Pandera
    3. Truncate/load to PostgreSQL
    """
    # Implementation handled by framework
```

#### PostgREST API (Auto-generated)

Once published to PostgreSQL, PostgREST automatically creates a REST API:

```bash
# Get latest glucose overview
GET /mrt_glucose_overview?order=reading_date.desc&limit=7

# Filter by date range
GET /mrt_glucose_overview?reading_date=gte.2024-01-01&reading_date=lte.2024-01-31

# Get days with excellent management
GET /mrt_glucose_overview?diabetes_management_rating=eq.Excellent

# Aggregate: average time in range by day of week
GET /mrt_glucose_overview?select=day_name,avg(time_in_range_pct)&group_by=day_name
```

#### Hasura GraphQL API

```graphql
query GetRecentGlucose {
  mrt_glucose_overview(
    order_by: { reading_date: desc }
    limit: 30
  ) {
    reading_date
    avg_glucose_mg_dl
    time_in_range_pct
    estimated_a1c_pct
    diabetes_management_rating
  }
}
```

### 5. Analytics & Visualization

#### DuckDB for Analysts
**File:** `examples/analyst_duckdb_demo.py`

```python
import duckdb

# Analysts can query Iceberg tables directly via DuckDB
con = duckdb.connect()

# Install Iceberg extension
con.execute("INSTALL iceberg; LOAD iceberg;")

# Query directly from S3/MinIO
result = con.execute("""
    SELECT
        date_trunc('day', reading_timestamp) as date,
        avg(glucose_mg_dl) as avg_glucose,
        count(*) as reading_count
    FROM iceberg_scan('s3://phlo-data/iceberg/glucose_entries')
    WHERE reading_timestamp >= current_date - interval '30 days'
    GROUP BY date
    ORDER BY date DESC
""").fetchall()
```

**No Docker access needed!** Analysts can:
- Query Iceberg tables directly
- No need for PostgreSQL access
- Full power of SQL on raw lakehouse data
- Sub-second query performance

#### Superset Dashboards

Pre-built dashboard includes:
- **Glucose Trends:** 30-day rolling average
- **Time in Range:** Daily percentages with ADA targets
- **Hourly Patterns:** Identify problematic times of day
- **A1C Estimation:** Track GMI over time
- **Hypoglycemia Alerts:** Days with low glucose events

---

## Setting Up the Platform

### Prerequisites

```bash
# Required services (via Docker Compose)
docker compose up -d

# Services started:
# - MinIO (S3-compatible storage)
# - Nessie (Iceberg catalog)
# - Trino (SQL query engine)
# - PostgreSQL (BI/API layer)
# - PostgREST (REST API)
# - Superset (Dashboards)
```

### Step-by-Step Setup

#### 1. Install Phlo

```bash
# Install in development mode
cd /home/user/cascade
pip install -e ".[dev]"

# Verify installation
phlo --version
```

#### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Required configuration:
NESSIE_URI=http://localhost:19120/api/v1
ICEBERG_WAREHOUSE_PATH=s3://phlo-data/iceberg/
AWS_S3_ENDPOINT=http://localhost:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin

# Nightscout API (optional for live data)
NIGHTSCOUT_URL=https://gwp-diabetes.fly.dev
```

#### 3. Initialize the Catalog

```bash
# Create Nessie branches
phlo nessie create-branch dev
phlo nessie create-branch main

# Verify branches
phlo nessie list-branches
```

#### 4. Run Initial Ingestion

```bash
# Materialize glucose ingestion for yesterday
dagster asset materialize -m phlo \
    --select glucose_entries \
    --partition 2024-01-15

# Check Dagster UI
open http://localhost:3000
```

#### 5. Run dbt Transformations

```bash
# Transform data through all layers
cd transforms/dbt
dbt run --models bronze.stg_glucose_entries
dbt run --models silver.fct_glucose_readings
dbt run --models gold.fct_daily_glucose_metrics
dbt run --models marts_postgres.mrt_glucose_overview

# Run data quality tests
dbt test --models fct_glucose_readings
```

#### 6. Publish to PostgreSQL

```bash
# Publish marts for BI/API consumption
dagster asset materialize -m phlo \
    --select publish_glucose_to_postgres
```

#### 7. Access the APIs

```bash
# PostgREST API
curl http://localhost:3001/mrt_glucose_overview?limit=5

# Response:
[
  {
    "reading_date": "2024-01-15",
    "avg_glucose_mg_dl": 142.3,
    "time_in_range_pct": 68.2,
    "estimated_a1c_pct": 6.72,
    "diabetes_management_rating": "Good"
  },
  ...
]
```

#### 8. View Dashboards

```bash
# Open Superset
open http://localhost:8088

# Login credentials (default):
# Username: admin
# Password: admin

# Navigate to: Dashboards → Glucose Monitoring
```

---

## Data Flow Walkthrough

### End-to-End Example: Single Glucose Reading

Let's trace a single glucose reading through the entire platform:

#### 1. API Response (Nightscout)

```json
{
  "_id": "65a1b2c3d4e5f6789",
  "sgv": 145,
  "date": 1705334400000,
  "dateString": "2024-01-15T14:00:00.000Z",
  "direction": "Flat",
  "device": "DexcomG6",
  "type": "sgv"
}
```

#### 2. DLT Staging (Parquet on S3)

```
s3://phlo-data/dlt_staging/glucose_entries/2024-01-15/
  └── entries_0_0.parquet
      └── Row: {
           "_id": "65a1b2c3d4e5f6789",
           "sgv": 145,
           "date": 1705334400000,
           ...
           "_phlo_ingested_at": "2024-01-15T14:05:23.123Z"
         }
```

#### 3. Validation (Pandera)

```python
# RawGlucoseEntries schema checks:
✓ _id is unique and non-null
✓ sgv (145) is between 1-1000
✓ date is valid timestamp
✓ direction ("Flat") is in allowed list
✓ _phlo_ingested_at is present
```

#### 4. Iceberg Merge (Raw Table)

```sql
-- PyIceberg operation
MERGE INTO dev.glucose_entries AS target
USING staged_data AS source
ON target._id = source._id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
```

**Result:** Single row in `dev.glucose_entries` Iceberg table

#### 5. dbt Bronze Layer

```sql
-- stg_glucose_entries.sql transformation
{
  "entry_id": "65a1b2c3d4e5f6789",
  "glucose_mg_dl": 145,
  "reading_timestamp": "2024-01-15 14:00:00",
  "timestamp_iso": "2024-01-15T14:00:00.000Z",
  "direction": "Flat",
  "trend": "Flat",
  "device": "DexcomG6"
}
```

#### 6. dbt Silver Layer (Enrichment)

```sql
-- fct_glucose_readings.sql adds calculations
{
  "entry_id": "65a1b2c3d4e5f6789",
  "glucose_mg_dl": 145,
  "reading_timestamp": "2024-01-15 14:00:00",
  "reading_date": "2024-01-15",

  -- Time dimensions
  "hour_of_day": 14,
  "day_of_week": 1,  # Monday
  "day_name": "Monday",

  -- Business logic
  "glucose_category": "in_range",  # 70-180 mg/dL
  "is_in_range": 1,

  -- Rate of change (vs previous reading at 13:55)
  "glucose_change_mg_dl": 3,  # +3 mg/dL in 5 minutes
  "minutes_since_last_reading": 5
}
```

#### 7. dbt Gold Layer (Daily Aggregation)

```sql
-- fct_daily_glucose_metrics.sql aggregates all readings for 2024-01-15
{
  "reading_date": "2024-01-15",
  "day_name": "Monday",
  "reading_count": 288,  # 288 readings in 24 hours (every 5 min)

  "avg_glucose_mg_dl": 142.3,
  "min_glucose_mg_dl": 68,
  "max_glucose_mg_dl": 201,
  "stddev_glucose_mg_dl": 24.7,

  "time_in_range_pct": 68.2,  # 68.2% of day in 70-180 range
  "time_below_range_pct": 4.5,
  "time_above_range_pct": 27.3,

  "estimated_a1c_pct": 6.72  # GMI calculation
}
```

#### 8. PostgreSQL Publishing

```sql
-- Truncate/load to mrt_glucose_overview table
INSERT INTO public.mrt_glucose_overview
SELECT
    reading_date,
    day_name,
    reading_count,
    avg_glucose_mg_dl,
    time_in_range_pct,
    estimated_a1c_pct,
    'Good' as diabetes_management_rating  -- 68.2% TIR
FROM iceberg.main.fct_daily_glucose_metrics
WHERE reading_date = '2024-01-15'
```

#### 9. API Response

```bash
# PostgREST API call
curl http://localhost:3001/mrt_glucose_overview?reading_date=eq.2024-01-15

# Response:
{
  "reading_date": "2024-01-15",
  "day_name": "Monday",
  "reading_count": 288,
  "avg_glucose_mg_dl": 142.3,
  "time_in_range_pct": 68.2,
  "estimated_a1c_pct": 6.72,
  "diabetes_management_rating": "Good"
}
```

#### 10. Dashboard Visualization

```
Superset Chart: Time in Range Trend
┌────────────────────────────────────────┐
│  Time in Range (7-day rolling avg)    │
├────────────────────────────────────────┤
│                                        │
│  80% ┤                    ╭───╮       │
│  70% ┤          ╭────────╮│   │       │  ← Jan 15: 68.2%
│  60% ┤     ╭────╯        ╰╯   ╰───    │
│  50% ┤─────╯                          │
│      └────────────────────────────────│
│       Jan 9  Jan 11  Jan 13  Jan 15   │
└────────────────────────────────────────┘
```

**Journey Complete:** From API reading to dashboard in ~5 minutes (hourly ingestion + transform + publish)

---

## Extending the Platform

### Adding a New Data Source

Example: Add medication tracking alongside glucose data

#### 1. Define Schema

```python
# src/phlo/schemas/medications.py
class RawMedicationEntries(DataFrameModel):
    """Schema for medication tracking data."""

    _id: str = Field(nullable=False, unique=True)
    medication_name: str = Field(nullable=False)
    dosage_mg: float = Field(ge=0, nullable=False)
    administered_at: datetime = Field(nullable=False)
    notes: str | None = Field(nullable=True)
```

#### 2. Create Ingestion Asset

```python
# src/phlo/defs/ingestion/nightscout/medications.py
@phlo_ingestion(
    table_name="medication_entries",
    unique_key="_id",
    validation_schema=RawMedicationEntries,
    group="nightscout",
    cron="0 */6 * * *",  # Every 6 hours
)
def medication_entries(partition_date: str):
    """Ingest medication tracking data."""
    source = rest_api({
        "client": {
            "base_url": "https://gwp-diabetes.fly.dev/api/v1",
        },
        "resources": [{
            "name": "treatments",
            "endpoint": {
                "path": "treatments.json",
                "params": {
                    "find[eventType]": "Insulin",
                    "find[created_at][$gte]": f"{partition_date}T00:00:00Z",
                },
            },
        }],
    })
    return source
```

#### 3. Create dbt Models

```sql
-- transforms/dbt/models/silver/fct_medications.sql
select
    _id as medication_id,
    medication_name,
    dosage_mg,
    administered_at,

    -- Join with glucose data
    date_trunc('hour', administered_at) as medication_hour

from {{ ref('stg_medication_entries') }}
```

```sql
-- transforms/dbt/models/gold/mrt_medication_effectiveness.sql
select
    m.medication_hour,
    m.medication_name,
    m.dosage_mg,

    -- Glucose before medication (1 hour window)
    avg(case when g.reading_timestamp between
            m.administered_at - interval '1 hour' and
            m.administered_at
         then g.glucose_mg_dl end) as glucose_before,

    -- Glucose after medication (3 hour window)
    avg(case when g.reading_timestamp between
            m.administered_at and
            m.administered_at + interval '3 hours'
         then g.glucose_mg_dl end) as glucose_after,

    -- Calculate effectiveness
    avg(glucose_before) - avg(glucose_after) as glucose_reduction

from {{ ref('fct_medications') }} m
left join {{ ref('fct_glucose_readings') }} g
    on date_trunc('day', m.administered_at) = g.reading_date
group by 1, 2, 3
```

#### 4. Run the Pipeline

```bash
# Materialize new asset
dagster asset materialize -m phlo --select medication_entries

# Run dbt transformations
dbt run --models fct_medications mrt_medication_effectiveness

# Publish to PostgreSQL
dagster asset materialize -m phlo --select publish_medications_to_postgres
```

**Result:** New API endpoint at `/mrt_medication_effectiveness` showing insulin effectiveness!

### Adding Custom Quality Checks

```python
# src/phlo/defs/quality/nightscout.py
from dagster import AssetCheckResult, asset_check

@asset_check(
    asset=AssetKey("fct_glucose_readings"),
    description="Ensure no data gaps > 30 minutes",
)
def check_glucose_data_continuity() -> AssetCheckResult:
    """
    Check that glucose readings are continuous (CGM should report every 5 min).
    """
    # Query Iceberg table
    df = iceberg_to_df("fct_glucose_readings", branch="dev")

    # Calculate gaps between readings
    df = df.sort_values('reading_timestamp')
    df['gap_minutes'] = df['reading_timestamp'].diff().dt.total_seconds() / 60

    # Find gaps > 30 minutes
    large_gaps = df[df['gap_minutes'] > 30]

    if len(large_gaps) > 0:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.WARN,
            metadata={
                "gap_count": len(large_gaps),
                "max_gap_minutes": large_gaps['gap_minutes'].max(),
            }
        )

    return AssetCheckResult(passed=True)
```

**Quality gates prevent bad data from reaching production!**

---

## Best Practices

### 1. Branch Strategy

```
main branch (production)
  ↑
  │ merge after validation
  │
dev branch (development)
  ↑
  │ write new data here
  │
feature branches (experimental)
  ↑
  │ test schema changes
```

**Workflow:**
1. Ingest data to `dev` branch
2. Run dbt transformations
3. Execute quality checks
4. If checks pass → merge `dev` to `main`
5. Publish from `main` to PostgreSQL

### 2. Data Quality Philosophy

**Multi-layered validation:**

```
┌─────────────────────────────────────┐
│  Layer 1: Ingestion Validation      │  ← Pandera on raw data
│  Severity: ERROR (blocks ingestion) │
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  Layer 2: Transformation Tests      │  ← dbt tests
│  Severity: WARN (logs issues)       │
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  Layer 3: Asset Checks              │  ← Custom Dagster checks
│  Severity: ERROR (blocks promotion) │
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  Layer 4: Publishing Validation     │  ← Pandera on marts
│  Severity: ERROR (blocks publish)   │
└─────────────────────────────────────┘
```

### 3. Performance Optimization

**Partitioning Strategy:**
```python
# Partition by date for time-series data
@phlo_ingestion(
    table_name="glucose_entries",
    partition_by="date(reading_timestamp)",  # Daily partitions
)
```

**Benefits:**
- Query pruning: `WHERE reading_date = '2024-01-15'` only scans 1 partition
- Faster incrementals: dbt only processes new partitions
- Time travel: `SELECT ... FOR VERSION AS OF 'tag-v1.0'`

**Incremental dbt Models:**
```sql
{{ config(
    materialized='incremental',
    unique_key='reading_date',
    incremental_strategy='merge'
) }}

select * from {{ ref('fct_glucose_readings') }}

{% if is_incremental() %}
    -- Only process new dates
    where reading_date > (select max(reading_date) from {{ this }})
{% endif %}
```

### 4. Monitoring & Alerting

**Key Metrics to Track:**

```python
# Dagster asset metadata
@asset
def glucose_entries():
    # ... ingestion logic ...

    return Output(
        value=df,
        metadata={
            "row_count": len(df),
            "date_range": f"{df['date'].min()} to {df['date'].max()}",
            "avg_glucose": df['sgv'].mean(),
            "null_count": df['sgv'].isnull().sum(),
        }
    )
```

**Freshness Monitoring:**
```python
@phlo_ingestion(
    freshness_hours=(1, 24),  # Expected: 1h, stale after 24h
)
```

**Dagster Sensors for Alerts:**
```python
@sensor(
    job=send_alert_job,
    minimum_interval_seconds=3600,  # Check hourly
)
def glucose_freshness_sensor(context):
    """Alert if glucose data is stale."""
    last_run = get_latest_asset_timestamp("glucose_entries")

    if (datetime.now() - last_run).total_seconds() > 3600:
        return RunRequest(
            run_config={
                "ops": {
                    "send_alert": {
                        "config": {
                            "message": "Glucose data is stale!"
                        }
                    }
                }
            }
        )
```

### 5. Cost Optimization

**S3 Lifecycle Policies:**
```python
# Move old partitions to cheaper storage
s3_lifecycle = {
    "Rules": [{
        "Id": "ArchiveOldPartitions",
        "Status": "Enabled",
        "Transitions": [
            {
                "Days": 90,
                "StorageClass": "GLACIER"  # Archive after 90 days
            }
        ]
    }]
}
```

**Iceberg Compaction:**
```python
# Consolidate small files for better performance
@schedule(cron_schedule="0 2 * * 0")  # Weekly at 2am
def compact_iceberg_tables():
    """Compact Iceberg tables to optimize reads."""
    table = catalog.load_table("glucose_entries")
    table.rewrite_data_files()
```

---

## Production Checklist

Before deploying to production:

- [ ] **Security**
  - [ ] Enable PostgREST JWT authentication
  - [ ] Configure MinIO access policies
  - [ ] Use secrets manager for API keys
  - [ ] Enable SSL/TLS for all services

- [ ] **Reliability**
  - [ ] Set up automated backups (Nessie catalog + S3)
  - [ ] Configure Dagster retry policies
  - [ ] Implement circuit breakers for API calls
  - [ ] Set up monitoring and alerting

- [ ] **Performance**
  - [ ] Enable Iceberg table partitioning
  - [ ] Configure dbt incremental models
  - [ ] Set up read replicas for PostgreSQL
  - [ ] Optimize Trino query performance

- [ ] **Data Quality**
  - [ ] Implement all required Pandera schemas
  - [ ] Add dbt tests for all models
  - [ ] Configure asset checks with appropriate severity
  - [ ] Set up data lineage tracking

- [ ] **Documentation**
  - [ ] Document API endpoints
  - [ ] Create runbooks for common issues
  - [ ] Document schema changes process
  - [ ] Create user guides for dashboards

---

## Summary

You've now seen how to build a **production-ready glucose monitoring platform** using Phlo:

### What We Built
- ✅ Automated ingestion from Nightscout API
- ✅ Multi-layered data validation with Pandera
- ✅ Bronze/Silver/Gold medallion architecture
- ✅ REST & GraphQL APIs (auto-generated)
- ✅ Interactive dashboards
- ✅ Git-like version control for data
- ✅ ACID transactions and time travel

### Code Reduction
- **Traditional:** 270+ lines per ingestion asset
- **Phlo:** 60 lines with `@phlo_ingestion`
- **Savings:** 78% less boilerplate

### Key Innovations
1. **Declarative pipelines** - Focus on business logic, not plumbing
2. **Schema-first development** - Validation catches issues early
3. **Branch-aware workflows** - Test safely before production
4. **Quality gates** - Bad data never reaches production
5. **Automatic lineage** - Understand data provenance

### Next Steps

1. **Explore the code**
   - `src/phlo/defs/ingestion/nightscout/` - Ingestion assets
   - `transforms/dbt/models/` - dbt transformations
   - `docs/guides/workflow-development.md` - Detailed guide

2. **Try it yourself**
   - Clone the repo
   - Run `docker compose up`
   - Materialize the glucose pipeline
   - Query the APIs

3. **Extend the platform**
   - Add new data sources (medications, exercise, meals)
   - Create custom dashboards
   - Build ML models on glucose data
   - Integrate with mobile apps

### Resources

- **Documentation:** `/docs/`
- **Blog Series:** `/docs/blog/` (12 articles on lakehouse concepts)
- **Example Workflows:** `/docs/guides/workflow-development.md`
- **Package Plan:** `/INSTALLABLE_PACKAGE_PLAN.md`

---

**Built with Phlo** - The Modern Data Lakehouse Platform

*Transform your data engineering from complex boilerplate to declarative pipelines.*

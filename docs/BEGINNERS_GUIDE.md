# Cascade Lakehouse Platform - Beginner's Guide

## Welcome! 👋

This guide is designed for **complete beginners** to data engineering. We'll explain every concept from the ground up, so you can understand how Cascade works and build your own data pipelines.

---

## Table of Contents

1. [What is a Data Lakehouse?](#what-is-a-data-lakehouse)
2. [Core Concepts Explained](#core-concepts-explained)
3. [How Cascade Works - The Big Picture](#how-cascade-works---the-big-picture)
4. [Understanding the Data Journey](#understanding-the-data-journey)
5. [Key Technologies Explained](#key-technologies-explained)
6. [Your First Look at Cascade](#your-first-look-at-cascade)
7. [Understanding the Example Pipeline](#understanding-the-example-pipeline)
8. [Common Workflows](#common-workflows)
9. [Next Steps](#next-steps)

---

## What is a Data Lakehouse?

### The Problem

Imagine you're running a company and you have data everywhere:
- Customer data in a database
- Website logs in files
- Sales data in spreadsheets
- Social media metrics from APIs

You need to:
1. **Collect** all this data in one place
2. **Transform** it into useful formats
3. **Analyze** it to make decisions
4. **Serve** it to dashboards and applications

### Traditional Approaches

**Data Warehouse:**
- Structured, organized, fast queries
- ❌ Expensive to store large amounts of data
- ❌ Rigid schemas - hard to change
- ❌ Can't handle unstructured data (images, logs, etc.)

**Data Lake:**
- Cheap storage, handles any data type
- ❌ Messy, hard to query
- ❌ No guarantees about data quality
- ❌ "Data swamp" problem

### The Lakehouse Solution

A **Data Lakehouse** combines the best of both:
- ✅ Cheap storage like a lake
- ✅ Fast queries like a warehouse
- ✅ ACID transactions (data consistency)
- ✅ Time travel (query historical data)
- ✅ Schema flexibility
- ✅ Works with any data type

**Cascade is a complete, ready-to-use Data Lakehouse platform.**

---

## Core Concepts Explained

### 1. Object Storage (MinIO)

Think of this as a **giant file system in the cloud**.

- Stores data as files (called "objects")
- Incredibly cheap and scalable
- Compatible with AWS S3 (the most popular cloud storage)
- In Cascade, we use MinIO (an open-source S3-compatible storage)

**Example:** Your glucose readings get saved as Parquet files in MinIO at `s3://lake/warehouse/raw/glucose_entries/`

### 2. Table Format (Apache Iceberg)

This is the **magic** that makes a data lake work like a database.

**Without Iceberg:**
- Files scattered everywhere
- No way to know which files belong to which "table"
- Can't update or delete data safely
- No schema enforcement

**With Iceberg:**
- Files organized into logical "tables"
- Metadata tracks which files belong to each table
- ACID transactions (all-or-nothing operations)
- Schema evolution (add columns safely)
- Time travel (see data from yesterday, last week, etc.)

**Analogy:** Iceberg is like a library catalog system. The books (data files) are stored on shelves (object storage), but the catalog tells you where everything is and keeps everything organized.

### 3. Catalog (Project Nessie)

This is like **Git for data**.

**What does it do?**
- Tracks versions of your tables
- Lets you create "branches" (dev, staging, production)
- Lets you "commit" changes
- Lets you "merge" branches
- Lets you roll back if something goes wrong

**Example Workflow:**
```
1. Create a "dev" branch
2. Test new data in dev
3. If it looks good, merge to "main" (production)
4. If something breaks, roll back to yesterday
```

### 4. Query Engine (Trino)

This is your **SQL interface** to the data.

- Trino is a distributed SQL engine
- Queries Iceberg tables as if they were database tables
- Can join data from multiple sources
- Scales to petabytes of data

**You write normal SQL:**
```sql
SELECT
    date,
    AVG(glucose_value) as avg_glucose
FROM raw.glucose_entries
WHERE date >= '2024-01-01'
GROUP BY date
```

### 5. Transformation Tool (dbt)

**dbt** = "data build tool"

This is how you **transform raw data into analytics-ready data**.

**Philosophy:**
- Write SQL SELECT statements (not complex ETL code)
- dbt handles the hard parts (dependencies, testing, documentation)
- Version control your transformations
- Test data quality automatically

**Example:**
```sql
-- models/silver/fct_glucose_readings.sql
SELECT
    id,
    date,
    glucose_value,
    -- Add calculated fields
    CASE
        WHEN glucose_value < 70 THEN 'Low'
        WHEN glucose_value > 180 THEN 'High'
        ELSE 'Normal'
    END as glucose_category
FROM {{ source('raw', 'glucose_entries') }}
```

### 6. Orchestration (Dagster)

**Dagster** is your **workflow manager**.

**Think of it as:**
- A to-do list that runs automatically
- Knows which tasks depend on which other tasks
- Runs tasks in the right order
- Retries if something fails
- Shows you what's happening

**Key Concept: Assets**

In Dagster, everything is an "asset" (a piece of data):
- `glucose_entries` - raw data from API
- `stg_glucose_entries` - cleaned data
- `fct_glucose_readings` - calculated metrics

Dagster knows:
- `stg_glucose_entries` depends on `glucose_entries`
- `fct_glucose_readings` depends on `stg_glucose_entries`

So it runs them in order automatically!

### 7. Data Layers (Bronze/Silver/Gold)

This is a **design pattern** for organizing data:

**Bronze Layer (Raw):**
- Data exactly as it came from the source
- Minimal or no transformation
- "Keep everything" philosophy
- Example: `raw.glucose_entries`

**Silver Layer (Cleaned):**
- Type conversions
- Standardization
- Data cleaning
- Deduplication
- Example: `silver.fct_glucose_readings`

**Gold Layer (Business):**
- Aggregations
- Business metrics
- Dimension tables
- Optimized for analytics
- Example: `gold.dim_date`

**Marts Layer (Published):**
- Final business-ready tables
- Optimized for BI tools
- Often copied to PostgreSQL for fast access
- Example: `marts.mrt_glucose_overview`

**Why this pattern?**
- ✅ Clear separation of concerns
- ✅ Easy to debug (check each layer)
- ✅ Reusable transformations
- ✅ Can rebuild downstream if needed

---

## How Cascade Works - The Big Picture

Let's trace a single piece of data through the entire system:

### Step 1: Data Arrives (Ingestion)

```
Nightscout API (glucose monitoring app)
    ↓
DLT (Data Load Tool) fetches the data
    ↓
Saves to MinIO as Parquet files (s3://lake/stage/glucose_*.parquet)
    ↓
PyIceberg registers files as an Iceberg table
    ↓
Nessie catalog records the table metadata
    ↓
Result: raw.glucose_entries table exists
```

**What just happened?**
- Your glucose reading is now stored as a Parquet file
- The Iceberg metadata points to that file
- The Nessie catalog knows the table exists
- You can now query it with SQL!

### Step 2: Data Gets Cleaned (Bronze Layer)

```
dbt runs: models/bronze/stg_glucose_entries.sql
    ↓
Trino reads from raw.glucose_entries
    ↓
SQL transformations apply:
    - Convert types (strings to timestamps)
    - Standardize column names
    - Remove duplicates
    ↓
Trino writes results to bronze.stg_glucose_entries
    ↓
Result: Clean, standardized data
```

### Step 3: Data Gets Enriched (Silver Layer)

```
dbt runs: models/silver/fct_glucose_readings.sql
    ↓
Trino reads from bronze.stg_glucose_entries
    ↓
SQL transformations apply:
    - Calculate rolling averages
    - Add glucose categories (Low/Normal/High)
    - Join with other tables if needed
    ↓
Trino writes results to silver.fct_glucose_readings
    ↓
Result: Analytics-ready fact table
```

### Step 4: Data Gets Published (Marts)

```
dbt runs: models/marts_postgres/mrt_glucose_overview.sql
    ↓
Trino reads from silver/gold layers
    ↓
Creates summary metrics:
    - Daily averages
    - Time in range percentages
    - Trend indicators
    ↓
Results copied to PostgreSQL marts schema
    ↓
Result: Fast BI-ready tables
```

### Step 5: Data Gets Visualized

```
Superset connects to PostgreSQL marts
    ↓
Dashboard queries mrt_glucose_overview
    ↓
Charts display:
    - Glucose trends over time
    - Daily statistics
    - Time in range pie chart
    ↓
Result: Beautiful, fast dashboards
```

### Step 6: Data Gets Served via API

```
User requests: GET /api/v1/glucose/readings?date=2024-11-05
    ↓
FastAPI authenticates user (JWT token)
    ↓
Queries Trino: SELECT * FROM silver.fct_glucose_readings WHERE date = '2024-11-05'
    ↓
Returns JSON response
    ↓
Result: Applications can access data programmatically
```

---

## Understanding the Data Journey

Let's follow a **single glucose reading** through the entire pipeline:

### 🏁 Start: Glucose Reading Taken

```json
{
  "sgv": 120,
  "date": 1699200000000,
  "direction": "Flat",
  "device": "share2"
}
```

This reading exists in the Nightscout app's database.

### 📥 Step 1: Ingestion (DLT Asset)

**File:** `src/cascade/defs/ingestion/dlt_assets.py`

**What happens:**
```python
@dg.asset(name="dlt_glucose_entries")
def entries(context, iceberg: IcebergResource):
    # 1. DLT fetches from Nightscout API
    pipeline = dlt.pipeline(...)
    load_info = pipeline.run(nightscout_source())

    # 2. Data saved to MinIO as Parquet
    # 3. PyIceberg registers the new data
    iceberg.append_parquet("raw.glucose_entries", parquet_files)
```

**Result:**
- Data stored: `s3://lake/warehouse/raw/glucose_entries/data-xyz.parquet`
- Table created: `raw.glucose_entries` (visible in Trino)
- Dagster marks asset as materialized ✅

### 🧹 Step 2: Bronze Transformation (dbt)

**File:** `transforms/dbt/models/bronze/stg_glucose_entries.sql`

```sql
WITH source AS (
    SELECT * FROM {{ source('raw', 'glucose_entries') }}
),

cleaned AS (
    SELECT
        sgv AS glucose_value,
        CAST(date AS TIMESTAMP) AS reading_timestamp,
        direction,
        device
    FROM source
    WHERE sgv IS NOT NULL  -- Remove invalid readings
)

SELECT * FROM cleaned
```

**What happened:**
- Renamed column: `sgv` → `glucose_value`
- Converted type: `date` (bigint milliseconds) → `reading_timestamp` (timestamp)
- Filtered out null values
- Standardized column names

**Result:**
- Table created: `bronze.stg_glucose_entries`
- Data is now clean and consistent

### ⚙️ Step 3: Silver Transformation (dbt)

**File:** `transforms/dbt/models/silver/fct_glucose_readings.sql`

```sql
WITH staged AS (
    SELECT * FROM {{ ref('stg_glucose_entries') }}
),

enriched AS (
    SELECT
        *,
        -- Add glucose category
        CASE
            WHEN glucose_value < 70 THEN 'Low'
            WHEN glucose_value > 180 THEN 'High'
            ELSE 'Normal'
        END AS glucose_category,

        -- Calculate rolling 3-reading average
        AVG(glucose_value) OVER (
            ORDER BY reading_timestamp
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS rolling_avg_3,

        -- Extract date parts for easy filtering
        DATE(reading_timestamp) AS reading_date,
        HOUR(reading_timestamp) AS reading_hour
    FROM staged
)

SELECT * FROM enriched
```

**What happened:**
- Added calculated field: `glucose_category`
- Added rolling average: `rolling_avg_3`
- Added date parts for easier grouping
- This is a "fact table" - ready for analytics

**Result:**
- Table created: `silver.fct_glucose_readings`
- Data is analytics-ready with business logic applied

### 📊 Step 4: Marts Transformation (dbt)

**File:** `transforms/dbt/models/marts_postgres/mrt_glucose_overview.sql`

```sql
WITH daily_stats AS (
    SELECT
        reading_date,
        COUNT(*) AS reading_count,
        AVG(glucose_value) AS avg_glucose,
        MIN(glucose_value) AS min_glucose,
        MAX(glucose_value) AS max_glucose,

        -- Time in range calculations
        SUM(CASE WHEN glucose_category = 'Low' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS pct_low,
        SUM(CASE WHEN glucose_category = 'Normal' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS pct_in_range,
        SUM(CASE WHEN glucose_category = 'High' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS pct_high
    FROM {{ ref('fct_glucose_readings') }}
    GROUP BY reading_date
)

SELECT * FROM daily_stats
ORDER BY reading_date DESC
```

**What happened:**
- Aggregated to daily level
- Calculated summary statistics
- Calculated time-in-range percentages
- Ready for dashboards

**Result:**
- Table created: `marts.mrt_glucose_overview` (in Iceberg)
- Table copied to PostgreSQL `marts.mrt_glucose_overview` (for fast BI access)

### 📈 Step 5: Visualization (Superset)

**Superset Dashboard queries:**
```sql
SELECT
    reading_date,
    avg_glucose,
    pct_in_range
FROM marts.mrt_glucose_overview
WHERE reading_date >= CURRENT_DATE - INTERVAL '30' DAY
ORDER BY reading_date
```

**Result:**
- Line chart showing glucose trends
- Pie chart showing time in range
- Table showing daily statistics

### 🔌 Step 6: API Access (FastAPI)

**User requests:**
```bash
curl -H "Authorization: Bearer <token>" \
  https://api.cascade.local/api/v1/glucose/readings?date=2024-11-05
```

**API queries:**
```sql
SELECT *
FROM silver.fct_glucose_readings
WHERE reading_date = '2024-11-05'
ORDER BY reading_timestamp
```

**Response:**
```json
[
  {
    "glucose_value": 120,
    "reading_timestamp": "2024-11-05T14:30:00",
    "glucose_category": "Normal",
    "rolling_avg_3": 118.3,
    "direction": "Flat"
  },
  ...
]
```

---

## Key Technologies Explained

### MinIO (Object Storage)

**What is it?**
- S3-compatible object storage
- Stores data as files (objects) in buckets

**Why do we use it?**
- Cheap and scalable
- Industry standard (S3 API)
- Works locally or in cloud

**How to access:**
- Web UI: http://localhost:9001
- AWS CLI: `aws --endpoint-url http://localhost:9000 s3 ls s3://lake/`
- Python: `boto3.client('s3', endpoint_url='http://localhost:9000')`

**Buckets in Cascade:**
- `lake` - Main data storage
  - `warehouse/` - Iceberg table data
  - `stage/` - Temporary staging files

### Apache Iceberg (Table Format)

**What is it?**
- An open table format for huge analytic datasets
- Adds database-like features to data lakes

**Key Features:**
- **ACID Transactions** - Atomic commits, no partial updates
- **Schema Evolution** - Add/remove columns safely
- **Time Travel** - Query data as of any point in time
- **Partition Evolution** - Change partitioning without rewriting data
- **Hidden Partitioning** - Partitions managed automatically

**How it works:**
```
Iceberg Table = Metadata + Data Files

Metadata (JSON files):
  ├─ Schema (column names, types)
  ├─ Partition spec (how data is organized)
  ├─ Snapshots (versions of the table)
  └─ Manifests (lists of data files)

Data Files (Parquet):
  ├─ data-001.parquet
  ├─ data-002.parquet
  └─ data-003.parquet
```

**Example commands:**
```sql
-- Query current data
SELECT * FROM raw.glucose_entries;

-- Time travel to yesterday
SELECT * FROM raw.glucose_entries
FOR SYSTEM_TIME AS OF TIMESTAMP '2024-11-04 00:00:00';

-- Query specific snapshot
SELECT * FROM raw.glucose_entries
FOR SYSTEM_VERSION AS OF 1234567890;
```

### Project Nessie (Catalog)

**What is it?**
- A Git-like catalog for Iceberg tables
- Manages table metadata and versions

**Key Concepts:**

**Branches:**
- Like Git branches
- Isolate development from production
- Cascade uses: `main` (prod) and `dev` (testing)

**Commits:**
- Atomic changes to table metadata
- Can commit multiple table changes together

**Tags:**
- Named snapshots (like Git tags)
- "v1.0-release", "end-of-quarter", etc.

**Merges:**
- Promote changes from dev → main
- All-or-nothing operation

**Example workflow:**
```bash
# Create a branch
nessie branch create -s dev experiment

# Make changes on experiment branch
# ...

# Merge back to dev
nessie merge experiment -s dev

# Promote to production
nessie merge dev -s main
```

**How Cascade uses it:**
```
main branch (production)
  ├─ raw.glucose_entries
  ├─ silver.fct_glucose_readings
  └─ marts.mrt_glucose_overview

dev branch (development)
  ├─ raw.glucose_entries (newer data)
  ├─ silver.fct_glucose_readings (newer data)
  └─ marts.mrt_glucose_overview (newer data)

Daily workflow:
1. Ingest new data to dev
2. Run transformations on dev
3. Validate data quality
4. Merge dev → main
```

### Trino (Query Engine)

**What is it?**
- Distributed SQL query engine
- Queries data where it lives (no movement needed)

**Key Features:**
- **Fast** - Designed for interactive analytics
- **Scalable** - Queries petabytes of data
- **Federated** - Query multiple data sources in one query
- **Standards-compliant** - Uses ANSI SQL

**Architecture:**
```
Trino Coordinator (brains)
    ↓
Trino Workers (muscle)
    ↓
Connectors (plugins)
    ├─ Iceberg Connector → MinIO
    ├─ PostgreSQL Connector → Postgres
    └─ Others (MySQL, MongoDB, etc.)
```

**How to use:**
```bash
# Command line
trino --server localhost:10011

# In the Trino CLI
SELECT * FROM iceberg.raw.glucose_entries LIMIT 10;

# Join across sources
SELECT
    i.glucose_value,
    p.user_name
FROM iceberg.raw.glucose_entries i
JOIN postgresql.public.users p ON i.user_id = p.id;
```

**Configuration in Cascade:**

Trino has two catalog configurations:

1. `iceberg.properties` - Points to `main` branch
   ```properties
   connector.name=iceberg
   iceberg.catalog.type=nessie
   iceberg.catalog.ref=main
   ```

2. `iceberg_dev.properties` - Points to `dev` branch
   ```properties
   connector.name=iceberg
   iceberg.catalog.type=nessie
   iceberg.catalog.ref=dev
   ```

### dbt (Data Build Tool)

**What is it?**
- Transformation framework
- "Analytics engineering" tool
- Write SQL, get pipelines

**Philosophy:**
- Transformations are SELECT statements
- Version control your SQL
- Test your data
- Document everything

**Key Concepts:**

**1. Models**
- A model = one SQL file = one table/view
- File: `models/silver/fct_glucose_readings.sql`
- Creates: `silver.fct_glucose_readings` table

**2. Sources**
- External tables (not created by dbt)
- Defined in `models/sources/sources.yml`
- Referenced with `{{ source('raw', 'glucose_entries') }}`

**3. Refs**
- References to other models
- `{{ ref('stg_glucose_entries') }}`
- Automatically builds dependency graph

**4. Tests**
- Data quality checks
- Built-in: `unique`, `not_null`, `accepted_values`, `relationships`
- Custom SQL tests

**5. Documentation**
- YAML descriptions
- Auto-generated docs site
- Column-level documentation

**Example dbt project structure:**
```
models/
├── sources/
│   └── sources.yml          # Define raw tables
├── bronze/
│   └── stg_glucose_entries.sql   # Staging transformations
├── silver/
│   └── fct_glucose_readings.sql  # Fact tables
├── gold/
│   └── dim_date.sql              # Dimension tables
└── marts_postgres/
    └── mrt_glucose_overview.sql  # Business metrics
```

**dbt Commands:**
```bash
# Compile SQL (check for errors)
dbt compile

# Run transformations
dbt run

# Run specific model
dbt run --select fct_glucose_readings

# Run model and everything downstream
dbt run --select fct_glucose_readings+

# Test data quality
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

### Dagster (Orchestration)

**What is it?**
- Modern orchestration platform
- Manages data workflows
- "Assets" not "tasks"

**Key Difference from Airflow:**

**Airflow (task-based):**
```
Task: fetch_data → Task: transform_data → Task: load_data
```
You care about **running tasks**.

**Dagster (asset-based):**
```
Asset: glucose_entries → Asset: fct_glucose_readings → Asset: glucose_overview
```
You care about **materializing data assets**.

**Key Concepts:**

**1. Assets**
- A piece of data (table, file, ML model, etc.)
- Has dependencies on other assets
- Can be materialized (created/updated)

```python
@asset
def glucose_entries():
    # Fetch from API
    return data

@asset
def fct_glucose_readings(glucose_entries):  # Depends on glucose_entries
    # Transform
    return transformed_data
```

**2. Resources**
- External services (databases, APIs, etc.)
- Injected into assets
- Configured separately

```python
@asset
def my_asset(trino: TrinoResource, iceberg: IcebergResource):
    results = trino.execute("SELECT * FROM ...")
    iceberg.append(results)
```

**3. Partitions**
- Split assets by time or other dimensions
- Process incrementally

```python
@asset(partitions_def=DailyPartitionsDefinition(start_date="2024-01-01"))
def daily_glucose_entries(context):
    partition_date = context.partition_key  # "2024-11-05"
    # Fetch only data for this date
```

**4. Sensors**
- Watch for events
- Trigger materializations automatically

```python
@sensor
def new_data_sensor():
    if new_data_available():
        return RunRequest(...)
```

**5. Schedules**
- Time-based triggers
- Cron expressions

```python
@schedule(cron_schedule="0 2 * * *")  # Daily at 2 AM
def daily_pipeline_schedule():
    return RunRequest(...)
```

**Dagster UI:**
- Web interface: http://localhost:3000
- View assets, runs, schedules
- Trigger materializations manually
- Monitor progress and logs

---

## Your First Look at Cascade

Let's start Cascade and explore!

### Step 1: Start the Services

```bash
# Make sure you're in the cascade directory
cd /path/to/cascade

# Copy example environment file
cp .env.example .env

# Edit .env if needed (or use defaults)
nano .env

# Start core services
make up-core

# Wait for services to be healthy (watch logs)
docker-compose logs -f
```

### Step 2: Access the Hub Dashboard

Open http://localhost:10009 in your browser.

You'll see a dashboard with links to all services:
- Dagster (orchestration)
- Trino (query engine)
- Superset (BI)
- MinIO (storage)
- Prometheus (metrics)
- Grafana (monitoring)

### Step 3: Explore Dagster

1. Click "Dagster" in the Hub
2. You'll see the Dagster UI at http://localhost:3000
3. Click "Assets" in the top menu

**What you see:**
- Asset graph showing all data assets
- Arrows showing dependencies
- Colors showing materialization status:
  - Green = recently materialized
  - Gray = never materialized
  - Yellow = stale (upstream changed)

**Try this:**
1. Find the `dlt_glucose_entries` asset
2. Click it to see details
3. Click "Materialize" button
4. Watch it run!

### Step 4: Query Data in Trino

1. Connect to Trino CLI:
   ```bash
   docker-compose exec trino trino
   ```

2. List catalogs:
   ```sql
   SHOW CATALOGS;
   ```

3. List schemas:
   ```sql
   SHOW SCHEMAS IN iceberg;
   ```

4. List tables:
   ```sql
   SHOW TABLES IN iceberg.raw;
   ```

5. Query data:
   ```sql
   SELECT * FROM iceberg.raw.glucose_entries LIMIT 10;
   ```

### Step 5: Explore MinIO Storage

1. Open http://localhost:9001
2. Login with credentials from `.env`
3. Browse the `lake` bucket
4. Navigate to `warehouse/raw/glucose_entries/`
5. See the Parquet files storing your data!

### Step 6: View dbt Documentation

1. Generate dbt docs:
   ```bash
   docker-compose exec dagster-webserver dbt docs generate --project-dir /opt/dagster/app/transforms/dbt
   ```

2. Serve docs (if not running):
   ```bash
   docker-compose up mkdocs
   ```

3. Open http://localhost:8000
4. Explore the data lineage graph!

---

## Understanding the Example Pipeline

Cascade includes a complete example: ingesting glucose monitoring data from Nightscout.

### The Pipeline Flow

```
Nightscout API
    ↓
[Dagster Asset: dlt_glucose_entries]
    ↓
Iceberg Table: raw.glucose_entries
    ↓
[dbt Model: stg_glucose_entries]
    ↓
Iceberg Table: bronze.stg_glucose_entries
    ↓
[dbt Model: fct_glucose_readings]
    ↓
Iceberg Table: silver.fct_glucose_readings
    ↓
[dbt Model: mrt_glucose_overview]
    ↓
Iceberg Table: marts.mrt_glucose_overview
    ↓
[Dagster Asset: postgres_glucose_marts]
    ↓
PostgreSQL Table: marts.mrt_glucose_overview
    ↓
Superset Dashboard
```

### Key Files

**1. Ingestion**
- **File:** `src/cascade/defs/ingestion/dlt_assets.py`
- **Asset:** `dlt_glucose_entries`
- **What it does:** Fetches from Nightscout API, saves to Iceberg

**2. Bronze Transformation**
- **File:** `transforms/dbt/models/bronze/stg_glucose_entries.sql`
- **Model:** `stg_glucose_entries`
- **What it does:** Cleans and standardizes raw data

**3. Silver Transformation**
- **File:** `transforms/dbt/models/silver/fct_glucose_readings.sql`
- **Model:** `fct_glucose_readings`
- **What it does:** Adds calculated fields and business logic

**4. Marts Transformation**
- **File:** `transforms/dbt/models/marts_postgres/mrt_glucose_overview.sql`
- **Model:** `mrt_glucose_overview`
- **What it does:** Creates aggregated daily statistics

**5. Publishing**
- **File:** `src/cascade/defs/publishing/trino_to_postgres.py`
- **Asset:** `postgres_glucose_marts`
- **What it does:** Copies Iceberg marts to PostgreSQL

### Configuration

**Source Configuration:**
- **File:** `src/cascade/config.py`
- **Environment Variables:**
  ```
  NIGHTSCOUT_URL=https://your-nightscout.herokuapp.com
  NIGHTSCOUT_API_SECRET=your-secret
  ```

**dbt Configuration:**
- **File:** `transforms/dbt/dbt_project.yml`
- **Profile:** `transforms/dbt/profiles/profiles.yml`

**Publishing Configuration:**
- **File:** `src/cascade/defs/publishing/config.yaml`
- **Defines which tables to publish to PostgreSQL**

---

## Common Workflows

### Workflow 1: Manually Trigger a Pipeline

**Scenario:** You want to refresh your data now (not wait for schedule).

**Steps:**
1. Open Dagster UI: http://localhost:3000
2. Click "Assets"
3. Find the asset you want to materialize (e.g., `dlt_glucose_entries`)
4. Click the asset name
5. Click "Materialize" button
6. Watch the run progress in the UI

**Or use the CLI:**
```bash
# Materialize a single asset
dagster asset materialize -m cascade.definitions -a dlt_glucose_entries

# Materialize with all downstream assets
dagster asset materialize -m cascade.definitions -a dlt_glucose_entries --downstream
```

### Workflow 2: Query Historical Data (Time Travel)

**Scenario:** You want to see what your data looked like yesterday.

**Steps:**
1. Connect to Trino:
   ```bash
   docker-compose exec trino trino
   ```

2. Find snapshot IDs:
   ```sql
   SELECT
       made_current_at,
       snapshot_id,
       parent_id
   FROM iceberg.raw."glucose_entries$snapshots"
   ORDER BY made_current_at DESC;
   ```

3. Query specific snapshot:
   ```sql
   SELECT * FROM iceberg.raw.glucose_entries
   FOR SYSTEM_VERSION AS OF 1234567890;
   ```

4. Or query by timestamp:
   ```sql
   SELECT * FROM iceberg.raw.glucose_entries
   FOR SYSTEM_TIME AS OF TIMESTAMP '2024-11-04 00:00:00';
   ```

### Workflow 3: Test Changes Safely (Branch Development)

**Scenario:** You want to test a new transformation without affecting production.

**Steps:**
1. Work on the `dev` branch (default in Cascade)

2. Make your changes to dbt models

3. Run transformations on dev:
   ```bash
   # Dagster uses dev branch by default
   dagster asset materialize -m cascade.definitions -a dbt:*
   ```

4. Query dev branch data:
   ```sql
   -- Uses iceberg_dev catalog (points to dev branch)
   SELECT * FROM iceberg_dev.silver.fct_glucose_readings;
   ```

5. If everything looks good, promote to main:
   ```bash
   # Use Nessie API or Dagster workflow
   # (Cascade includes a promote_dev_to_main asset)
   dagster asset materialize -m cascade.definitions -a promote_dev_to_main
   ```

6. Now production uses your changes:
   ```sql
   -- Uses iceberg catalog (points to main branch)
   SELECT * FROM iceberg.silver.fct_glucose_readings;
   ```

### Workflow 4: Debug a Failed Asset

**Scenario:** An asset materialization failed and you need to understand why.

**Steps:**
1. Open Dagster UI

2. Click "Runs" in top menu

3. Find the failed run (red)

4. Click the run to see details

5. Look at the logs:
   - Stdout shows print statements and query results
   - Stderr shows errors

6. Common issues:
   - **Schema mismatch:** Column types don't match
   - **Missing dependency:** Upstream asset not materialized
   - **Query error:** SQL syntax error in dbt model
   - **Connection error:** Can't reach external service

7. Fix the issue and re-run:
   - Click "Re-execute" button in Dagster UI
   - Or materialize the asset again

### Workflow 5: Add Data Quality Tests

**Scenario:** You want to ensure data quality with automated tests.

**Steps:**
1. Edit dbt schema file:
   ```yaml
   # transforms/dbt/models/silver/schema.yml
   version: 2

   models:
     - name: fct_glucose_readings
       description: "Glucose readings with calculated metrics"
       columns:
         - name: glucose_value
           description: "Glucose reading in mg/dL"
           tests:
             - not_null
             - accepted_values:
                 values: [40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310, 320, 330, 340, 350, 360, 370, 380, 390, 400]
                 quote: false

         - name: reading_timestamp
           description: "When the reading was taken"
           tests:
             - not_null
             - unique
   ```

2. Run tests:
   ```bash
   docker-compose exec dagster-webserver dbt test --project-dir /opt/dagster/app/transforms/dbt
   ```

3. Tests run automatically when you materialize dbt assets in Dagster

4. If a test fails:
   - Check Dagster logs
   - Fix data or adjust test
   - Re-run

### Workflow 6: Monitor Pipeline Health

**Scenario:** You want to monitor your pipelines and get alerted to issues.

**Steps:**
1. Open Grafana: http://localhost:10003

2. Navigate to dashboards:
   - Dagster dashboard shows asset materialization rates
   - Trino dashboard shows query performance
   - System dashboard shows resource usage

3. Set up alerts:
   - Click dashboard panel
   - Edit → Alert tab
   - Configure alert conditions
   - Add notification channel (Slack, email, etc.)

4. View logs in Loki:
   - Grafana → Explore
   - Select Loki data source
   - Query: `{job="dagster"}`

---

## Next Steps

Congratulations! You now understand the basics of Cascade.

**Continue your learning:**
1. 📖 Read the [Workflow Development Guide](WORKFLOW_DEVELOPMENT_GUIDE.md) to build your own pipelines
2. 📖 Read the [Data Modeling Guide](DATA_MODELING_GUIDE.md) to learn Bronze/Silver/Gold best practices
3. 📖 Read the [Dagster Assets Tutorial](DAGSTER_ASSETS_TUTORIAL.md) for deep-dive on orchestration
4. 📖 Read the [dbt Development Guide](DBT_DEVELOPMENT_GUIDE.md) for transformation best practices

**Try these exercises:**
1. Add a new field to `fct_glucose_readings`
2. Create a new mart table with weekly aggregations
3. Add a data quality test
4. Create a custom Dagster asset
5. Set up a Grafana alert

**Get help:**
- Read the docs in the `docs/` folder
- Check the Dagster documentation: https://docs.dagster.io
- Check the dbt documentation: https://docs.getdbt.com
- Check the Iceberg documentation: https://iceberg.apache.org/docs
- Open an issue on GitHub

**Happy data engineering!** 🚀

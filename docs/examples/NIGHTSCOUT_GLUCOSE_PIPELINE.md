# End-to-End Data Pipeline: Nightscout Glucose Monitoring

This guide walks through a complete data engineering pipeline using real-world continuous glucose monitoring (CGM) data from Nightscout. It demonstrates every component of the lakehouse stack: ingestion, transformation, validation, lineage tracking, and visualization.

## What You'll Learn

By following this example, you'll understand how to:
1. Ingest data from REST APIs using custom Dagster assets
2. Store raw data efficiently in Parquet format
3. Transform data through staging, intermediate, and curated layers using dbt
4. Validate data quality with Great Expectations
5. Track data lineage with OpenLineage/Marquez
6. Build production dashboards in Superset
7. Orchestrate the entire pipeline with Dagster

## Target Audience

This guide is written for experienced Python developers who are new to data engineering. If you've built web APIs or ETL scripts before, but haven't used modern data stack tools like dbt, Dagster, or data lakehouse architectures, this will get you up to speed.

---

## Part 1: Understanding the Data Source

### What is Nightscout?

Nightscout is an open-source platform for continuous glucose monitoring (CGM) used by people with diabetes. It collects real-time blood glucose data from devices like Dexcom sensors and exposes it via a REST API.

**API Endpoint:** `https://gwp-diabetes.fly.dev/api/v1/entries.json`

**Sample Response:**
```json
[
  {
    "_id": "68e6d727b25bba8934f3d0f4",
    "sgv": 182,
    "date": 1759958801573,
    "dateString": "2025-10-08T21:26:41.573Z",
    "trend": 4,
    "direction": "Flat",
    "device": "share2",
    "type": "sgv"
  }
]
```

**Key Fields:**
- `sgv`: Sensor Glucose Value (mg/dL)
- `date`/`mills`: Unix timestamp in milliseconds
- `direction`: Trend arrow (Flat, SingleUp, DoubleDown, etc.)
- `trend`: Numeric trend indicator

**Why This Data Matters:**
- Readings every 5 minutes = ~288 data points per day
- Time in range (70-180 mg/dL) is a key clinical metric
- Pattern analysis helps identify issues (e.g., overnight lows, post-meal spikes)

---

## Part 2: Data Ingestion with Dagster Assets

Instead of using Airbyte for this simple REST API, we built custom Dagster assets. This gives us more control and demonstrates how to build reusable ingestion patterns.

### Asset 1: Raw API Ingestion

**File:** `dagster/assets/nightscout_assets.py`

```python
@asset(
    group_name="nightscout",
    compute_kind="python",
    description="Raw glucose entries from Nightscout API",
)
def raw_nightscout_entries(context: AssetExecutionContext) -> dict[str, Any]:
    """
    Fetch glucose entries from Nightscout API.

    This demonstrates:
    - HTTP API calls with requests library
    - Pagination/filtering with query parameters
    - Error handling for network failures
    - Logging for observability
    """
    endpoint = "https://gwp-diabetes.fly.dev/api/v1/entries.json"
    params = {"count": 2016}  # Last 7 days of data

    response = requests.get(endpoint, params=params, timeout=30)
    response.raise_for_status()

    entries = response.json()
    context.log.info(f"Fetched {len(entries)} glucose entries")

    return {"entries": entries, "count": len(entries)}
```

**Key Concepts:**
- **Asset**: A versioned data artifact that Dagster tracks
- **Context**: Provides logging, metadata, and run information
- **Return Value**: Passed to downstream assets via dependency injection

### Asset 2: Parquet Conversion

**File:** `dagster/assets/nightscout_assets.py`

```python
@asset(
    group_name="nightscout",
    compute_kind="duckdb",
    deps=[raw_nightscout_entries],
)
def processed_nightscout_entries(
    context: AssetExecutionContext,
    raw_nightscout_entries: dict[str, Any]
) -> str:
    """
    Convert raw JSON to typed Parquet format.

    Why Parquet?
    - Columnar storage: 10-100x faster for analytics
    - Strong typing: Catches schema drift early
    - Compression: ~10x smaller than JSON
    - Partitioning: Efficient time-range queries
    """
    entries = raw_nightscout_entries["entries"]
    output_path = Path("/data/lake/raw/nightscout/glucose_entries.parquet")

    # Use DuckDB for efficient JSON → Parquet conversion
    con = duckdb.connect(":memory:")
    con.execute("CREATE TABLE temp AS SELECT * FROM read_json_auto(?)", [json.dumps(entries)])

    con.execute("""
        COPY (
            SELECT
                _id as entry_id,
                sgv as glucose_mg_dl,
                epoch_ms(mills) as timestamp,
                direction,
                device
            FROM temp
            WHERE sgv IS NOT NULL
        ) TO ? (FORMAT PARQUET, COMPRESSION ZSTD)
    """, [str(output_path)])

    return str(output_path)
```

**Why DuckDB Instead of Pandas?**
- 5-10x faster for this use case
- Better memory efficiency
- Direct Parquet write (no intermediate DataFrame)
- SQL interface is familiar and expressive

---

## Part 3: Data Transformation with dbt

dbt (data build tool) is the industry standard for SQL-based transformations. It provides:
- Version control for SQL logic
- Incremental materializations
- Automated documentation and lineage
- Testing and validation

### Layer 1: Staging (`stg_nightscout_glucose.sql`)

**Purpose:** Clean, typed view over raw Parquet files

```sql
{{ config(
    materialized='view',
    tags=['nightscout', 'stg']
) }}

select
    entry_id,
    glucose_mg_dl,
    timestamp as reading_timestamp,
    direction,
    device
from read_parquet('/data/lake/raw/nightscout/*.parquet')
where glucose_mg_dl is not null
    and glucose_mg_dl between 20 and 600  -- Physiologically plausible
```

**Key Concepts:**
- `{{ config() }}`: Jinja templating for model configuration
- `materialized='view'`: Creates a lightweight view (not a table)
- `tags`: Used for selective model runs (`dbt run --select tag:stg`)

### Layer 2: Intermediate (`int_glucose_enriched.sql`)

**Purpose:** Add calculated fields and business logic

```sql
{{ config(
    materialized='table',
    tags=['nightscout', 'int']
) }}

with glucose_data as (
    select * from {{ ref('stg_nightscout_glucose') }}
),

enriched as (
    select
        *,
        -- Time-based dimensions
        date_trunc('day', reading_timestamp) as reading_date,
        extract(hour from reading_timestamp) as hour_of_day,

        -- Blood sugar categories (ADA guidelines)
        case
            when glucose_mg_dl < 70 then 'hypoglycemia'
            when glucose_mg_dl >= 70 and glucose_mg_dl <= 180 then 'in_range'
            when glucose_mg_dl > 180 then 'hyperglycemia'
        end as glucose_category,

        -- Rate of change (lag over 5 minutes)
        glucose_mg_dl - lag(glucose_mg_dl) over (
            partition by device order by reading_timestamp
        ) as glucose_change_mg_dl
    from glucose_data
)

select * from enriched
```

**Key Concepts:**
- `{{ ref() }}`: Creates dependency graph automatically
- **CTEs (Common Table Expressions):** Organize complex SQL
- **Window Functions:** `lag()` for time-series calculations
- `materialized='table'`: Persists results for performance

### Layer 3: Curated (`fact_glucose_readings.sql`)

**Purpose:** Production-ready, incrementally updated fact table

```sql
{{ config(
    materialized='incremental',
    unique_key='entry_id',
    tags=['nightscout', 'curated']
) }}

select
    entry_id,
    glucose_mg_dl,
    reading_timestamp,
    glucose_category,
    glucose_change_mg_dl,
    direction
from {{ ref('int_glucose_enriched') }}

{% if is_incremental() %}
    where reading_timestamp > (select max(reading_timestamp) from {{ this }})
{% endif %}
```

**Why Incremental?**
- Only processes new data after first run
- Scales to billions of rows
- Much faster for large datasets
- `{{ this }}` references the existing table

### Layer 4: Dimensions (`dim_glucose_date.sql`)

**Purpose:** Daily aggregations for trend analysis

```sql
select
    reading_date,
    count(*) as reading_count,
    round(avg(glucose_mg_dl), 1) as avg_glucose_mg_dl,

    -- Time in range (key clinical metric)
    round(100.0 * sum(is_in_range) / count(*), 1) as time_in_range_pct,

    -- Estimated A1C (glucose management indicator)
    round(3.31 + (0.02392 * avg(glucose_mg_dl)), 2) as estimated_a1c_pct
from {{ ref('int_glucose_enriched') }}
group by reading_date
```

### Layer 5: Marts (`mart_glucose_overview.sql`)

**Purpose:** Denormalized tables in PostgreSQL for BI tools

```sql
{{ config(
    materialized='table',
    tags=['nightscout', 'mart']
) }}

select
    reading_date,
    avg_glucose_mg_dl,
    time_in_range_pct,
    estimated_a1c_pct,

    -- 7-day rolling average
    avg(estimated_a1c_pct) over (
        order by reading_date
        rows between 6 preceding and current row
    ) as estimated_a1c_7d_avg
from {{ ref('dim_glucose_date') }}
where reading_date >= current_date - interval '90 days'
```

**Why Separate Marts?**
- Postgres is faster than DuckDB for BI queries
- Pre-aggregated for dashboard performance
- Optimized indexes for specific query patterns

---

## Part 4: Data Quality with Great Expectations

Great Expectations (GE) validates data at every stage. It's like unit tests for data.

**File:** `great_expectations/expectations/nightscout_suite.json`

```json
{
  "expectation_suite_name": "nightscout_glucose_suite",
  "expectations": [
    {
      "expectation_type": "expect_column_values_to_be_between",
      "kwargs": {
        "column": "glucose_mg_dl",
        "min_value": 20,
        "max_value": 600,
        "mostly": 0.99
      },
      "meta": {
        "notes": "Physiologically plausible glucose range"
      }
    },
    {
      "expectation_type": "expect_column_values_to_not_be_null",
      "kwargs": {
        "column": "glucose_mg_dl"
      }
    },
    {
      "expectation_type": "expect_column_mean_to_be_between",
      "kwargs": {
        "column": "glucose_mg_dl",
        "min_value": 80,
        "max_value": 250
      }
    }
  ]
}
```

**Dagster Integration:** `dagster/assets/nightscout_validations.py`

```python
@asset(
    group_name="nightscout_quality",
    compute_kind="great_expectations",
    ins={"int_glucose_enriched": AssetIn()},
)
def validate_glucose_enriched(
    context: AssetExecutionContext,
    int_glucose_enriched: str
) -> dict[str, Any]:
    """
    Validate enriched glucose data quality.

    Runs GE expectations and logs failures.
    """
    suite = ExpectationSuite.read_json("expectations/nightscout_suite.json")
    df = pd.read_parquet(int_glucose_enriched)
    ge_df = PandasDataset(df)

    results = []
    for expectation in suite.expectations:
        result = getattr(ge_df, expectation.expectation_type)(**expectation.kwargs)
        results.append(result)

        if not result["success"]:
            context.log.warning(f"Validation failed: {expectation.expectation_type}")

    return {"success_rate": sum(r["success"] for r in results) / len(results)}
```

**When to Run Validations:**
- After raw ingestion (structure checks)
- After enrichment (derived fields)
- Before loading to marts (business logic)

---

## Part 5: Data Lineage with OpenLineage/Marquez

OpenLineage tracks data flow automatically via instrumentation.

**Setup:** Already configured in `dagster/resource/openlineage.py`

**What Gets Tracked:**
- Input datasets (Parquet files)
- Output datasets (tables, views)
- Transformations (SQL queries)
- Job runs (success/failure, duration)
- Schema changes

**Viewing Lineage:**
1. Start Marquez: `docker-compose up marquez`
2. Open: http://localhost:3000
3. View graph: Sources → `nightscout` → Lineage

**Why This Matters:**
- Debugging: "Why did this number change?"
- Impact analysis: "What breaks if I modify this table?"
- Compliance: Complete audit trail for regulated environments

---

## Part 6: Dashboards with Superset

Superset connects to the `mart_glucose_overview` table in Postgres.

**Configuration:** `superset/dashboards/glucose_monitoring.json`

**Charts:**
1. **Big Number**: Current glucose level
2. **Line Chart**: 7-day glucose trend with target range shading
3. **Heatmap**: Glucose patterns by hour/day of week
4. **Pie Chart**: Time in range distribution
5. **Big Number**: Estimated A1C

**Creating the Dashboard:**
1. Start Superset: `docker-compose up superset`
2. Add database connection to Postgres
3. Import dashboard JSON
4. Set refresh interval to 5 minutes

---

## Part 7: Running the Complete Pipeline

### Step 1: Start Infrastructure

```bash
# Start all services
docker-compose up -d postgres minio dagster marquez superset

# Check status
docker-compose ps
```

### Step 2: Initialize Data Lake

```bash
# Create MinIO buckets
mc alias set local http://localhost:9000 minioadmin minioadmin
mc mb local/lakehouse

# Create Postgres schemas
psql -h localhost -U lakehouse -d lakehouse -c "CREATE SCHEMA IF NOT EXISTS marts;"
```

### Step 3: Run Dagster Pipeline

```bash
# Navigate to Dagster project
cd dagster

# Install dependencies
uv pip install -e .

# Start Dagster UI
dagster dev

# Open browser: http://localhost:3000
```

### Step 4: Materialize Assets

In Dagster UI:
1. Navigate to **Assets** tab
2. Select `raw_nightscout_entries`
3. Click **Materialize**
4. Watch the cascade: raw → processed → dbt staging → curated → marts

### Step 5: View Results

**Check Data Quality:**
- Navigate to `validate_glucose_enriched` asset
- Review validation results in metadata

**Check Lineage:**
- Open Marquez: http://localhost:3000
- Search for `nightscout` namespace
- Explore upstream/downstream dependencies

**Check Dashboard:**
- Open Superset: http://localhost:8088
- Navigate to "Glucose Monitoring" dashboard
- Verify charts display data

---

## Part 8: Scheduling and Automation

### Create Dagster Schedule

**File:** `dagster/schedules/nightscout.py`

```python
from dagster import ScheduleDefinition, define_asset_job, AssetSelection

nightscout_job = define_asset_job(
    name="nightscout_pipeline",
    selection=AssetSelection.groups("nightscout", "nightscout_quality"),
)

nightscout_schedule = ScheduleDefinition(
    name="nightscout_every_30_min",
    job=nightscout_job,
    cron_schedule="*/30 * * * *",  # Every 30 minutes
    execution_timezone="UTC",
)
```

**Register in repository.py:**
```python
from schedules.nightscout import nightscout_schedule

defs = Definitions(
    schedules=[nightscout_schedule],
    # ... other definitions
)
```

**Activate Schedule:**
1. In Dagster UI, go to **Schedules**
2. Find `nightscout_every_30_min`
3. Click **Start Schedule**

---

## Part 9: Monitoring and Alerting

### Dagster Alerts

Configure Slack/email alerts for failures:

```python
from dagster import run_failure_sensor, RunFailureSensorContext

@run_failure_sensor
def pipeline_failure_alert(context: RunFailureSensorContext):
    message = f"Pipeline failed: {context.dagster_run.job_name}"
    # Send to Slack, PagerDuty, etc.
```

### Data Quality Alerts

Fail pipeline if critical validations fail:

```python
@asset
def validate_glucose_enriched(...):
    results = run_validations(...)

    if results["critical_failures"] > 0:
        raise Exception("Critical data quality checks failed!")
```

---

## Part 10: Extending the Pipeline

### Add Treatments Data

Nightscout also tracks insulin, carbs, and exercise:

```python
@asset
def raw_nightscout_treatments(context):
    response = requests.get("https://gwp-diabetes.fly.dev/api/v1/treatments.json")
    # ... similar pattern to glucose entries
```

### Add ML Predictions

Use historical data to predict future glucose:

```python
@asset
def glucose_predictions(context, fact_glucose_readings):
    # Load curated data
    df = duckdb.execute("SELECT * FROM fact_glucose_readings").df()

    # Train model (e.g., Prophet, LSTM)
    model = train_time_series_model(df)

    # Generate 6-hour forecast
    predictions = model.predict(periods=72)  # 72 * 5 min = 6 hours

    return predictions
```

---

## Summary: What We Built

| Component | Files | Purpose |
|-----------|-------|---------|
| **Ingestion** | `nightscout_assets.py` | Fetch API data, convert to Parquet |
| **Staging** | `stg_nightscout_glucose.sql` | Clean, typed view over raw data |
| **Intermediate** | `int_glucose_enriched.sql` | Enrich with calculated fields |
| **Curated** | `fact_glucose_readings.sql`, `dim_glucose_date.sql` | Production fact/dimension tables |
| **Marts** | `mart_glucose_overview.sql` | Denormalized tables for BI |
| **Validation** | `nightscout_suite.json`, `nightscout_validations.py` | Data quality checks |
| **Orchestration** | `repository.py` | Dagster pipeline definition |
| **Visualization** | `glucose_monitoring.json` | Superset dashboard |

---

## Key Takeaways for Data Engineers

### 1. Asset-Based Thinking
- **Assets** are versioned data artifacts, not just ephemeral job outputs
- Dependencies are explicit (type-safe function arguments)
- Materializations are replayable and auditable

### 2. Layered Transformations
- **Staging**: Clean and type raw data (minimal logic)
- **Intermediate**: Add business logic (not exposed to end users)
- **Curated**: Production-ready datasets (strict SLAs)
- **Marts**: Optimized for specific use cases (BI, ML, APIs)

### 3. DuckDB + Parquet for Analytics
- Avoid loading data into memory (read directly from Parquet)
- Push down filters/aggregations to storage layer
- 10-100x faster than pandas for large datasets

### 4. Incremental Materializations
- Full refreshes don't scale beyond TB-scale data
- Use `unique_key` to handle late-arriving data
- Partition by time for efficient queries

### 5. Data Quality as Code
- Expectations are version-controlled, testable, and reusable
- Validate at ingestion, transformation, and serving layers
- Fail fast (catch issues before they cascade downstream)

### 6. Observability is Critical
- Track lineage automatically (don't rely on documentation)
- Log metadata (row counts, nulls, durations)
- Alert on failures AND anomalies (silent failures are worse)

---

## Next Steps

1. **Add More Sources**: Extend to other APIs (weather, activity trackers)
2. **Add ML Models**: Predict glucose trends with Prophet or LSTM
3. **Add Alerts**: Send notifications for critical glucose levels
4. **Scale to Cloud**: Migrate to MotherDuck, S3, or Snowflake
5. **Add Governance**: Use OpenMetadata for enterprise catalog

---

## Questions and Troubleshooting

### Pipeline Fails on Parquet Write
- Check directory permissions: `chmod -R 777 /data/lake`
- Verify DuckDB version: `duckdb --version` (should be 1.1.0+)

### dbt Models Don't Run
- Check profiles: `dbt debug --profiles-dir /dbt/profiles`
- Verify connection: `dbt run --select stg_nightscout_glucose`

### Great Expectations Fails
- Check pandas compatibility: GE requires pandas 1.x (not 2.x)
- Verify suite path: Expectations must be in `great_expectations/expectations/`

### Superset Can't Connect to Postgres
- Check connection string: `postgresql://lakehouse:lakehouse@postgres:5432/lakehouse`
- Verify marts exist: `psql -c "SELECT * FROM marts.mart_glucose_overview LIMIT 1"`

---

## Additional Resources

- **Dagster Docs**: https://docs.dagster.io
- **dbt Docs**: https://docs.getdbt.com
- **Great Expectations**: https://docs.greatexpectations.io
- **OpenLineage**: https://openlineage.io/docs
- **DuckDB SQL**: https://duckdb.org/docs/sql/introduction

---

**Author:** Generated with Claude Code
**Last Updated:** 2025-10-08
**License:** MIT

# Part 8: Real-World Example—Building a Complete Data Pipeline

> Prerequisite: Complete [Part 2: Getting Started](02-setup-guide.md), [Part 5: Data Ingestion](05-data-ingestion.md), and [Part 6: dbt Transformations](06-dbt-transformations.md).

## What You'll Learn

- How the ingestion, dbt, and publishing layers fit together
- How to configure end-to-end assets for a real dataset
- How to validate data quality during the pipeline
- How to visualize outputs in Superset

## Prerequisites

- [Part 2: Getting Started—Setup Guide](02-setup-guide.md)
- [Part 5: Data Ingestion](05-data-ingestion.md)
- [Part 6: dbt Transformations](06-dbt-transformations.md)

We've covered all the pieces. Now let's build a complete, working pipeline from start to finish: **Nightscout Glucose Monitoring**.
For validation patterns used in this walkthrough, see [Part 9: Data Quality with Pandera](09-data-quality-with-pandera.md).

## The Use Case

**Nightscout** is an open-source glucose monitoring system used by people with diabetes. It sends glucose readings every 5 minutes to a cloud API.

**Goal**: Build analytics to understand:

- Daily glucose averages and ranges
- Time spent in range (70-180 mg/dL)
- Hour-by-hour patterns
- Overnight stability

## The Architecture

```
Nightscout API
  ↓ (5-min readings)
Phlo Ingestion
  ├─ DLT stages to S3
  ├─ PyIceberg merges to raw.glucose_entries
  └─ Nessie tracks via snapshot
    ↓
dbt Transformation
  ├─ Bronze: stg_glucose_entries (staging)
  ├─ Silver: fct_glucose_readings (enriched)
  ├─ Gold: dim_date, mrt_glucose_readings (metrics)
  └─ Marts: mrt_glucose_overview (aggregated)
    ↓
Postgres Publishing
  └─ Superset Dashboard
```

## Step 1: Understanding the API

Nightscout's glucose API:

```bash
# Fetch glucose readings
curl "https://gwp-diabetes.fly.dev/api/v1/entries.json" \
  -G \
  --data-urlencode 'count=10000' \
  --data-urlencode 'find[dateString][$gte]=2024-10-15T00:00:00.000Z' \
  --data-urlencode 'find[dateString][$lt]=2024-10-15T23:59:59.999Z'

# Response:
[
  {
    "_id": "507f1f77bcf86cd799439011",  # MongoDB ObjectId
    "sgv": 145,                          # Glucose in mg/dL
    "date": 1729027800000,               # Unix ms
    "dateString": "2024-10-15T10:30:00.000Z",
    "direction": "Flat",                 # Trend direction
    "trend": 0,                          # Numeric trend
    "device": "share2",                  # Device type
    "type": "sgv",                       # Type
    "rssi": 100,                         # Signal strength
  },
  ...
]
```


## Step 2: Data Ingestion

### Using @phlo_ingestion Decorator

Phlo simplifies ingestion with the `@phlo_ingestion` decorator that handles validation, staging, and Iceberg merging:

```python
# File: phlo-examples/nightscout/workflows/ingestion/nightscout/readings.py

import phlo
from dlt.sources.rest_api import rest_api
from workflows.schemas.nightscout import RawGlucoseEntries

@phlo_ingestion(
    table_name="glucose_entries",
    unique_key="_id",
    validation_schema=RawGlucoseEntries,
    group="nightscout",
    cron="0 */1 * * *",
    freshness_hours=(1, 24),
)
def glucose_entries(partition_date: str):
    """
    Ingest Nightscout glucose entries using DLT rest_api source.

    Features:
    - Idempotent ingestion: safe to run multiple times without duplicates
    - Deduplication based on _id field (Nightscout's unique entry ID)
    - Daily partitioning by timestamp
    - Automatic validation with Pandera schema
    - Branch-aware writes to Iceberg

    Args:
        partition_date: Date partition in YYYY-MM-DD format

    Returns:
        DLT resource for glucose entries, or None if no data
    """
    start_time_iso = f"{partition_date}T00:00:00.000Z"
    end_time_iso = f"{partition_date}T23:59:59.999Z"

    source = rest_api(
        client={
            "base_url": "https://gwp-diabetes.fly.dev/api/v1",
        },
        resources=[
            {
                "name": "entries",
                "endpoint": {
                    "path": "entries.json",
                    "params": {
                        "count": 10000,
                        "find[dateString][$gte]": start_time_iso,
                        "find[dateString][$lt]": end_time_iso,
                    },
                },
            }
        ],
    )

    return source
```

**What the @phlo_ingestion decorator does automatically**:

1. Creates Dagster asset with daily partitioning
2. Runs DLT pipeline to fetch and stage data to parquet
3. Validates with RawGlucoseEntries Pandera schema
4. Creates Iceberg table if it doesn't exist
5. Merges data idempotently using `_id` as unique key
6. Adds freshness checks and cron scheduling
7. Returns MaterializeResult with metadata

**Run it**:

```bash
phlo materialize --select dlt_glucose_entries --partition 2024-10-15
```


## Step 3: Bronze Layer Transformation

### dbt Model: Staging

```sql
-- File: workflows/transforms/dbt/models/bronze/stg_glucose_entries.sql

{{ config(
    materialized='view',
    tags=['nightscout', 'stg']
) }}

WITH raw_data AS (
    SELECT * FROM {{ source('dagster_assets', 'glucose_entries') }}
)

SELECT
    -- Rename and type columns
    _id as entry_id,
    CAST(sgv AS INT) as glucose_mg_dl,
    CAST(date_string AS TIMESTAMP) as reading_timestamp,
    date_string as timestamp_iso,
    direction,
    trend,
    device,
    type as reading_type,
    CAST(utc_offset AS INT) as utc_offset_minutes,

    -- Metadata
    _cascade_ingested_at as ingested_at,
    _dlt_load_id,
    _dlt_id

FROM raw_data

-- Data quality filters
WHERE sgv IS NOT NULL
  AND sgv BETWEEN 20 AND 600  -- Physiologically plausible
  {% if var('partition_date_str', None) is not none %}
    AND DATE(date_string) = DATE('{{ var("partition_date_str") }}')
  {% endif %}
```

**Purpose**:

- Clean types (string → timestamp)
- Rename for clarity (\_id → entry_id)
- Filter out bad data (null, out-of-range)

## Step 4: Silver Layer Transformation

### dbt Model: Enriched Facts

```sql
-- File: workflows/transforms/dbt/models/silver/fct_glucose_readings.sql

{{ config(
    materialized='table',
    tags=['nightscout', 'int']
) }}

WITH glucose_data AS (
    SELECT * FROM {{ ref('stg_glucose_entries') }}
),

enriched AS (
    SELECT
        entry_id,
        glucose_mg_dl,
        reading_timestamp,
        timestamp_iso,
        direction,
        device,

        -- Time dimensions
        DATE(reading_timestamp) as reading_date,
        EXTRACT(HOUR FROM reading_timestamp) as hour_of_day,
        DAY_OF_WEEK(reading_timestamp) as day_of_week,
        FORMAT_DATETIME(reading_timestamp, 'EEEE') as day_name,

        -- Glucose classification (ADA guidelines)
        CASE
            WHEN glucose_mg_dl < 70 THEN 'hypoglycemia'
            WHEN glucose_mg_dl >= 70 AND glucose_mg_dl <= 180 THEN 'in_range'
            WHEN glucose_mg_dl > 180 AND glucose_mg_dl <= 250 THEN 'hyperglycemia_mild'
            WHEN glucose_mg_dl > 250 THEN 'hyperglycemia_severe'
        END as glucose_category,

        -- Time in range flag
        CASE
            WHEN glucose_mg_dl >= 70 AND glucose_mg_dl <= 180 THEN 1
            ELSE 0
        END as is_in_range,

        -- Rate of change
        glucose_mg_dl - LAG(glucose_mg_dl) OVER (
            PARTITION BY device ORDER BY reading_timestamp
        ) as glucose_change_mg_dl,

        -- Minutes since last reading
        DATE_DIFF('minute',
            LAG(reading_timestamp) OVER (
                PARTITION BY device ORDER BY reading_timestamp
            ),
            reading_timestamp
        ) as minutes_since_last_reading

    FROM glucose_data
)

SELECT * FROM enriched
ORDER BY reading_timestamp DESC
```

**Features added**:

- Time dimensions (hour, day, etc.)
- Glucose categories (hypoglycemia/in-range/hyperglycemia)
- Time in range indicator
- Rate of change (lag window function)
- Interval between readings

## Step 5: Gold Layer Metrics

### dbt Model: Summarized Metrics

```sql
-- File: workflows/transforms/dbt/models/gold/mrt_glucose_readings.sql

{{ config(
    materialized='table',
    tags=['nightscout', 'metrics']
) }}

SELECT
    reading_date,
    hour_of_day,

    -- Glucose statistics
    COUNT(*) as reading_count,
    ROUND(AVG(glucose_mg_dl), 1) as avg_glucose,
    MIN(glucose_mg_dl) as min_glucose,
    MAX(glucose_mg_dl) as max_glucose,

    -- Time in range
    ROUND(100.0 * SUM(is_in_range) / COUNT(*), 1) as percent_in_range,

    -- Glucose categories
    COUNT(CASE WHEN glucose_category = 'hypoglycemia' THEN 1 END) as hypoglycemia_count,
    COUNT(CASE WHEN glucose_category = 'in_range' THEN 1 END) as in_range_count,
    COUNT(CASE WHEN glucose_category = 'hyperglycemia_mild' THEN 1 END) as hyperglycemia_mild_count,
    COUNT(CASE WHEN glucose_category = 'hyperglycemia_severe' THEN 1 END) as hyperglycemia_severe_count

FROM {{ ref('fct_glucose_readings') }}

GROUP BY reading_date, hour_of_day
ORDER BY reading_date DESC, hour_of_day DESC
```

**Metrics**:

- Average glucose per hour
- Time in range percentage
- Hypoglycemia warnings
- Hyperglycemia counts

## Step 6: Publishing to Postgres

### dbt Model: BI-Ready Marts

```sql
-- File: workflows/transforms/dbt/models/marts_postgres/mrt_glucose_overview.sql

{{ config(
    materialized='table',
    meta={'external_database': 'postgres'}
) }}

SELECT
    reading_date,

    -- Daily stats
    COUNT(*) as total_readings,
    ROUND(AVG(glucose_mg_dl), 1) as avg_glucose_mg_dl,
    MIN(glucose_mg_dl) as min_glucose_mg_dl,
    MAX(glucose_mg_dl) as max_glucose_mg_dl,
    ROUND(STDDEV(glucose_mg_dl), 1) as stddev_glucose,

    -- Time in range
    ROUND(100.0 * SUM(is_in_range) / COUNT(*), 1) as percent_in_range,

    -- Alerts
    CASE
        WHEN COUNT(CASE WHEN glucose_category = 'hypoglycemia' THEN 1 END) > 3 THEN 'CRITICAL'
        WHEN COUNT(CASE WHEN glucose_category = 'hyperglycemia_severe' THEN 1 END) > 5 THEN 'ALERT'
        ELSE 'OK'
    END as day_status

FROM {{ ref('fct_glucose_readings') }}

WHERE reading_date >= CURRENT_DATE - INTERVAL '30' DAY

GROUP BY reading_date
ORDER BY reading_date DESC
```

**Note**: Marts are built in Iceberg first, then auto-published to Postgres.

### Auto-Publishing: Iceberg Marts → Postgres

Phlo automatically discovers dbt models in the `marts` schema and creates a `publish_marts_to_postgres` asset:

```python
# This is auto-generated by phlo_dagster.framework.discovery._discover_publishing_assets()
# You don't need to write this code - Phlo creates it automatically!

@asset(
    name="publish_marts_to_postgres",
    group_name="publishing",
    deps=[AssetKey("mrt_glucose_overview"), AssetKey("mrt_glucose_hourly_patterns")],
    kinds={"trino", "postgres"},
    description="Publish mart tables from Iceberg to PostgreSQL for BI",
)
def publish_marts_to_postgres(context):
    """Auto-generated publishing asset for dbt marts."""
    trino = TrinoResource()
    conn = trino.get_connection()
    cursor = conn.cursor()

    # Create marts schema in postgres if not exists
    cursor.execute("CREATE SCHEMA IF NOT EXISTS postgres.marts")

    # For each mart table discovered in dbt manifest:
    for table_name in ["mrt_glucose_overview", "mrt_glucose_hourly_patterns"]:
        source = f"iceberg.marts.{table_name}"
        target = f"postgres.marts.{table_name}"

        # Drop and recreate (simple refresh)
        cursor.execute(f"DROP TABLE IF EXISTS {target}")
        cursor.execute(f"CREATE TABLE {target} AS SELECT * FROM {source}")

        context.log.info(f"Published {table_name} to Postgres")
```

**How it works:**

1. Phlo scans the dbt `manifest.json` for models in the `marts` schema
2. Auto-generates a publishing asset with dependencies on those marts
3. Uses Trino to copy data from Iceberg (`iceberg.marts.*`) to Postgres (`postgres.marts.*`)

You don't need to write any publishing code - just create dbt models in the `marts` schema!

## Step 7: Running the Full Pipeline

### Materialize Everything

```bash
# Run all glucose assets for a specific date
phlo materialize \
  --select "dlt_glucose_entries,stg_glucose_entries,fct_glucose_readings,mrt_glucose_readings,publish_glucose_marts" \
  --partition 2024-10-15

# Output:
# Materializing dlt_glucose_entries [2024-10-15]
#   Successfully fetched 288 entries
#   Merged 288 rows to iceberg
#   Asset materialized in 2.45s
#
# Materializing stg_glucose_entries [2024-10-15]
#   dbt build completed
#   Asset materialized in 1.23s
#
# Materializing fct_glucose_readings [2024-10-15]
#   dbt run completed
#   Asset materialized in 3.42s
#
# Materializing mrt_glucose_readings [2024-10-15]
#   dbt run completed
#   Asset materialized in 1.15s
#
# Materializing publish_glucose_marts
#   Published 1 daily record to Postgres
#   Published 24 hourly records to Postgres
#   Asset materialized in 0.67s
#
# All assets materialized successfully in 8.92s
```

**In Dagster**:

```
http://localhost:10006
→ Assets tab
→ dlt_glucose_entries
→ Click to view lineage graph with status
```

**In Observatory**:

```
http://localhost:3001
→ Data Explorer
→ Browse marts.mrt_glucose_overview
→ Preview data and run queries
```

**In Postgres**:

```bash
docker exec -it pg psql -U phlo lakehouse

lakehouse=# SELECT * FROM marts.mrt_glucose_overview ORDER BY reading_date DESC LIMIT 1;

reading_date | avg_glucose_mg_dl | min_glucose_mg_dl | max_glucose_mg_dl | percent_in_range
──────────────────────────────────────────────────────────────────────────────────────────
2024-10-15   | 145.3             | 89                | 210               | 78.2
```


## Step 8: Monitoring and Alerts

### Quality Checks with @phlo_quality

Phlo provides two approaches for quality checks. The declarative `@phlo_quality` decorator:

```python
# File: phlo-examples/nightscout/workflows/quality/nightscout.py

import phlo
from phlo_quality import NullCheck, RangeCheck, FreshnessCheck

@phlo_quality(
    table="silver.fct_glucose_readings",
    checks=[
        NullCheck(columns=["entry_id", "glucose_mg_dl", "reading_timestamp"]),
        RangeCheck(column="glucose_mg_dl", min_value=20, max_value=600),
        RangeCheck(column="hour_of_day", min_value=0, max_value=23),
        FreshnessCheck(column="reading_timestamp", max_age_hours=24),
    ],
    group="nightscout",
    blocking=True,
)
def glucose_readings_quality():
    """Declarative quality checks for glucose readings using @phlo_quality."""
    pass
```

And the traditional `@asset_check` for custom logic:

```python
# File: phlo-examples/nightscout/workflows/quality/nightscout.py

from dagster import AssetCheckResult, AssetKey, asset_check
from workflows.schemas.nightscout import FactGlucoseReadings

@asset_check(
    name="nightscout_glucose_quality",
    asset=AssetKey(["fct_glucose_readings"]),
    blocking=True,
    description="Validate processed Nightscout glucose data using Pandera schema validation.",
)
def nightscout_glucose_quality_check(context, trino: TrinoResource) -> AssetCheckResult:
    """Quality check using Pandera for type-safe schema validation."""

    query = """
    SELECT
        entry_id, glucose_mg_dl, reading_timestamp, direction,
        hour_of_day, day_of_week, glucose_category, is_in_range
    FROM iceberg_dev.silver.fct_glucose_readings
    """

    with trino.cursor(schema="silver") as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

    fact_df = pd.DataFrame(rows, columns=columns)

    # Validate with Pandera schema
    try:
        FactGlucoseReadings.validate(fact_df, lazy=True)
        return AssetCheckResult(
            passed=True,
            metadata={
                "rows_validated": len(fact_df),
                "columns_validated": len(fact_df.columns),
            },
        )
    except pandera.errors.SchemaErrors as err:
        return AssetCheckResult(
            passed=False,
            metadata={
                "failed_checks": len(err.failure_cases),
                "failures_by_column": err.failure_cases.groupby("column").size().to_dict(),
            },
        )
```

**Alerts**: If checks fail:

- Dagster UI shows red
- 📧 Optional: send to Slack/email
- 🔔 Dashboard shows warnings

## Complete Data Flow Diagram

```
┌─ Nightscout API ─────────────────┐
│ 288 readings/day                  │
│ 5-min intervals                   │
└────────────┬──────────────────────┘

┌─ INGESTION (2.45s) ───────────────────────┐
│ dlt_glucose_entries                       │
│ ├─ Fetch from API (288 rows)              │
│ ├─ Validate with Pandera [PASSED]         │
│ ├─ Stage to S3 parquet                    │
│ └─ Merge to iceberg raw.glucose_entries   │
└────────────┬──────────────────────────────┘

┌─ TRANSFORM BRONZE (1.23s) ────────────────┐
│ stg_glucose_entries                       │
│ ├─ Type conversions                       │
│ ├─ Rename columns                         │
│ ├─ Filter nulls & out-of-range            │
│ └─ Create view in bronze.*                │
└────────────┬──────────────────────────────┘

┌─ TRANSFORM SILVER (3.42s) ────────────────┐
│ fct_glucose_readings                      │
│ ├─ Add time dimensions                    │
│ ├─ Classify glucose (hypo/in-range/hyper) │
│ ├─ Calculate rate of change (window fn)   │
│ └─ Create table in silver.*               │
└────────────┬──────────────────────────────┘

┌─ TRANSFORM GOLD (1.15s) ──────────────────┐
│ mrt_glucose_readings                      │
│ ├─ Aggregate by hour                      │
│ ├─ Calculate % time in range               │
│ ├─ Count by category                      │
│ └─ Create table in gold.*                 │
└────────────┬──────────────────────────────┘

┌─ PUBLISH (0.67s) ────────────────────────┐
│ publish_glucose_marts                    │
│ ├─ Query Iceberg gold tables              │
│ ├─ Truncate Postgres marts                │
│ └─ Insert results (1 daily + 24 hourly)   │
└────────────┬──────────────────────────────┘

┌─ ANALYTICS ───────────────────────┐
│ Superset Dashboard                │
│ ├─ Daily avg glucose: 145.3 mg/dL │
│ ├─ Time in range: 78.2%           │
│ ├─ Hourly patterns graph           │
│ └─ 30-day trend                    │
└───────────────────────────────────┘

Total pipeline time: 8.92s
```

## Key Takeaways

**End-to-end pipeline** from API to dashboard
**Idempotent ingestion** - safe to re-run
**Type-safe transformations** via dbt
**Data quality checks** with Pandera & Dagster
**Audit trail** via Nessie versioning
**Scalable** to millions of rows
**Observable** with logs, metrics, dashboards

This is real-world data engineering:

- Start with raw data (APIs, files, databases)
- Validate early (Pandera schemas)
- Transform incrementally (bronze → silver → gold)
- Publish for consumption (Postgres, dashboards)
- Monitor quality (tests, checks, alerts)

## Hands-On Exercise: Extend the Pipeline

1. Add one new source (GitHub, Fitbit, or weather) to the ingestion workflow.
2. Create a new dbt model to join it to `silver.fct_glucose_readings`.
3. Publish a new mart table to Postgres.
4. Build a simple Superset chart using the new data.

## Common Issues

- **Ingestion assets do not run**

```bash
phlo materialize dlt_glucose_entries
```


Fix: confirm the asset name and check Dagster logs.

- **dbt models fail to build**

```bash
docker exec dagster-webserver dbt run --select model_name
```


Fix: verify the model names and dbt profiles configuration.

- **Dashboards show no data**

```bash
phlo services logs postgres
```


Fix: confirm marts are loaded and the dashboard points at Postgres.

See [Troubleshooting Guide](../operations/troubleshooting.md) for deeper diagnostics.

## See Also

See also: [Part 5: Data Ingestion](05-data-ingestion.md), [Part 6: dbt Transformations](06-dbt-transformations.md), [Part 9: Data Quality with Pandera](09-data-quality-with-pandera.md). Reference: [Architecture Overview](../reference/architecture.md).


## Summary

You now understand:

- Modern data lakehouse architecture (Iceberg, Nessie)
- Complete ingestion pattern (DLT, PyIceberg)
- SQL transformation best practices (dbt layers)
- Production orchestration (Dagster assets)
- Data quality and testing
- Real-world example building dashboards

Time to build your own pipelines!

See the [main docs](../index.md) for API references, troubleshooting, and production deployment guides.

## Next Steps

- Continue with [Part 9: Data Quality with Pandera](09-data-quality-with-pandera.md).
- Review governance patterns in [Part 10: Metadata & Governance](10-metadata-governance.md).

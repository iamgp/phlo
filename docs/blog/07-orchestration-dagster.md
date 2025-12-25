# Part 7: Orchestration with Dagster—Running Your Pipelines

We have data flowing in (DLT + Iceberg) and transformations defined (dbt). Now: **Who runs this? When? What happens if it fails?**

That's **Dagster's job**—orchestration.

## The Orchestration Problem

Without orchestration:

```bash
# 6:00 AM
curl nightscout-api | dlt_ingest.py          # Manual - easy to forget
# 6:30 AM
dbt build                                      # Manual - depends on above
# 7:00 AM
publish_to_postgres.py                        # Manual - depends on dbt
# 7:30 AM (oops! API was down)
# Pipeline failed silently - nobody knows!
# Dashboards show stale data for 24 hours
```

With Dagster:

```
6:00 AM: Dagster scheduler triggers ingestion
         ↓ watches for completion
6:02 AM: Ingestion done → Dagster auto-triggers dbt
         ↓ watches for completion
6:04 AM: dbt done → Dagster auto-triggers publishing
         ↓ watches for completion
6:06 AM: All complete
         ↓
         If anything fails → Alert via email/Slack
```

## Dagster's Core Concepts

### 1. Assets (Declarative Data Dependencies)

Instead of telling Dagster "run this code", you declare:

- **What**: What data does this produce?
- **When**: When should it run?
- **Where**: Where does it come from?

```python
# Instead of: "Run this function at 6am"
# You declare: "This is an asset"

@dg.asset
def dlt_glucose_entries() -> MaterializeResult:
    """
    Produces: raw.glucose_entries table
    Source: Nightscout API
    """
    # Ingest data...
    return MaterializeResult(metadata={...})


@dg.asset
def dbt_bronze(dbt: DbtCliResource) -> None:
    """
    Produces: bronze.stg_glucose_entries
    Depends on: dlt_glucose_entries (auto-detected)
    """
    # Run dbt bronze models...
    dbt.cli(["build", "--select", "tag:bronze"])


@dg.asset(deps=[dbt_bronze])
def dbt_silver() -> None:
    """
    Produces: silver.fct_glucose_readings
    Depends on: dbt_bronze (explicit)
    """
    dbt.cli(["build", "--select", "tag:silver"])
```

Dagster automatically:

- Detects dependencies (bronze depends on ingestion)
- Builds DAG (directed acyclic graph)
- Executes in correct order
- Skips if already done (idempotent)
- Retries on failure
- Tracks lineage

### 2. Partitions (Time-Based Splitting)

Large datasets need splitting. Dagster partitions by time:

```python
# Define daily partitions starting from a date
from phlo_dagster.partitions import daily_partition

@dg.asset(
    partitions_def=daily_partition,
    description="Daily ingestion of glucose entries"
)
def dlt_glucose_entries(context) -> MaterializeResult:
    """
    Materialize for each day independently.

    Daily partition ensures:
    - Idempotency (re-run one day without affecting others)
    - Incremental loading (only process new data per day)
    - Easy recovery (re-run single failed day)
    """
    partition_date = context.partition_key  # "2024-10-15"

    # Fetch data for this date range only
    start = f"{partition_date}T00:00:00.000Z"
    end = f"{partition_date}T23:59:59.999Z"

    entries = fetch_from_nightscout(start, end)
    # ... ingest ...
    return MaterializeResult(metadata={...})
```

In the UI, you can materialize specific partitions:

```
Oct 14 (complete)
Oct 15 ⏳ (running)
Oct 16 (failed - can re-run)
Oct 17 ⚪ (not run yet)
```

### 3. Automation (Schedules & Sensors)

Run assets automatically:

**Schedule**: Run at specific times

```python
@dg.daily_schedule
def daily_ingestion():
    """Ingest new data every morning at 6 AM."""
    return dg.build_asset_context(
        partition_key=get_today_date()
    )
```

**Sensor**: Run when something happens

```python
@dg.sensor
def nightscout_api_sensor():
    """Ingest when new data available in Nightscout API."""
    if has_new_data():
        yield dg.SensorResult(
            cursor=get_latest_timestamp(),
            run_requests=[dg.RunRequest(tags={"source": "nightscout"})]
        )
```

In Phlo's code:

```python
# From workflows/ingestion/dlt_assets.py

@dg.asset(
    partitions_def=daily_partition,
    # ... other config ...
    automation_condition=dg.AutomationCondition.on_cron("0 */1 * * *"),
    # ^ Run every hour on :00 minute (0 * * * * = UTC cron format)
)
def entries(context) -> MaterializeResult:
    # Runs automatically hourly
    pass
```

### 4. Resources (Connections & Clients)

Instead of hardcoding connections, pass as resources:

```python
@dg.resource
def trino_resource(config) -> trino.dbapi.Connection:
    """Trino connection (configured via .env)."""
    return trino.dbapi.connect(
        host=config.trino_host,
        port=config.trino_port,
        user="phlo",
    )

@dg.resource
def iceberg_resource(config) -> IcebergCatalog:
    """PyIceberg catalog for Iceberg operations."""
    return get_catalog(ref="dev")

@dg.asset
def dlt_glucose_entries(iceberg: IcebergResource) -> MaterializeResult:
    """iceberg resource injected automatically."""
    # Use iceberg resource
    iceberg.ensure_table(...)
    iceberg.merge_parquet(...)
```

Resources are:

- Configured centrally (no hardcoding)
- Testable (swap real for mock)
- Shared across assets
- Lifecycle managed (connect/disconnect)

### 5. Asset Checks (Data Quality)

Beyond dbt tests, add explicit checks:

```python
@dg.asset_check(asset=dlt_glucose_entries)
def glucose_not_null(context) -> dg.AssetCheckResult:
    """Ensure no null glucose values."""

    table = get_table("raw.glucose_entries")
    null_count = table.scan().filter("sgv IS NULL").count()

    return dg.AssetCheckResult(
        passed=null_count == 0,
        metadata={
            "null_count": dg.MetadataValue.int(null_count),
            "total_rows": dg.MetadataValue.int(table.count_rows()),
        }
    )


@dg.asset_check(asset=fct_glucose_readings)
def range_check(context) -> dg.AssetCheckResult:
    """Ensure glucose values in physiologically plausible range."""

    table = get_table("silver.fct_glucose_readings")

    out_of_range = table.scan().filter(
        "(glucose_mg_dl < 20) OR (glucose_mg_dl > 600)"
    ).count()

    return dg.AssetCheckResult(
        passed=out_of_range == 0,
        metadata={
            "out_of_range_count": dg.MetadataValue.int(out_of_range),
        }
    )
```

Checks run after asset materialization:

```
dlt_glucose_entries (complete)
  ├─ Check: glucose_not_null [PASSED]
  └─ Check: row_count_increased [PASSED]
↓ (checks pass, continue)
dbt_bronze [SUCCESS]
```

## Phlo's Asset Graph

Here's Phlo's actual orchestration (simplified):

```
Sources
├── Nightscout API
└── GitHub API
    ↓
Ingestion Layer
├── dlt_glucose_entries (raw.glucose_entries)
├── dlt_github_user_events (raw.github_user_events)
└── Quality checks
    ↓
Transform Layer
├── stg_glucose_entries (bronze)
├── stg_github_user_events (bronze)
    ├── fct_glucose_readings (silver)
    ├── fct_github_user_events (silver)
        ├── dim_date (gold)
        ├── mrt_glucose_readings (gold)
        └── More metrics
            ↓
Publish Layer
├── mrt_glucose_overview (postgres)
├── mrt_glucose_hourly_patterns (postgres)
└── mrt_github_activity_overview (postgres)
    ↓
Analytics
└── Superset Dashboards
```

All dependencies auto-detected by Dagster:

```python
# File: workflows/ingestion/dlt_assets.py
@dg.asset(name="dlt_glucose_entries")
def entries() -> MaterializeResult:
    """Produces raw.glucose_entries"""
    pass

# File: workflows/transform/dbt.py
@dbt_assets(...)
def all_dbt_assets(dbt: DbtCliResource):
    """
    Produces bronze.*, silver.*, gold.*
    Depends on dlt_glucose_entries (via dbt source definition)
    """
    dbt.cli(["build"])

# Dagster automatically:
# - Sees dbt reads from dlt_glucose_entries
# - Waits for ingestion before running dbt
# - Re-runs dbt when ingestion changes
```

## Viewing the Lineage

Open Dagster UI (http://localhost:3000):

**Asset Graph**:

- Visual DAG of dependencies
- Color-coded by status (complete, ⏳ running, failed)
- Click to drill down

**Asset Details**:

```
dlt_glucose_entries
├── Dependencies
│   ├── Upstream: None (source)
│   └── Downstream: stg_glucose_entries
├── Recent Materializations
│   ├── 2024-10-15 10:30:00 (2.45s)
│   ├── 2024-10-15 09:30:00 (2.51s)
│   └── 2024-10-15 08:30:00 (2.48s)
├── Runs
│   └── 2024-10-15-103001 (view logs, re-run, etc.)
└── Metadata
    ├── rows_loaded: 288
    ├── rows_inserted: 288
    ├── partition: 2024-10-15
```

## Running Pipelines Manually

### Via UI

1. Open http://localhost:3000
2. Click asset: `stg_glucose_entries`
3. Click **Materialize this asset**
4. Select partition date (or use defaults)
5. Click **Materialize**
6. Watch progress in sidebar

### Via CLI

```bash
# Materialize single asset
docker exec dagster-webserver dagster asset materialize \
  --select dlt_glucose_entries

# Materialize with partition
docker exec dagster-webserver dagster asset materialize \
  --select dlt_glucose_entries \
  --partition "2024-10-15"

# Materialize multiple assets
docker exec dagster-webserver dagster asset materialize \
  --select "dlt_glucose_entries,stg_glucose_entries" \
  --partition "2024-10-15"

# Materialize all downstream of ingestion
docker exec dagster-webserver dagster asset materialize \
  --select "dlt_glucose_entries*"  # Asterisk = all downstream
```

### Via Python API

```python
# From workflows/...

from dagster import materialize

# Programmatic trigger
materialize(
    [dlt_glucose_entries],
    partition_key="2024-10-15"
)
```

## Backfilling Historical Data

Single materializations work for daily operations, but what about:

- Loading historical data when you first set up
- Re-processing after a bug fix
- Filling gaps from outages

That's where backfills come in.

### The Backfill Problem

```
Scenario: You fixed a bug in your glucose transformation.
Need to re-process the last 90 days.

Manual approach:
  for date in 2024-07-01 to 2024-09-30:
    phlo materialize glucose_entries --partition $date
    # Wait for each to complete...

Time: 90 days × 2 minutes = 3 hours of babysitting
```

### Using phlo backfill

The `phlo backfill` command handles date ranges intelligently:

```bash
# Backfill a date range
$ phlo backfill glucose_entries --start-date 2024-07-01 --end-date 2024-09-30

Backfill Plan: glucose_entries
══════════════════════════════

Date Range: 2024-07-01 to 2024-09-30
Partitions: 92 days
Estimated Time: ~45 minutes (parallel)

Proceed? [y/N] y

[1/92]  2024-07-01 ✓ (32s)
[2/92]  2024-07-02 ✓ (28s)
[3/92]  2024-07-03 ✓ (31s)
...
[92/92] 2024-09-30 ✓ (29s)

Backfill complete: 92 partitions in 43m
```

### Parallel Execution

For large backfills, run multiple partitions simultaneously:

```bash
# Run 4 partitions in parallel
$ phlo backfill glucose_entries \
    --start-date 2024-01-01 \
    --end-date 2024-12-31 \
    --parallel 4

Backfill Plan: glucose_entries
══════════════════════════════

Date Range: 2024-01-01 to 2024-12-31
Partitions: 365 days
Parallel Workers: 4
Estimated Time: ~90 minutes

[Worker 1] 2024-01-01 ✓
[Worker 2] 2024-01-02 ✓
[Worker 3] 2024-01-03 ✓
[Worker 4] 2024-01-04 ✓
[Worker 1] 2024-01-05 ✓
...
```

**Parallel considerations:**

- More workers = faster, but more resource usage
- Don't exceed your database connection pool
- Start with 2-4 workers, increase if stable

### Explicit Partitions

Sometimes you need specific dates, not a range:

```bash
# Only these specific dates
$ phlo backfill glucose_entries \
    --partitions 2024-01-01,2024-01-15,2024-02-01,2024-03-01
```

### Resuming Failed Backfills

If a backfill fails partway through (network issue, resource limits), resume it:

```bash
# Backfill gets interrupted at partition 45
$ phlo backfill glucose_entries --start-date 2024-01-01 --end-date 2024-03-31
...
[45/90] 2024-02-14 ✗ Connection timeout
Backfill interrupted. Run with --resume to continue.

# Later, resume from where it stopped
$ phlo backfill --resume

Resuming backfill: glucose_entries
Completed: 44/90
Remaining: 46 partitions

[45/90] 2024-02-14 ✓
[46/90] 2024-02-15 ✓
...
```

### Dry Run

Preview what will happen without executing:

```bash
$ phlo backfill glucose_entries \
    --start-date 2024-01-01 \
    --end-date 2024-01-31 \
    --dry-run

Backfill Plan (DRY RUN)
═══════════════════════

Asset: glucose_entries
Partitions to process: 31

  2024-01-01 (not materialized)
  2024-01-02 (not materialized)
  2024-01-03 (stale - upstream changed)
  2024-01-04 (not materialized)
  ...
  2024-01-15 (already fresh) <- would skip
  ...

Would process: 30 partitions
Would skip: 1 partition (already fresh)

Run without --dry-run to execute.
```

### Backfill Strategies

| Scenario           | Strategy                                          |
| ------------------ | ------------------------------------------------- |
| Initial load       | `--start-date` from earliest data, `--parallel 4` |
| Bug fix re-process | Date range of affected data, `--parallel 2`       |
| Fill gaps          | `--partitions` with explicit list                 |
| Monthly refresh    | `--start-date` first of month, `--end-date` last  |
| Testing            | `--dry-run` first, then small range               |

### Backfills in Production

For production backfills:

1. **Test first**: Run on a few partitions manually
2. **Monitor resources**: Watch CPU, memory, connections
3. **Off-peak hours**: Schedule large backfills overnight
4. **Incremental**: Better to run multiple smaller backfills than one huge one
5. **Notify team**: Large backfills can impact query performance

```bash
# Production backfill pattern
$ phlo backfill glucose_entries \
    --start-date 2024-01-01 \
    --end-date 2024-12-31 \
    --parallel 2 \           # Conservative parallelism
    --dry-run                # Preview first

# If dry-run looks good:
$ phlo backfill glucose_entries \
    --start-date 2024-01-01 \
    --end-date 2024-12-31 \
    --parallel 2
```

## Monitoring and Alerts

### Event Logging

Dagster logs every action:

```python
@dg.asset
def dlt_glucose_entries(context) -> MaterializeResult:
    # All logs captured
    context.log.info("Starting ingestion...")
    context.log.warning("Got 288 entries")
    context.log.error("Failed to connect to MinIO")

    # Metadata attached to run
    return dg.MaterializeResult(
        metadata={
            "rows_loaded": dg.MetadataValue.int(288),
            "duration_seconds": dg.MetadataValue.float(2.45),
            "partition": dg.MetadataValue.text("2024-10-15"),
        }
    )
```

View logs in Dagster UI → Runs → Click run → Logs tab

### Failure Monitoring

```python
@dg.sensor
def failure_alert_sensor(context):
    """Alert on pipeline failures."""

    failed_runs = context.instance.get_runs(
        filters=[
            DagsterRunStatus.FAILURE
        ],
        limit=10
    )

    for run in failed_runs:
        send_slack_alert(f"Pipeline failed: {run.asset_selection}")
```

### Freshness Policies

Ensure data is fresh:

```python
@dg.asset(
    freshness_policy=FreshnessPolicy(
        maximum_lag_minutes=60,  # Data must be <1hr old
        # If not met:
        # - ⚠️ Warning in UI
        # - Can trigger automatic re-run
    ),
    partitions_def=daily_partition
)
def dlt_glucose_entries() -> MaterializeResult:
    pass
```

## Configuration and Environment

Phlo uses `phlo/config.py` for centralized config:

```python
# phlo/config.py
from pydantic_settings import BaseSettings

class PhloConfig(BaseSettings):
    # Iceberg
    iceberg_warehouse_path: str = "s3://lake/warehouse"
    iceberg_staging_path: str = "s3://lake/stage"

    # Nessie
    nessie_uri: str = "http://nessie:19120"
    nessie_branch: str = "dev"

    # Trino
    trino_host: str = "trino"
    trino_port: int = 8080

    class Config:
        env_file = ".env"  # Read from .env

config = PhloConfig()  # Singleton
```

In assets:

```python
@dg.asset
def dlt_glucose_entries(context, iceberg: IcebergResource) -> MaterializeResult:
    context.log.info(f"Using warehouse: {config.iceberg_warehouse_path}")
    context.log.info(f"Using branch: {config.nessie_branch}")
    # ...
```

## Advanced: Custom Ops and Jobs

For complex workflows, you can define Jobs (lower-level than assets):

```python
# Assets are preferred, but sometimes you need Jobs

from dagster import op, job

@op
def fetch_data():
    return requests.get(...).json()

@op
def validate_data(data):
    return pandera_schema.validate(data)

@op
def write_to_iceberg(data):
    iceberg.merge_parquet(...)

@job
def ingestion_pipeline():
    """Explicit workflow if you need more control."""
    data = fetch_data()
    validated = validate_data(data)
    write_to_iceberg(validated)

# Most of Phlo uses Assets instead (more declarative)
```

## Performance Considerations

### Dagster Daemon

The daemon runs scheduled assets:

```
Dagster Daemon
├── Runs scheduled assets
├── Monitors sensors
└── Manages run queue
```

In Docker:

```yaml
dagster-daemon:
  image: dagster/dagster:1.8.0
  command: dagster-daemon run
  depends_on:
    - postgres
    - dagster-webserver
```

The daemon needs:

- Access to PostgreSQL (run history)
- Access to code (asset definitions)
- Compute resources (run actual ops)

### Concurrency

By default, Dagster runs one partition at a time. For parallel:

```python
@dg.asset(
    partitions_def=daily_partition,
    # Run up to 4 partitions in parallel
    automation_condition=dg.AutomationCondition.eager(),
    tags={"dagster/max_concurrency": 4}
)
def dlt_glucose_entries() -> MaterializeResult:
    pass
```

## Next: Data Quality

Orchestration keeps pipelines running. But are they running _correctly_?

**Part 8: Data Quality and Testing**

See you there!

## Summary

**Dagster provides**:

- Asset-based orchestration (declare dependencies)
- Automatic scheduling (run on cron)
- Partitioning (split by time)
- Lineage tracking (visual DAG)
- Error handling and retries
- Monitoring and alerting

**In Phlo**:

- Assets for ingestion, transformation, publishing
- Daily partitions for scalability
- Automatic dependency resolution
- Asset checks for data quality
- Freshness policies for monitoring

**Key Pattern**: Declare assets, Dagster handles orchestration.

**Next**: [Part 8: Real-World Example—Building a Complete Data Pipeline](08-real-world-example.md)

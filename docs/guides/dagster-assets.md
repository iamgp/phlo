# Dagster Assets Tutorial

## Mastering Asset-Based Orchestration

This guide teaches you everything about Dagster assets in Cascade - from basics to advanced patterns.

---

## Table of Contents

1. [Asset Basics](#asset-basics)
2. [Asset Dependencies](#asset-dependencies)
3. [Resources and Configuration](#resources-and-configuration)
4. [Partitions](#partitions)
5. [Asset Checks and Quality](#asset-checks-and-quality)
6. [Schedules and Sensors](#schedules-and-sensors)
7. [Advanced Patterns](#advanced-patterns)
8. [Troubleshooting](#troubleshooting)

---

## Asset Basics

### What is an Asset?

An **asset** is a piece of data that you want to create and maintain.

**Examples:**
- A table in Iceberg
- A file in S3
- A machine learning model
- A dashboard

**Key concept:** You declare **what** you want (the asset), not **how** to create it (the task).

### Your First Asset

```python
import dagster as dg

@dg.asset
def my_first_asset():
    """A simple asset that returns data."""
    return [1, 2, 3, 4, 5]
```

That's it! Dagster will:
- Track when it was last materialized
- Let you materialize it on-demand
- Show it in the UI

### Materializing an Asset

**In the UI:**
1. Open http://localhost:3000
2. Click "Assets"
3. Find your asset
4. Click "Materialize"

**CLI:**
```bash
dagster asset materialize -m cascade.definitions -a my_first_asset
```

**Programmatically:**
```python
from dagster import materialize

result = materialize([my_first_asset])
```

### Asset Context

Get information about the current run:

```python
@dg.asset
def asset_with_context(context: dg.AssetExecutionContext):
    """Asset that uses context."""

    # Logging
    context.log.info("Starting materialization")
    context.log.warning("This is a warning")
    context.log.error("This is an error")

    # Asset info
    context.log.info(f"Asset key: {context.asset_key}")
    context.log.info(f"Run ID: {context.run_id}")

    # Partition info (if partitioned)
    if context.has_partition_key:
        context.log.info(f"Partition: {context.partition_key}")

    return "data"
```

### Asset Metadata

Return metadata about your materialization:

```python
@dg.asset
def asset_with_metadata(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """Asset that returns metadata."""

    data = fetch_data()

    return dg.MaterializeResult(
        metadata={
            "num_records": len(data),
            "preview": dg.MetadataValue.md(data.head().to_markdown()),
            "row_count": dg.MetadataValue.int(len(data)),
            "schema": dg.MetadataValue.json({"columns": list(data.columns)}),
        }
    )
```

Metadata shows up in the Dagster UI!

### Asset Configuration

Add configuration to your assets:

```python
@dg.asset(
    name="configured_asset",
    description="This asset has configuration",
    compute_kind="python",
    group_name="my_group",
    tags={"owner": "data_team", "priority": "high"},
)
def configured_asset(context: dg.AssetExecutionContext):
    """Asset with configuration."""
    return "data"
```

**Parameters:**
- `name`: Asset name (default: function name)
- `description`: Shows in UI
- `compute_kind`: Badge showing technology (python, sql, spark, etc.)
- `group_name`: Organize related assets
- `tags`: Key-value labels for filtering

---

## Asset Dependencies

### Declaring Dependencies

**Method 1: Function parameter**

```python
@dg.asset
def upstream_asset():
    return [1, 2, 3]

@dg.asset
def downstream_asset(upstream_asset):  # Depends on upstream_asset
    """This asset depends on upstream_asset."""
    data = upstream_asset  # Gets the return value
    return [x * 2 for x in data]
```

Dagster automatically:
- Knows `downstream_asset` depends on `upstream_asset`
- Materializes `upstream_asset` first
- Passes its return value to `downstream_asset`

**Method 2: deps parameter**

```python
@dg.asset(
    deps=["upstream_asset"]  # Depends but doesn't need the data
)
def downstream_asset():
    """This runs after upstream_asset but doesn't use its data."""
    # Fetch data from database instead
    return query_database()
```

Use `deps` when:
- You don't need the upstream asset's return value
- The upstream asset writes to a database/storage
- You just need it to run first

**Method 3: AssetKey**

```python
@dg.asset(
    deps=[dg.AssetKey(["schema", "table_name"])]
)
def asset_with_key_dep():
    """Depend on asset by key."""
    return "data"
```

### Multi-Asset Dependencies

```python
@dg.asset
def asset_a():
    return "A"

@dg.asset
def asset_b():
    return "B"

@dg.asset
def asset_c(asset_a, asset_b):  # Depends on both
    """Combines data from A and B."""
    return f"{asset_a} + {asset_b}"
```

Graph:
```
asset_a ─┐
         ├─> asset_c
asset_b ─┘
```

### Conditional Dependencies

```python
from cascade.config import get_config

@dg.asset
def optional_upstream():
    return "data"

@dg.asset
def conditional_asset():
    """Conditionally uses upstream asset."""
    config = get_config()

    if config.USE_CACHE:
        # Use upstream asset
        return load_from_cache()
    else:
        # Fetch fresh
        return fetch_fresh_data()
```

---

## Resources and Configuration

### What are Resources?

**Resources** are external services your assets need:
- Databases (Trino, Postgres)
- APIs (Iceberg catalog)
- File systems (S3)
- External services

### Using Resources

```python
from cascade.defs.resources import TrinoResource, IcebergResource

@dg.asset
def asset_with_resources(
    trino: TrinoResource,
    iceberg: IcebergResource,
):
    """Asset that uses resources."""

    # Query with Trino
    results = trino.execute("SELECT * FROM iceberg.raw.my_table")

    # Write to Iceberg
    iceberg.append_parquet("silver.processed_table", results)

    return len(results)
```

Resources are automatically injected by Dagster!

### Creating Custom Resources

```python
from dagster import ConfigurableResource
import requests

class WeatherAPIResource(ConfigurableResource):
    """Resource for weather API."""

    api_key: str
    base_url: str = "https://api.openweathermap.org/data/2.5"

    def get_weather(self, city: str) -> dict:
        """Fetch weather for a city."""
        url = f"{self.base_url}/weather"
        params = {"q": city, "appid": self.api_key}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()


# Register resource
def build_resources():
    return dg.Definitions(
        resources={
            "weather_api": WeatherAPIResource(
                api_key=get_config().WEATHER_API_KEY,
            ),
        },
    )
```

**Use it:**
```python
@dg.asset
def weather_data(weather_api: WeatherAPIResource):
    """Fetch weather data."""
    return weather_api.get_weather("London")
```

### Configuration from Environment

```python
from cascade.config import get_config

@dg.asset
def configured_asset(context: dg.AssetExecutionContext):
    """Asset that uses config."""
    config = get_config()

    context.log.info(f"Using API: {config.API_BASE_URL}")
    context.log.info(f"Batch size: {config.BATCH_SIZE}")

    # Use configuration
    return fetch_data(
        url=config.API_BASE_URL,
        batch_size=config.BATCH_SIZE,
    )
```

---

## Partitions

### What are Partitions?

**Partitions** let you process data incrementally instead of all at once.

**Example:** Instead of processing all historical data every time, process one day at a time.

### Daily Partitions

```python
from dagster import DailyPartitionsDefinition

daily_partition = DailyPartitionsDefinition(start_date="2024-01-01")

@dg.asset(
    partitions_def=daily_partition,
)
def daily_weather_data(context: dg.AssetExecutionContext):
    """Fetch weather data for one day."""

    # Get the partition we're processing
    date = context.partition_key  # "2024-11-05"

    context.log.info(f"Processing date: {date}")

    # Fetch only data for this date
    data = fetch_weather_for_date(date)

    return data
```

**Benefits:**
- Process incrementally (one day at a time)
- Backfill missing dates easily
- Re-process specific dates if needed
- Parallel processing of partitions

### Materializing Partitions

**Single partition:**
```bash
dagster asset materialize -m cascade.definitions \
  -a daily_weather_data \
  --partition 2024-11-05
```

**Range of partitions:**
```bash
# Backfill last 7 days
dagster asset backfill -m cascade.definitions \
  -a daily_weather_data \
  --from 2024-11-01 \
  --to 2024-11-07
```

**Latest partition:**
```bash
dagster asset materialize -m cascade.definitions \
  -a daily_weather_data \
  --partition $(date +%Y-%m-%d)
```

### Hourly Partitions

```python
from dagster import HourlyPartitionsDefinition

hourly_partition = HourlyPartitionsDefinition(start_date="2024-01-01-00:00")

@dg.asset(
    partitions_def=hourly_partition,
)
def hourly_traffic_data(context: dg.AssetExecutionContext):
    """Fetch traffic data for one hour."""
    hour = context.partition_key  # "2024-11-05-14:00"
    return fetch_traffic_for_hour(hour)
```

### Static Partitions

```python
from dagster import StaticPartitionsDefinition

city_partition = StaticPartitionsDefinition(
    ["london", "new_york", "tokyo", "sydney"]
)

@dg.asset(
    partitions_def=city_partition,
)
def city_weather_data(context: dg.AssetExecutionContext):
    """Fetch weather for one city."""
    city = context.partition_key  # "london"
    return fetch_weather_for_city(city)
```

### Multi-Dimensional Partitions

```python
from dagster import MultiPartitionsDefinition

multi_partition = MultiPartitionsDefinition({
    "date": daily_partition,
    "city": city_partition,
})

@dg.asset(
    partitions_def=multi_partition,
)
def multi_partitioned_data(context: dg.AssetExecutionContext):
    """Process by date AND city."""
    partition_key = context.partition_key
    # partition_key.keys_by_dimension = {"date": "2024-11-05", "city": "london"}

    date = partition_key.keys_by_dimension["date"]
    city = partition_key.keys_by_dimension["city"]

    return fetch_weather(city, date)
```

---

## Asset Checks and Quality

### Asset Checks

**Asset checks** validate data quality without failing the materialization.

```python
from dagster import asset_check, AssetCheckResult

@dg.asset
def my_data():
    """Create some data."""
    return [{"value": x} for x in range(100)]

@asset_check(asset=my_data)
def check_data_not_empty(my_data):
    """Check that data is not empty."""
    if len(my_data) == 0:
        return AssetCheckResult(
            passed=False,
            description="Data is empty!",
        )

    return AssetCheckResult(
        passed=True,
        description=f"Data has {len(my_data)} records",
        metadata={"record_count": len(my_data)},
    )

@asset_check(asset=my_data)
def check_data_values(my_data):
    """Check data values are in expected range."""
    values = [d["value"] for d in my_data]
    min_val = min(values)
    max_val = max(values)

    if min_val < 0 or max_val > 1000:
        return AssetCheckResult(
            passed=False,
            description=f"Values out of range: {min_val} to {max_val}",
        )

    return AssetCheckResult(
        passed=True,
        description="All values in range",
        metadata={"min": min_val, "max": max_val},
    )
```

### Freshness Checks

Ensure data is up-to-date:

```python
from dagster import build_last_update_freshness_checks
from datetime import timedelta

# Automatically check freshness
freshness_checks = build_last_update_freshness_checks(
    assets=[my_data],
    lower_bound_delta=timedelta(hours=1),  # Must be updated within 1 hour
)
```

### Data Quality with Pandera

Use Pandera for schema validation:

```python
import pandera as pa
from pandera.typing import Series
from dagster_pandera import pandera_schema_to_dagster_type

class MyDataSchema(pa.DataFrameModel):
    """Schema for my data."""
    id: Series[int] = pa.Field(ge=0)
    value: Series[float] = pa.Field(ge=0, le=100)
    name: Series[str]

    class Config:
        coerce = True
        strict = True

# Use as type hint
@dg.asset
def validated_data() -> pandera_schema_to_dagster_type(MyDataSchema):
    """Data with automatic validation."""
    import pandas as pd

    df = pd.DataFrame({
        "id": [1, 2, 3],
        "value": [10.5, 20.3, 30.1],
        "name": ["A", "B", "C"],
    })

    # Validation happens automatically!
    return df
```

---

## Schedules and Sensors

### Schedules

Run assets on a schedule:

```python
@dg.schedule(
    name="daily_weather_schedule",
    cron_schedule="0 2 * * *",  # Daily at 2 AM
    job=dg.define_asset_job(
        name="weather_job",
        selection=dg.AssetSelection.groups("weather"),
    ),
    execution_timezone="UTC",
    default_status=dg.DefaultScheduleStatus.RUNNING,
)
def daily_weather_schedule():
    """Run weather pipeline daily."""
    return dg.RunRequest()
```

**Cron examples:**
```
"0 * * * *"      # Every hour
"0 0 * * *"      # Daily at midnight
"0 2 * * *"      # Daily at 2 AM
"0 0 * * 0"      # Weekly on Sunday
"0 0 1 * *"      # Monthly on 1st
"*/15 * * * *"   # Every 15 minutes
```

### Sensors

React to events:

```python
@dg.sensor(
    name="file_sensor",
    minimum_interval_seconds=60,  # Check every minute
)
def file_arrival_sensor(context: dg.SensorEvaluationContext):
    """Trigger when new file arrives."""

    # Check for new files
    files = list_files_in_bucket("s3://my-bucket/incoming/")

    if not files:
        return dg.SkipReason("No new files")

    # Trigger job for each file
    for file in files:
        yield dg.RunRequest(
            run_key=file,  # Unique key to avoid duplicates
            tags={"file_path": file},
        )
```

### Freshness Sensors

Alert on stale data:

```python
@dg.sensor(
    name="data_freshness_sensor",
    minimum_interval_seconds=300,  # Check every 5 minutes
    default_status=dg.DefaultSensorStatus.RUNNING,
)
def data_freshness_sensor(context: dg.SensorEvaluationContext):
    """Alert if data is stale."""

    asset_key = dg.AssetKey(["my_important_data"])
    last_materialization = context.instance.get_latest_materialization_event(asset_key)

    if not last_materialization:
        return dg.SkipReason("No materialization yet")

    from datetime import datetime, timedelta
    age = datetime.now().timestamp() - last_materialization.timestamp
    max_age = timedelta(hours=2).total_seconds()

    if age > max_age:
        context.log.error(f"Data is {age/3600:.1f} hours old!")
        # Trigger rematerialization
        return dg.RunRequest(asset_selection=[asset_key])

    return dg.SkipReason(f"Data is fresh ({age/3600:.1f} hours)")
```

---

## Advanced Patterns

### Pattern 1: Dynamic Assets

Generate assets programmatically:

```python
CITIES = ["london", "new_york", "tokyo"]

def build_city_assets():
    """Generate asset for each city."""
    assets = []

    for city in CITIES:
        @dg.asset(name=f"weather_{city}")
        def city_weather_asset():
            return fetch_weather(city)

        assets.append(city_weather_asset)

    return assets
```

### Pattern 2: Multi-Asset

One function creates multiple assets:

```python
@dg.multi_asset(
    outs={
        "customers": dg.AssetOut(),
        "orders": dg.AssetOut(),
        "products": dg.AssetOut(),
    },
)
def extract_from_api():
    """Extract multiple entities from API."""

    api_data = fetch_all_data()

    return (
        api_data["customers"],  # customers asset
        api_data["orders"],     # orders asset
        api_data["products"],   # products asset
    )
```

### Pattern 3: Observable Source Assets

Track external data you don't create:

```python
@dg.observable_source_asset
def external_api_data(context: dg.AssetExecutionContext):
    """Track external API without ingesting."""

    # Check external source
    last_updated = get_api_last_updated_time()

    return dg.ObserveResult(
        metadata={
            "last_updated": last_updated.isoformat(),
            "record_count": get_api_record_count(),
        }
    )
```

### Pattern 4: Asset Factories

Reusable asset patterns:

```python
def create_ingestion_asset(source_name: str, table_name: str):
    """Factory function for ingestion assets."""

    @dg.asset(
        name=f"ingest_{source_name}_{table_name}",
        group_name=source_name,
    )
    def ingestion_asset(
        context: dg.AssetExecutionContext,
        iceberg: IcebergResource,
    ):
        """Ingest data from source."""
        data = fetch_from_source(source_name, table_name)
        iceberg.append_parquet(f"raw.{table_name}", data)
        return len(data)

    return ingestion_asset

# Create multiple assets
assets = [
    create_ingestion_asset("salesforce", "accounts"),
    create_ingestion_asset("salesforce", "opportunities"),
    create_ingestion_asset("stripe", "payments"),
]
```

### Pattern 5: Retry Logic

Add automatic retries:

```python
@dg.asset(
    retry_policy=dg.RetryPolicy(
        max_retries=3,
        delay=30,  # seconds between retries
        backoff=dg.Backoff.EXPONENTIAL,  # 30s, 60s, 120s
    ),
)
def asset_with_retries():
    """Automatically retries on failure."""
    return fetch_unreliable_api()
```

### Pattern 6: Asset Versioning

Track versions of your assets:

```python
@dg.asset(
    code_version="v2.0",  # Update when logic changes
)
def versioned_asset():
    """Asset with version tracking."""
    return compute_data_v2()
```

Dagster tracks version changes in UI!

### Pattern 7: IO Managers

Custom storage for assets:

```python
from dagster import IOManager, io_manager

class IcebergIOManager(IOManager):
    """Custom IO manager for Iceberg tables."""

    def __init__(self, iceberg_resource):
        self.iceberg = iceberg_resource

    def handle_output(self, context, obj):
        """Save asset to Iceberg."""
        table_name = f"raw.{context.asset_key.path[-1]}"
        self.iceberg.append_parquet(table_name, obj)

    def load_input(self, context):
        """Load asset from Iceberg."""
        table_name = f"raw.{context.asset_key.path[-1]}"
        return self.iceberg.read_table(table_name)

@io_manager
def iceberg_io_manager(iceberg: IcebergResource):
    return IcebergIOManager(iceberg)
```

---

## Troubleshooting

### Asset Not Showing in UI

**Check:**
1. Is it registered in definitions?
   ```python
   defs = dg.Definitions(assets=[my_asset])
   ```

2. Restart Dagster:
   ```bash
   docker-compose restart dagster-webserver dagster-daemon
   ```

3. Check logs:
   ```bash
   docker-compose logs dagster-webserver
   ```

### Asset Fails to Materialize

**Debug steps:**
1. Check logs in Dagster UI (Runs → Failed run → Logs)

2. Run locally:
   ```python
   from cascade.definitions import defs
   from dagster import materialize

   result = materialize([defs.get_asset_def("my_asset")])
   print(result)
   ```

3. Check dependencies materialized

4. Verify resources configured

### Asset Dependencies Not Working

**Common issues:**

1. Typo in asset name:
   ```python
   # Wrong
   def downstream(upsteam_asset):  # Typo!
       pass

   # Correct
   def downstream(upstream_asset):
       pass
   ```

2. Asset not in same definitions:
   ```python
   # Must merge definitions
   defs = dg.Definitions.merge(
       build_ingestion_defs(),  # Contains upstream
       build_transform_defs(),   # Contains downstream
   )
   ```

### Partition Errors

**Common issues:**

1. Partition key not found:
   ```python
   # Check partition exists
   context.log.info(f"Partition: {context.partition_key}")
   ```

2. Partition dependency mismatch:
   ```python
   # Both assets must use same partition definition
   @asset(partitions_def=daily_partition)
   def upstream(): ...

   @asset(partitions_def=daily_partition)  # Must match!
   def downstream(upstream): ...
   ```

### Slow Asset Materialization

**Optimization:**

1. Add partitioning (process incrementally)

2. Use incremental dbt models

3. Parallelize with multi-asset

4. Optimize queries (add indexes, filters)

5. Increase resources:
   ```yaml
   # docker-compose.yml
   dagster-webserver:
     deploy:
       resources:
         limits:
           cpus: '2'
           memory: 4G
   ```

---

## Summary

**Key Concepts:**
- **Assets** = Data you want to create
- **Dependencies** = What depends on what
- **Resources** = External services
- **Partitions** = Process incrementally
- **Checks** = Validate quality
- **Schedules** = Time-based triggers
- **Sensors** = Event-based triggers

**Best Practices:**
- ✅ Use meaningful asset names
- ✅ Add descriptions and metadata
- ✅ Group related assets
- ✅ Add data quality checks
- ✅ Use partitions for large datasets
- ✅ Log important information
- ✅ Handle errors gracefully

**Next:** [Troubleshooting Guide](../operations/troubleshooting.md) - Debug common issues.

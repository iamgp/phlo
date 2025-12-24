# 10-Minute Quickstart

Get Phlo running and see your first data pipeline in action in under 10 minutes.

## What You'll Build

A simple glucose data ingestion pipeline that:
1. Fetches data from Nightscout API
2. Validates with Pandera schemas
3. Stores in Apache Iceberg table
4. Views in Dagster UI

## Prerequisites

- Docker and Docker Compose
- 10 minutes
- Text editor

## Step 1: Clone and Setup (2 minutes)

```bash
git clone https://github.com/iamgp/phlo.git
cd phlo

# Copy environment template
cp .env.example .env
# Edit .env if needed (defaults work for local development)

# Start core services
make up-core up-query
```

Wait for services to start (~60 seconds).

## Step 2: View Dagster UI (30 seconds)

```bash
make dagster
# Opens http://localhost:10006
```

You'll see the existing glucose ingestion asset already defined!

## Step 3: Understand the Asset (2 minutes)

Open `workflows/ingestion/nightscout/glucose.py`:

```python
from dlt.sources.rest_api import rest_api
import phlo
from workflows.schemas.glucose import RawGlucoseEntries

@phlo_ingestion(
    table_name="glucose_entries",
    unique_key="_id",
    validation_schema=RawGlucoseEntries,
    group="nightscout",
    cron="0 */1 * * *",
    freshness_hours=(1, 24),
)
def glucose_entries(partition_date: str):
    """Ingest Nightscout glucose entries."""
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

**Notice**: Only 60 lines! The `@phlo_ingestion` decorator handles:
- DLT pipeline setup
- Pandera validation
- Iceberg table creation
- Merge with deduplication
- Timing instrumentation

## Step 4: Materialize the Asset (1 minute)

```bash
# Materialize for today's date
docker exec dagster-webserver dagster asset materialize --select glucose_entries

# Or in Dagster UI:
# Navigate to Assets → glucose_entries → Materialize
```

Watch the execution in the Dagster UI. You'll see:
1. DLT fetching data from API
2. Pandera validation
3. Staging to parquet
4. Merge to Iceberg

## Step 5: Query Your Data (2 minutes)

### Option A: Trino (SQL)

```bash
# Connect to Trino
docker exec -it trino trino --catalog iceberg_dev --schema raw

# Query your data
SELECT _id, sgv, dateString
FROM glucose_entries
ORDER BY dateString DESC
LIMIT 10;
```

### Option B: DuckDB (local analysis)

```python
import duckdb

conn = duckdb.connect()

# Install Iceberg extension
conn.execute("INSTALL iceberg;")
conn.execute("LOAD iceberg;")

# Query Iceberg table (adapt path to your MinIO endpoint)
result = conn.execute("""
    SELECT _id, sgv, dateString
    FROM iceberg_scan('s3://warehouse/raw/glucose_entries', ...)
    LIMIT 10
""").df()

print(result)
```

## What You Just Did

In 10 minutes, you:
1. Started Phlo's lakehouse platform
2. Explored an ingestion asset
3. Materialized data to Iceberg
4. Queried with SQL engines

**Key Concepts**:
- **Decorator-driven**: Minimal boilerplate with `@phlo_ingestion`
- **Schema-first**: Pandera validates data quality
- **Iceberg tables**: ACID transactions, time travel, schema evolution
- **Multi-engine**: Query with Trino, DuckDB, Spark

## Next Steps

### Create Your Own Ingestion Asset (15 minutes)

1. Define schema in `workflows/schemas/mydata.py`:

```python
import pandera as pa
from pandera.typing import Series

class RawWeatherData(pa.DataFrameModel):
    city_name: Series[str] = pa.Field(description="City name")
    temperature: Series[float] = pa.Field(ge=-50, le=50)
    timestamp: Series[str] = pa.Field(description="ISO 8601 timestamp")

    class Config:
        strict = True
        coerce = True
```

2. Create asset in `workflows/ingestion/weather/observations.py`:

```python
from dlt.sources.rest_api import rest_api
import phlo
from workflows.schemas.mydata import RawWeatherData

@phlo_ingestion(
    table_name="weather_observations",
    unique_key="timestamp",
    validation_schema=RawWeatherData,
    group="weather",
    cron="0 */1 * * *",
    freshness_hours=(1, 24),
)
def weather_observations(partition_date: str):
    """Ingest weather observations."""
    # TODO: Replace with your API
    source = rest_api({
        "client": {
            "base_url": "https://api.openweathermap.org/data/3.0",
            "auth": {"token": "YOUR_API_KEY"}
        },
        "resources": [{
            "name": "observations",
            "endpoint": {
                "path": "onecall/timemachine",
                "params": {"dt": partition_date}
            }
        }]
    })
    return source
```

3. No manual registration is needed. Phlo discovers assets under `workflows/`.

4. Restart Dagster:

```bash
docker restart dagster-webserver
```

5. Materialize in UI!

### Build Complete Pipeline (60 minutes)

Follow the comprehensive tutorial:
- **[Workflow Development Guide](../guides/workflow-development.md)** (42KB, 10-step tutorial)

This covers:
- Bronze/Silver/Gold layers with dbt
- Data quality checks
- Publishing to Postgres
- Scheduling and automation

### Explore Advanced Features

- **Time Travel**: Query historical snapshots
- **Git-like Branching**: Nessie for data versioning
- **Data Catalog**: OpenMetadata integration
- **Observability**: Grafana dashboards

## Learning Resources

- **Concepts**: [Core Concepts](core-concepts.md) - Understand lakehouse fundamentals
- **Complete Tutorial**: [Workflow Development Guide](../guides/workflow-development.md) - Build full pipeline
- **Best Practices**: [Best Practices Guide](../operations/best-practices.md) - Production patterns
- **Architecture**: [Architecture](../reference/architecture.md) - System design
- **Troubleshooting**: [Troubleshooting Guide](../operations/troubleshooting.md) - Common issues

## Common Issues

**"Services won't start"**
```bash
# Check Docker is running
docker ps

# Check logs
make logs

# Restart services
make down
make up-core up-query
```

**"Asset not showing in UI"**
```bash
# Restart Dagster webserver
docker restart dagster-webserver

# Ensure asset file lives under workflows/ and imports cleanly
```

**"Validation failed"**
```bash
# Check schema matches your data types
# Common issue: timestamp as datetime instead of string
# Review Pandera schema in workflows/schemas/
```

**"Permission denied in MinIO"**
```bash
# Check .env has correct MinIO credentials
# Default: MINIO_ROOT_USER=minioadmin, MINIO_ROOT_PASSWORD=minioadmin
```

## Why Phlo?

**74% less boilerplate** vs manual Dagster/Iceberg/DLT integration:

| Operation | Manual Code | With Phlo | Reduction |
|-----------|-------------|--------------|-----------|
| DLT setup | ~50 lines | 0 lines | 100% |
| Iceberg schema | ~40 lines | 0 lines (auto-generated) | 100% |
| Merge logic | ~60 lines | 0 lines | 100% |
| Error handling | ~40 lines | 0 lines | 100% |
| Timing/logging | ~30 lines | 0 lines | 100% |
| **Total** | **~270 lines** | **~60 lines** | **74%** |

**Unique Features**:
- Git-like branching for data (Nessie)
- Time travel queries (Iceberg)
- Schema auto-generation (Pandera → PyIceberg)
- Idempotent ingestion (deduplication built-in)
- Multi-engine analytics (Trino, DuckDB, Spark)

## Get Help

- **Documentation**: [docs/index.md](./index.md)
- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share ideas

**Next**: [Complete Tutorial](../guides/workflow-development.md) | [Best Practices](../operations/best-practices.md)

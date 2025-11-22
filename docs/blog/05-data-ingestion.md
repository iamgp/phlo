# Part 5: Data Ingestion—Getting Data Into the Lakehouse

We have our lakehouse infrastructure. Now: **how does data actually get in?**

Phlo uses a two-step pattern:
1. **DLT (Data Load Tool)**: Fetch and stage data
2. **PyIceberg**: Merge staged data into Iceberg tables

## The Two-Step Ingestion Pattern

Why two steps instead of one?

```
Single Step (Risky)
    External API
      ↓ (network fails?)
    Iceberg Table
      (Corruption if interrupted)

Two Steps (Safe)
    External API
      ↓ (network fails? No problem, retry)
    S3 Staging (Temporary)
      ↓ (Has backup of raw data)
    Iceberg Table
      (Merge with idempotent deduplication)
```

The two-step pattern ensures:
-  If network fails during fetch → restart from API
- 📦 If staging fails → S3 has backup
-  If merge fails → can retry with same data
-  Idempotent: run multiple times safely

## Step 1: DLT (Data Load Tool)

DLT is a Python library that:
- Fetches data from sources
- Normalizes schema (makes consistent)
- Stages to parquet files

### How DLT Works

```python
# From src/phlo/defs/ingestion/dlt_assets.py

import dlt
import requests

@dg.asset
def entries(context) -> MaterializeResult:
    """Ingest Nightscout glucose entries."""
    
    # 1. Fetch from API
    response = requests.get("https://gwp-diabetes.fly.dev/api/v1/entries.json",
        params={
            "count": "10000",
            "find[dateString][$gte]": start_time_iso,
            "find[dateString][$lt]": end_time_iso,
        }
    )
    entries_data = response.json()  # List of dicts
    
    # 2. Configure DLT pipeline
    local_staging_root = Path.home() / ".dlt" / "pipelines" / "partitioned"
    local_staging_root.mkdir(parents=True, exist_ok=True)

    filesystem_destination = dlt.destinations.filesystem(
        bucket_url=local_staging_root.as_uri(),
    )

    pipeline = dlt.pipeline(
        pipeline_name="nightscout_entries_2024_10_15",
        destination=filesystem_destination,
        dataset_name="nightscout",
        pipelines_dir=str(local_staging_root)
    )
    
    # 3. Define DLT resource
    @dlt.resource(name="entries", write_disposition="replace")
    def provide_entries():
        yield entries_data  # DLT consumes this
    
    # 4. Run pipeline (stages to parquet)
    info = pipeline.run(
        provide_entries(),
        loader_file_format="parquet"
    )
    
    # Result: ~/.dlt/pipelines/nightscout_entries_2024_10_15/
    #         └─ stage/nightscout/entries/
    #            └─ data.parquet (300 rows)
```

### DLT Schema Normalization

DLT normalizes messy API responses:

```python
# API Response (original)
[
  {
    "dateString": "2024-10-15T10:30:00.000Z",
    "_id": "abc123",
    "sgv": 145,
    "direction": "Flat",
    "trend": 0,
    "device": "iPhone",
    "type": "sgv"
  },
  ...
]

# After DLT (normalized schema)
Parquet file with columns:
├── dateString: string
├── _id: string
├── sgv: int64
├── direction: string
├── trend: int64
├── device: string
├── type: string
└── _cascade_ingested_at: timestamp  ← Added by Phlo
```

DLT automatically:
-  Infers column types
- 🚫 Handles nulls
- 📛 Renames fields (snake_case)
-  Validates structure

## Step 2: PyIceberg (Merge into Lakehouse)

PyIceberg is the Python client for Iceberg. It:
- Loads the staged parquet
- Creates/updates Iceberg table
- Performs idempotent merge (upsert)

### Creating the Iceberg Table

First, ensure the table exists:

```python
# From src/phlo/iceberg/tables.py

from pyiceberg.schema import Schema
from pyiceberg.types import NestedField, StringType, IntegerType, TimestampType

schema = Schema(
    NestedField(1, "_id", StringType(), required=True),
    NestedField(2, "sgv", IntegerType(), required=False),
    NestedField(3, "date_string", StringType(), required=False),
    NestedField(4, "direction", StringType(), required=False),
    NestedField(5, "timestamp_iso", StringType(), required=False),
    NestedField(6, "_cascade_ingested_at", TimestampType(), required=False),
)

catalog.create_table(
    identifier="raw.glucose_entries",
    schema=schema,
    partition_spec=None  # Iceberg will auto-partition by date
)
```

Result in MinIO:
```
s3://lake/warehouse/raw/glucose_entries/
├── metadata/
│   └── v1.metadata.json      ← Table created
└── data/ (empty)
```

### Merging Data (Idempotent Upsert)

Now merge staged parquet into Iceberg:

```python
# From src/phlo/defs/resources/iceberg.py

def merge_parquet(
    self,
    table_name: str,
    data_path: str,
    unique_key: str = "_id"
) -> dict:
    """
    Merge parquet file into Iceberg table (idempotent upsert).
    
    Args:
        table_name: "raw.glucose_entries"
        data_path: "/path/to/data.parquet"
        unique_key: Column to deduplicate on
        
    Returns:
        Metrics: rows_inserted, rows_deleted, etc.
    """
    
    # Load table
    table = self.catalog.load_table(table_name)
    
    # Read new data from parquet
    new_df = read_parquet(data_path)
    
    # SQL merge operation:
    # - If _id exists: delete old, insert new (deduplication)
    # - If _id new: insert it
    merge_query = f"""
    MERGE INTO {table_name} t
    USING (SELECT * FROM read_parquet('{data_path}')) n
    ON t.{unique_key} = n.{unique_key}
    WHEN MATCHED THEN DELETE
    WHEN NOT MATCHED THEN INSERT *
    """
    
    result = self.trino.execute(merge_query)
    
    return {
        'rows_inserted': result['inserted'],
        'rows_deleted': result['deleted'],
        'rows_total': len(table.scan().to_pandas())
    }
```

This ensures **idempotency**: running the same ingestion multiple times produces the same result.

### Real Example: Glucose Ingestion

Let's trace through a complete ingestion:

```bash
# Timeline: 2024-10-15, partition 10:00-11:00

# 1. Asset starts
dagster asset materialize --select entries \
  --partition "2024-10-15"

# 2. Fetch from Nightscout API (10:00-11:00 range)
Starting ingestion for partition 2024-10-15
Fetching data from Nightscout API...
Successfully fetched 288 entries from API

# 3. Validate with Pandera
Validating raw glucose data with Pandera schema...
Raw data validation passed for 288 entries

# 4. Stage to parquet
Staging data to parquet via DLT...
DLT staging completed in 1.23s

# 5. Create Iceberg table if needed
Ensuring Iceberg table raw.glucose_entries exists...

# 6. Merge with deduplication
Merging data to Iceberg table (idempotent upsert)...
Merged 288 rows to raw.glucose_entries
  (deleted 0 existing duplicates)

# Success!
Ingestion completed successfully in 2.45s
```

Now the data lives in Iceberg:

```
s3://lake/warehouse/raw/glucose_entries/
├── metadata/
│   ├── v1.metadata.json
│   └── snap-1234.avro         ← New snapshot for this ingestion
└── data/
    └── year=2024/month=10/day=15/
        ├── 00001.parquet (100 rows)
        ├── 00002.parquet (100 rows)
        └── 00003.parquet (88 rows)
```

## Pandera Data Quality Validation

Before storing in the lakehouse, Phlo validates with **Pandera**—a schema validation library.

```python
# From src/phlo/schemas/glucose.py

from pandera import Column, DataFrameSchema, Check, Index

RawGlucoseEntries = DataFrameSchema({
    "_id": Column(
        str,
        checks=Check.str_matches(r"^[a-f0-9]{24}$"),  # MongoDB ObjectId format
        required=True
    ),
    "sgv": Column(
        int,
        checks=[
            Check.greater_than_or_equal_to(20),   # Physiologically plausible minimum
            Check.less_than_or_equal_to(600),     # Physiologically plausible maximum
        ],
        required=False
    ),
    "date_string": Column(
        "datetime64[ns]",
        required=False
    ),
    "direction": Column(
        str,
        checks=Check.isin(["Flat", "Single Up", "Double Up", 
                           "Single Down", "Double Down", "None"]),
        required=False
    ),
    "trend": Column(
        int,
        checks=Check.isin([-2, -1, 0, 1, 2]),  # Valid trend codes
        required=False
    ),
})
```

Pandera checks:
- Data types (int, string, datetime)
- Value ranges (20-600 for glucose)
- Format patterns (ObjectId format for _id)
- Allowed values (direction must be specific strings)
- Nullability (which columns are required)

In the ingestion code:

```python
try:
    RawGlucoseEntries.validate(raw_df, lazy=True)
    context.log.info(f"Raw data validation passed for {len(raw_df)} entries")
except pandera.errors.SchemaErrors as err:
    failure_cases = err.failure_cases
    context.log.error(f"Raw data validation failed with {len(failure_cases)} errors")
    # Log errors but continue (logging gate)
    context.log.warning("Proceeding with ingestion despite validation errors")
```

**Note**: In this example, validation failures are logged but don't block ingestion (logging gate). In production, you might fail hard:

```python
# More strict: fail if validation errors
RawGlucoseEntries.validate(raw_df)  # Raises exception if invalid
```

## Handling Different Data Sources

Phlo can ingest from multiple sources. Let's look at GitHub as another example:

```python
# From src/phlo/defs/ingestion/github_assets.py

@dg.asset(
    name="dlt_github_user_events",
    partitions_def=daily_partition,
)
def github_user_events(context, iceberg: IcebergResource) -> MaterializeResult:
    """Ingest GitHub user activity via GitHub API + DLT."""
    
    # Configure GitHub API client
    github = Github(token=config.github_token)
    user = github.get_user()
    
    # Fetch events (different schema than glucose)
    events = [
        {
            "event_id": event.id,
            "event_type": event.type,
            "repo_name": event.repo.name,
            "created_at": event.created_at,
            "action": event.payload.get("action"),
        }
        for event in user.get_events()
    ]
    
    # Same pattern: DLT stage → PyIceberg merge
    local_staging_root = Path.home() / ".dlt" / "pipelines" / "github_events"
    local_staging_root.mkdir(parents=True, exist_ok=True)

    filesystem_destination = dlt.destinations.filesystem(
        bucket_url=local_staging_root.as_uri(),
    )

    pipeline = dlt.pipeline(
        pipeline_name=f"github_events_{partition_date}",
        destination=filesystem_destination,
        dataset_name="github"
    )
    
    @dlt.resource(name="user_events", write_disposition="replace")
    def provide_events():
        yield events
    
    pipeline.run(provide_events(), loader_file_format="parquet")
    
    # Merge to Iceberg
    merge_metrics = iceberg.merge_parquet(
        table_name="raw.github_user_events",
        data_path=str(parquet_path),
        unique_key="event_id",
    )
    
    return dg.MaterializeResult(
        metadata={
            "partition_date": dg.MetadataValue.text(partition_date),
            "rows_merged": dg.MetadataValue.int(merge_metrics["rows_inserted"]),
            "table_total_rows": dg.MetadataValue.int(merge_metrics["rows_total"]),
        }
    )
```

## Ingestion Patterns in Phlo

### Pattern 1: API Ingestion (Nightscout, GitHub)

```
API (network)
  ↓ (requests.get)
Python dict
  ↓ (DLT pipeline)
S3 parquet
  ↓ (PyIceberg merge)
Iceberg table
```

### Pattern 2: File Upload (CSV, Excel)

```
Local file
  ↓ (read_csv, openpyxl)
Pandas DataFrame
  ↓ (DLT pipeline)
S3 parquet
  ↓ (PyIceberg merge)
Iceberg table
```

### Pattern 3: Database Replication

```
Source Database (PostgreSQL, MySQL)
  ↓ (SELECT * from table)
Pandas DataFrame
  ↓ (DLT pipeline)
S3 parquet
  ↓ (PyIceberg merge)
Iceberg table
```

All follow the same pattern for safety and idempotency.

## Hands-On: Trace an Ingestion

```bash
# Run ingestion and watch the flow
docker exec dagster-webserver dagster asset materialize \
  --select dlt_glucose_entries \
  --partition "2024-10-15"

# Check staged parquet
docker exec minio mc ls myminio/lake/stage/entries/2024-10-15/

# Check Iceberg table
docker exec dagster-webserver python3 << 'EOF'
from phlo.iceberg.catalog import get_catalog
import pandas as pd

catalog = get_catalog()
table = catalog.load_table("raw.glucose_entries")

# Load all data
df = table.scan().to_pandas()
print(f"Total rows: {len(df)}")
print(f"\nLatest snapshot: {table.current_snapshot().snapshot_id}")
print(f"\nColumns:\n{df.columns.tolist()}")
print(f"\nFirst row:\n{df.head(1)}")
EOF
```

## Performance Considerations

### Batch Size

DLT chunks data into batches:

```python
# Small batches = more overhead
info = pipeline.run(
    provide_entries(),
    loader_file_format="parquet",
)  # Default: batches of ~10K rows

# For large datasets, you want good batch size
# 100K-1M rows per batch is typical
```

### Deduplication Key

Choose a column that's truly unique:

```python
# Good: Nightscout API's unique ID
unique_key="_id"  # MongoDB ObjectId, guaranteed unique

# Bad: Reading data multiple times
unique_key="date_string"  # Multiple readings per minute!
```

### Idempotency

Always design for idempotency:

```python
# Good: Can run any time, same result
merge_parquet(table, data, unique_key="_id")
merge_parquet(table, data, unique_key="_id")  # Second run does nothing
# Result: 288 rows

# Bad: Non-idempotent (duplicates!)
append_parquet(table, data)
append_parquet(table, data)  # Second run duplicates!
# Result: 576 rows (corrupted)
```

## Next: Transformations

Data is now in the lakehouse. Next: **Transform it with dbt and Trino**.

**Part 6: SQL Transformations with dbt**

See you there!

## Summary

**Phlo's Ingestion Pattern**:
1. Fetch data from source (API, file, database)
2. Validate with Pandera schemas
3. Stage to S3 parquet with DLT
4. Merge to Iceberg table with deduplication (idempotent)
5. New snapshot created in Iceberg
6. Ready for transformation

**Why This Pattern Works**:
- Idempotent (safe to retry)
- Atomic (all-or-nothing)
- Validated (Pandera checks)
- Auditable (snapshot history)
- Scalable (works for small to large datasets)

**Next**: [Part 6: SQL Transformations with dbt—The Right Way](06-dbt-transformations.md)

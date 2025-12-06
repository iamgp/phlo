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

### The @phlo.ingestion Decorator

Phlo provides the `@phlo.ingestion` decorator to simplify DLT ingestion. Here's the actual implementation from the glucose platform:

```python
# From examples/glucose-platform/workflows/ingestion/nightscout/readings.py

import phlo
from dlt.sources.rest_api import rest_api
from workflows.schemas.nightscout import RawGlucoseEntries

@phlo.ingestion(
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

    Fetches CGM glucose readings from the Nightscout API for a specific partition date,
    stages to parquet, and merges to Iceberg with idempotent deduplication.

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

### What @phlo.ingestion Does

The decorator handles all the complexity:

1. **DLT Pipeline Setup**: Automatically configures DLT staging and execution
2. **Schema Validation**: Validates data with Pandera schema before ingestion
3. **Iceberg Merge**: Performs idempotent upsert to Iceberg table using unique_key
4. **Scheduling**: Supports cron-based scheduling
5. **Freshness Checks**: Monitors data freshness (1-24 hours in this example)
6. **Asset Metadata**: Tracks lineage and dependencies in Dagster

### Merge Strategies

Phlo supports two merge strategies, allowing you to optimize for different data patterns:

#### Append Strategy (Insert-Only)

Best for immutable event streams where you never update existing records:

```python
@phlo.ingestion(
    table_name="api_events",
    unique_key="event_id",
    validation_schema=EventSchema,
    merge_strategy="append",  # Insert-only, no deduplication
    group="events",
)
def api_events(partition_date: str):
    return rest_api(...)
```

**Characteristics:**
- Fastest performance (no deduplication overhead)
- No checking for duplicates
- Simply appends all new records
- **Use for**: Server logs, clickstream events, time-series sensor data, immutable audit trails

**Trade-offs:**
- If you accidentally run the same partition twice, you'll get duplicates
- No way to update existing records
- Requires careful pipeline design to avoid re-runs

#### Merge Strategy (Upsert with Deduplication)

Best for dimension tables and data that may need updates:

```python
@phlo.ingestion(
    table_name="user_profiles",
    unique_key="user_id",
    validation_schema=UserSchema,
    merge_strategy="merge",      # Upsert mode
    dedup_strategy="last",       # Keep most recent
    group="users",
)
def user_profiles(partition_date: str):
    return rest_api(...)
```

**Deduplication Strategies:**

1. **`last` (default)**: Keep the most recent occurrence
   ```python
   dedup_strategy="last"
   ```
   - Based on insertion order during the pipeline run
   - Most common choice for dimension tables
   - Example: User profile updates (keep latest email, phone, etc.)

2. **`first`**: Keep the earliest occurrence
   ```python
   dedup_strategy="first"
   ```
   - Useful when first value is authoritative
   - Example: Initial signup timestamp, first purchase date

3. **`hash`**: Keep based on content hash
   ```python
   dedup_strategy="hash"
   ```
   - Compares full record content, not just timestamp
   - Useful when you want to detect actual data changes
   - Example: Configuration snapshots (only update if content differs)

**Characteristics:**
- Performs upsert: UPDATE if `unique_key` exists, INSERT if new
- Removes duplicates within the same batch
- Idempotent: running multiple times produces same result
- **Use for**: User profiles, product catalogs, reference data, slowly changing dimensions

**Trade-offs:**
- Slower than append (requires deduplication logic)
- More memory usage during merge
- Worth it for data correctness

#### Strategy Comparison

| Aspect | Append | Merge (last) | Merge (first) | Merge (hash) |
|--------|--------|--------------|---------------|--------------|
| **Performance** | Fastest | Medium | Medium | Slowest |
| **Deduplication** | None | By order | By order | By content |
| **Idempotency** | No | Yes | Yes | Yes |
| **Updates** | No | Yes (keeps latest) | No (keeps first) | Yes (if changed) |
| **Use Case** | Logs, events | Dimensions | Historical records | Config snapshots |

#### Real-World Example: Glucose Data

The glucose ingestion uses merge strategy because:

1. **API may return overlapping data**: Querying "last 24 hours" twice gives duplicates
2. **Data corrections**: Nightscout allows retroactive corrections to glucose readings
3. **Idempotency**: We want `materialize --partition 2024-10-15` to be safe to run multiple times

```python
@phlo.ingestion(
    table_name="glucose_entries",
    unique_key="_id",              # Nightscout's unique entry ID
    merge_strategy="merge",        # Upsert mode
    dedup_strategy="last",         # Keep most recent reading
    validation_schema=RawGlucoseEntries,
    ...
)
```

If we used `append` strategy instead:
- Running the same partition twice would create duplicates
- Corrected readings wouldn't update (you'd have both old and new)
- dbt transformations downstream would need to handle deduplication

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
    "device": "iPhone",
    "type": "sgv"
  },
  ...
]

# After DLT (normalized schema)
Parquet file with columns:
├── date_string: string (converted from dateString)
├── _id: string
├── sgv: int64
├── direction: string
├── device: string
├── type: string
```

DLT automatically:
-  Infers column types
- 🚫 Handles nulls
- 📛 Renames fields (snake_case)
-  Validates structure

### Pandera Schema Validation

The validation schema is defined in `examples/glucose-platform/workflows/schemas/nightscout.py`:

```python
# From workflows/schemas/nightscout.py

from pandera.pandas import DataFrameModel, Field

class RawGlucoseEntries(DataFrameModel):
    """
    Schema for raw Nightscout glucose entries from the API.

    Validates raw glucose data at ingestion time:
    - Valid glucose ranges (1-1000 mg/dL for raw data)
    - Proper field types and nullability
    - Required metadata fields
    - Unique entry IDs
    """

    _id: str = Field(
        nullable=False,
        unique=True,
        description="Nightscout entry ID (unique identifier)",
    )

    sgv: int = Field(
        ge=1,
        le=1000,
        nullable=False,
        description="Sensor glucose value in mg/dL (1-1000 for raw data)",
    )

    date: int = Field(
        nullable=False,
        description="Unix timestamp in milliseconds",
    )

    date_string: datetime = Field(
        nullable=False,
        description="ISO 8601 timestamp",
    )

    direction: str | None = Field(
        isin=["Flat", "FortyFiveUp", "FortyFiveDown", "SingleUp", "SingleDown", "DoubleUp", "DoubleDown", "NONE"],
        nullable=True,
        description="Trend direction (e.g., 'SingleUp', 'Flat')",
    )

    class Config:
        strict = False  # Allow DLT metadata fields
        coerce = True
```

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

### Real Example: Glucose Ingestion with @phlo.ingestion

Let's trace through what happens when you materialize a `@phlo.ingestion` asset:

```bash
# Timeline: 2024-10-15

# 1. Materialize the asset
dagster asset materialize --select glucose_entries \
  --partition "2024-10-15"

# 2. The @phlo.ingestion decorator executes your function
# Your function returns a DLT source configured for 2024-10-15

# 3. Decorator automatically stages data via DLT
Fetching data from Nightscout API...
Successfully fetched 288 entries from API
Staging data to parquet via DLT...
DLT staging completed in 1.23s

# 4. Decorator validates with Pandera schema (RawGlucoseEntries)
Validating raw glucose data with Pandera schema...
Raw data validation passed for 288 entries

# 5. Decorator creates Iceberg table if needed
Ensuring Iceberg table glucose_entries exists...

# 6. Decorator merges with deduplication (using unique_key="_id")
Merging data to Iceberg table (idempotent upsert)...
Merged 288 rows to glucose_entries
  (deleted 0 existing duplicates)

# 7. Decorator tracks metadata in Dagster
Asset materialized successfully
Metadata:
  - rows_ingested: 288
  - table_name: glucose_entries
  - partition_date: 2024-10-15

# Success!
Ingestion completed successfully in 2.45s
```

**You wrote**: ~10 lines of code (just the DLT source configuration)
**You got**: Full ingestion pipeline with validation, staging, merging, and monitoring

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

## Quality Checks with @phlo.quality

After ingestion and transformation, Phlo validates data with quality checks. The `@phlo.quality` decorator provides a declarative way to define quality checks:

```python
# From examples/glucose-platform/workflows/quality/nightscout.py

import phlo
from phlo.quality import FreshnessCheck, NullCheck, RangeCheck

@phlo.quality(
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
    """Declarative quality checks for glucose readings using @phlo.quality."""
    pass
```

The `@phlo.quality` decorator provides:

1. **NullCheck**: Ensures critical columns have no null values
2. **RangeCheck**: Validates numeric values are within expected ranges
3. **FreshnessCheck**: Ensures data is not stale (within 24 hours)
4. **Blocking**: If `blocking=True`, downstream assets wait for checks to pass

### Traditional Asset Checks (Alternative)

You can also use traditional Dagster asset checks for more control:

```python
# From workflows/quality/nightscout.py

from dagster import AssetCheckResult, AssetKey, asset_check
from workflows.schemas.nightscout import FactGlucoseReadings

@asset_check(
    name="nightscout_glucose_quality",
    asset=AssetKey(["fct_glucose_readings"]),
    blocking=True,
)
def nightscout_glucose_quality_check(context, trino: TrinoResource) -> AssetCheckResult:
    """Quality check using Pandera for type-safe schema validation."""

    # Query data from Iceberg via Trino
    query = "SELECT * FROM iceberg_dev.silver.fct_glucose_readings"
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
                "rows_validated": MetadataValue.int(len(fact_df)),
            }
        )
    except pandera.errors.SchemaErrors as err:
        return AssetCheckResult(
            passed=False,
            metadata={
                "failed_checks": MetadataValue.int(len(err.failure_cases)),
            }
        )
```

This approach gives you more control over the validation logic and error handling.

## Handling Different Data Sources

The `@phlo.ingestion` decorator works with any DLT source. You just return a DLT source/resource and the decorator handles the rest.

**Pattern**: Define your data source, return it, and let `@phlo.ingestion` handle staging, validation, and merging.

```python
# Example: Custom API ingestion

import phlo
from dlt.sources.rest_api import rest_api

@phlo.ingestion(
    table_name="github_events",
    unique_key="event_id",
    validation_schema=GitHubEventSchema,
    group="github",
)
def github_events(partition_date: str):
    """Ingest GitHub events using DLT."""

    # DLT rest_api source handles pagination and retries
    source = rest_api(
        client={
            "base_url": "https://api.github.com",
            "auth": {
                "token": os.getenv("GITHUB_TOKEN"),
            },
        },
        resources=[
            {
                "name": "events",
                "endpoint": {
                    "path": "/users/{username}/events",
                    "params": {
                        "per_page": 100,
                    },
                },
            }
        ],
    )

    return source
    # @phlo.ingestion automatically:
    # 1. Runs DLT pipeline to stage to parquet
    # 2. Validates with GitHubEventSchema
    # 3. Merges to Iceberg table with deduplication on event_id
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
# This uses the @phlo.ingestion decorated function
dagster asset materialize \
  --select glucose_entries \
  --partition "2024-10-15"

# Check Iceberg table via PyIceberg
python3 << 'EOF'
from phlo.iceberg.catalog import get_catalog
import pandas as pd

catalog = get_catalog()
table = catalog.load_table("glucose_entries")

# Load all data
df = table.scan().to_pandas()
print(f"Total rows: {len(df)}")
print(f"\nLatest snapshot: {table.current_snapshot().snapshot_id}")
print(f"\nColumns:\n{df.columns.tolist()}")
print(f"\nSample data:\n{df.head(3)}")
EOF

# Or query via Trino
docker exec trino trino \
  --catalog iceberg_dev \
  --schema raw \
  --execute "SELECT COUNT(*) as total FROM glucose_entries;"
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

**Phlo's Ingestion with @phlo.ingestion**:

The `@phlo.ingestion` decorator simplifies data ingestion by handling:
1. **DLT pipeline execution**: Stages data from source to parquet
2. **Schema validation**: Validates with Pandera before loading
3. **Iceberg merge**: Performs idempotent upsert using unique_key
4. **Monitoring**: Tracks metrics in Dagster (rows, freshness, etc.)
5. **Scheduling**: Supports cron-based execution

**Decorator Parameters**:
- `table_name`: Iceberg table to write to
- `unique_key`: Column for deduplication
- `validation_schema`: Pandera schema for validation
- `group`: Asset group for organization
- `cron`: Schedule (optional)
- `freshness_hours`: Expected data freshness (optional)

**Your Function**:
- Takes `partition_date: str` parameter
- Returns a DLT source or resource
- The decorator handles everything else

**Why This Pattern Works**:
- **Simple**: Write 10 lines, get full pipeline
- **Idempotent**: Safe to retry/rerun
- **Atomic**: All-or-nothing commits
- **Validated**: Pandera schema checks
- **Auditable**: Iceberg snapshot history
- **Scalable**: Works from KB to TB

**Quality Checks**:
- Use `@phlo.quality` for declarative checks (NullCheck, RangeCheck, FreshnessCheck)
- Or use traditional `@asset_check` for custom validation logic
- Both integrate with Dagster's asset check system

**Next**: [Part 6: SQL Transformations with dbt—The Right Way](06-dbt-transformations.md)

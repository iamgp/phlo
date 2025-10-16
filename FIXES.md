# DuckLake Pipeline Fixes

## Summary of Issues and Solutions

### Issue 1: dbt Models Created in Wrong Database/Schema

**Problem**: dbt creates models in `memory.raw_bronze.*` instead of `ducklake.bronze.*`

**Root Cause**:
- dbt profiles.yml sets `path: ":memory:"` as the default database
- Even though bootstrap macro attaches DuckLake, dbt doesn't automatically USE it for model creation
- The schema configuration prepends the profile schema name to model schemas

**Fix**: Update dbt profiles and project configuration

#### File: `transforms/dbt/profiles/profiles.yml`

BEFORE:
```yaml
cascade:
  target: ducklake
  outputs:
    ducklake:
      type: duckdb
      path: ":memory:"
      schema: "raw"  # This gets prepended to model schemas
```

AFTER:
```yaml
cascade:
  target: ducklake
  outputs:
    ducklake:
      type: duckdb
      path: ":memory:"
      schema: "main"  # Changed from "raw" - this becomes the default/staging schema
      # NOTE: path stays :memory: because we attach DuckLake in bootstrap
```

#### File: `transforms/dbt/macros/ducklake_setup.sql`

Add after line 104 (after `USE catalog_alias`):

```sql
  {# Set the default schema and database for dbt models #}
  {% do run_query("SET schema = '" ~ default_dataset ~ "'") %}
```

And modify the ATTACH statement (around line 100) to include CREATE_IF_NOT_EXISTS:

```sql
  {% if catalog_alias not in aliases %}
    {% set attach_sql = "ATTACH 'ducklake:" ~ ducklake_secret ~ "' AS " ~ catalog_alias ~ " (CREATE_IF_NOT_EXISTS true, DATA_PATH '" ~ data_path ~ "')" %}
    {% do run_query(attach_sql) %}
  {% endif %}
```

### Issue 2: Catalog Alias Mismatch

**Problem**: Python code defaults to "dbt" but .env and dbt use "ducklake"

**Fix**: Ensure consistent catalog alias

#### File: `src/cascade/config.py`

CHANGE line 39-42:
```python
    ducklake_catalog_alias: str = Field(
        default="ducklake",  # Changed from "dbt" to match .env
        description="Alias used when attaching the DuckLake catalog in DuckDB",
    )
```

### Issue 3: DLT Connection Pooling and Timeouts

**Problem**: Concurrent DLT pipelines can hang or timeout when writing to catalog

**Fix**: Add connection retry and timeout configuration

#### File: `src/cascade/dlt/ducklake_destination.py`

UPDATE the `build_destination` function (line 108-121):

```python
def build_destination(
    *args: Any,
    runtime_config: DuckLakeRuntimeConfig | None = None,
    **kwargs: Any,
) -> DuckLake:
    """
    Convenience helper returning a DuckLake destination for DLT pipelines.

    Each DLT pipeline gets its own ephemeral DuckDB connection that attaches
    to the shared DuckLake catalog (PostgreSQL + MinIO). No shared files = no locking.
    """
    # Use ephemeral connection with aggressive retry settings
    conn = duckdb.connect(database=":memory:")

    # Pre-configure connection with retry settings before DLT uses it
    if runtime_config is None:
        runtime_config = build_ducklake_runtime_config()

    # Increase retries for concurrent write scenarios
    runtime_config = dataclasses.replace(
        runtime_config,
        ducklake_retry_count=200,  # Increased from 100
        ducklake_retry_wait_ms=150,  # Increased from 100
        ducklake_retry_backoff=2.5,  # Increased from 2.0
    )

    kwargs["credentials"] = conn
    return DuckLake(*args, runtime_config=runtime_config, **kwargs)
```

Add import at top:
```python
import dataclasses
```

### Issue 4: DLT Asset Cleanup

**Problem**: DLT pipelines don't always clean up connections properly

**Fix**: Enhanced cleanup in dlt_assets.py

#### File: `src/cascade/defs/ingestion/dlt_assets.py`

UPDATE the context manager (lines 42-53):

```python
    finally:
        try:
            # More comprehensive cleanup
            if hasattr(pipeline, "_destination_client") and pipeline._destination_client:
                client = pipeline._destination_client

                # Close SQL client connection
                if hasattr(client, "sql_client") and client.sql_client:
                    if hasattr(client.sql_client, "_conn") and client.sql_client._conn:
                        try:
                            # Explicitly ROLLBACK any pending transaction
                            client.sql_client._conn.execute("ROLLBACK")
                        except Exception:
                            pass
                        try:
                            client.sql_client._conn.close()
                        except Exception:
                            pass

                # Close the destination client itself
                if hasattr(client, "close"):
                    try:
                        client.close()
                    except Exception:
                        pass
        except Exception as e:
            # Log but don't fail on cleanup errors
            pass
```

### Issue 5: Schema Creation and Management

**Problem**: Inconsistent schema naming between layers

**Fix**: Standardize schema names

#### File: `.env`

ENSURE these values:
```bash
DUCKLAKE_DEFAULT_DATASET=raw
DUCKLAKE_CATALOG_ALIAS=ducklake
```

#### File: `transforms/dbt/dbt_project.yml`

UPDATE schema configurations (lines 19-35):

```yaml
models:
  cascade:
    +materialized: table
    +database: ducklake  # Explicitly set database
    +pre-hook:
      - "{{ ducklake__bootstrap() }}"
    bronze:
      +schema: bronze  # Creates models in ducklake.bronze
      +materialized: view
      +tags: ["bronze"]
      +quoting:
        identifier: false
    silver:
      +schema: silver  # Creates models in ducklake.silver
      +tags: ["silver"]
    gold:
      +schema: gold  # Creates models in ducklake.gold
      +tags: ["gold"]
      +persist_docs: { relation: true, columns: true }
    marts_postgres:
      +schema: marts
      +tags: ["mart"]
      +materialized: table
```

### Issue 6: Source Configuration

**Problem**: Source references might not resolve correctly

#### File: `transforms/dbt/models/sources/sources.yml`

UPDATE to be explicit:

```yaml
version: 2

sources:
  - name: dagster_assets
    database: ducklake  # This should match DUCKLAKE_CATALOG_ALIAS
    schema: raw  # This should match DUCKLAKE_DEFAULT_DATASET
    description: Upstream Dagster assets that provide raw data from DuckLake raw layer
    tables:
      - name: entries
        description: Nightscout CGM data ingested via DLT into DuckLake raw.entries
        identifier: entries  # Explicit table name
        meta:
          dagster:
            asset_key: ["entries"]
```

## Implementation Order

1. Update `.env` and `config.py` for catalog alias consistency
2. Update dbt `profiles.yml` and `dbt_project.yml`
3. Update `ducklake_setup.sql` macro
4. Update DLT destination and cleanup code
5. Update source configuration
6. Run tests to verify

## Testing the Fixes

```bash
# 1. Update configuration files as described above

# 2. Restart services to pick up new configuration
docker compose down
docker compose up -d

# 3. Run integration tests
pytest tests/test_ducklake_integration.py -v

# 4. Test DLT ingestion
docker exec -it dagster-web dagster asset materialize -s entries --partition 2024-01-15

# 5. Test dbt transformation
docker exec -it dagster-web dbt build --project-dir /dbt --profiles-dir /dbt/profiles

# 6. Verify data location
docker exec -it dagster-web duckdb <<EOF
INSTALL ducklake; LOAD ducklake;
INSTALL postgres; LOAD postgres;
CREATE SECRET pg (TYPE postgres, HOST 'postgres', DATABASE 'ducklake_catalog', USER 'lake', PASSWORD 'lakepass');
ATTACH 'ducklake:pg' AS dl (DATA_PATH 's3://lake/ducklake');
USE dl;
SHOW TABLES;
SELECT count(*) FROM raw.entries;
SELECT count(*) FROM bronze.stg_entries;
EOF
```

## Expected Behavior After Fixes

1. DLT writes data to `ducklake.raw.entries`
2. dbt creates view at `ducklake.bronze.stg_entries` (not memory.raw_bronze)
3. dbt creates tables in `ducklake.silver.*` and `ducklake.gold.*`
4. No more hanging on concurrent DLT operations
5. Data flows correctly through all layers
6. All queries reference the shared DuckLake catalog

## Additional Recommendations

### 1. Add Connection Pooling Monitoring

Create a diagnostic script:

```python
# scripts/check_ducklake_health.py
import duckdb
from cascade.ducklake import build_ducklake_runtime_config, configure_ducklake_connection

def check_catalog_health():
    conn = duckdb.connect(":memory:")
    runtime = build_ducklake_runtime_config()
    configure_ducklake_connection(conn, runtime, read_only=True)

    # Check schemas
    schemas = conn.execute(
        f"SELECT schema_name FROM {runtime.catalog_alias}.information_schema.schemata"
    ).fetchall()
    print(f"Schemas: {[s[0] for s in schemas]}")

    # Check tables in each layer
    for schema in ["raw", "bronze", "silver", "gold"]:
        try:
            tables = conn.execute(
                f"SELECT table_name FROM {runtime.catalog_alias}.information_schema.tables "
                f"WHERE table_schema = '{schema}'"
            ).fetchall()
            print(f"{schema}: {[t[0] for t in tables]}")
        except:
            print(f"{schema}: ERROR")

    conn.close()

if __name__ == "__main__":
    check_catalog_health()
```

### 2. Add Retry Logic to Dagster Assets

For DLT assets, increase retry policy:

```python
@dg.asset(
    retry_policy=dg.RetryPolicy(max_retries=5, delay=60),  # Increased
    op_tags={"dagster/max_runtime": 600},  # Increased timeout
    ...
)
```

### 3. Monitor Postgres Catalog Load

Add monitoring for the Postgres catalog:

```sql
-- Check for long-running locks
SELECT
    pid,
    query,
    state,
    wait_event_type,
    wait_event,
    now() - query_start as duration
FROM pg_stat_activity
WHERE datname = 'ducklake_catalog'
    AND state != 'idle'
ORDER BY duration DESC;
```

### 4. Consider Partitioning Strategy

For the entries table with daily partitions, ensure DuckLake partitioning:

```sql
-- After creating entries table, partition it
ALTER TABLE ducklake.raw.entries
SET PARTITIONED BY (date_trunc('day', epoch_ms(date)));
```

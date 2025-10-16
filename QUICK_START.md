# Quick Start - Post-Fix Verification

## Immediate Actions

### 1. Restart Services
```bash
docker compose down
docker compose up -d postgres minio dagster-webserver dagster-daemon
```

### 2. Wait for Services to be Healthy
```bash
# Wait 30 seconds for services to start
sleep 30

# Check health
docker ps --filter "name=pg|minio|dagster" --format "table {{.Names}}\t{{.Status}}"
```

### 3. Run Health Check
```bash
python scripts/check_ducklake_health.py
```

Expected output: All ✓ marks, no ✗ marks

## Testing the Fixes

### Test 1: Single DLT Partition (Basic Test)
```bash
# Materialize a single partition
docker exec -it dagster-web dagster asset materialize --select entries --partition 2024-01-15

# Check logs - should complete in < 60s without hanging
# Expected: "Loaded X rows for partition 2024-01-15"
```

### Test 2: Concurrent DLT Partitions (Stress Test)
```bash
# Try 3 concurrent partitions - this should NOT hang anymore
docker exec -it dagster-web sh -c "
dagster asset materialize --select entries --partition 2024-01-13 &
dagster asset materialize --select entries --partition 2024-01-14 &
dagster asset materialize --select entries --partition 2024-01-15 &
wait
"

# All three should complete successfully
```

### Test 3: dbt Model Creation (Schema Location Test)
```bash
# Run dbt to create bronze layer
docker exec -it dagster-web dbt run \
  --project-dir /dbt \
  --profiles-dir /dbt/profiles \
  --select stg_entries \
  --target ducklake

# Check the logs for THIS EXACT LINE:
# Should see: "OK created sql view model ducklake.bronze.stg_entries"
# NOT: "OK created sql view model memory.raw_bronze.stg_entries"
```

### Test 4: Verify Data Location
```bash
# Query DuckLake directly to confirm data location
docker exec -it dagster-web python3 <<'PYTHON'
import duckdb
from cascade.ducklake import build_ducklake_runtime_config, configure_ducklake_connection

conn = duckdb.connect(":memory:")
runtime = build_ducklake_runtime_config()
configure_ducklake_connection(conn, runtime, read_only=True)

# Check what schemas exist
print("\nSchemas in catalog:")
schemas = conn.execute(f"SELECT schema_name FROM {runtime.catalog_alias}.information_schema.schemata").fetchall()
for (s,) in schemas:
    print(f"  - {s}")

# Check tables in each layer
for schema in ['raw', 'bronze', 'silver', 'gold']:
    try:
        tables = conn.execute(f"SELECT table_name FROM {runtime.catalog_alias}.information_schema.tables WHERE table_schema = '{schema}'").fetchall()
        print(f"\n{schema} tables:")
        for (t,) in tables:
            print(f"  - {t}")
    except:
        print(f"\n{schema}: No tables yet")

# Check row counts
try:
    raw_count = conn.execute(f"SELECT count(*) FROM {runtime.catalog_alias}.raw.entries").fetchone()[0]
    print(f"\nRaw entries: {raw_count:,} rows")
except Exception as e:
    print(f"\nRaw entries: ERROR - {e}")

try:
    bronze_count = conn.execute(f"SELECT count(*) FROM {runtime.catalog_alias}.bronze.stg_entries").fetchone()[0]
    print(f"Bronze entries: {bronze_count:,} rows")
except Exception as e:
    print(f"Bronze entries: ERROR - {e}")

conn.close()
PYTHON
```

## Success Indicators

After running all tests above, you should see:

1. Health check: All ✓ marks
2. Single partition: Completes in < 60 seconds
3. Concurrent partitions: All complete without timeouts
4. dbt logs show: `ducklake.bronze.stg_entries` (not `memory.raw_bronze`)
5. Data verification: Row counts > 0 in both raw and bronze

## If Tests Fail

### DLT Still Hangs
```bash
# Check Postgres for locks
docker exec -it pg psql -U lake -d ducklake_catalog -c "
SELECT
    pid,
    state,
    wait_event_type,
    wait_event,
    now() - query_start as duration,
    substring(query, 1, 50) as query_start
FROM pg_stat_activity
WHERE datname = 'ducklake_catalog'
    AND state != 'idle'
ORDER BY duration DESC;
"

# If you see long-running queries, kill them:
# docker exec -it pg psql -U lake -d ducklake_catalog -c "SELECT pg_terminate_backend(<pid>);"
```

### dbt Models in Wrong Place
```bash
# Check dbt is using correct target
docker exec -it dagster-web dbt debug --project-dir /dbt --profiles-dir /dbt/profiles

# Should show:
# - Connection test: OK
# - Database: :memory: (this is normal)
# - Schema: main (NOT raw)
```

### No Data in Tables
```bash
# Check MinIO bucket exists
docker exec -it minio mc ls local/lake/

# Check Postgres catalog initialized
docker exec -it pg psql -U lake -d ducklake_catalog -c "\dt ducklake_*" | head -20

# If catalog empty, DuckLake hasn't been initialized
# Run a simple write to initialize:
docker exec -it dagster-web python3 <<'PYTHON'
import duckdb
from cascade.ducklake import build_ducklake_runtime_config, configure_ducklake_connection

conn = duckdb.connect(":memory:")
runtime = build_ducklake_runtime_config()
configure_ducklake_connection(conn, runtime, read_only=False)

# Create a test table to initialize catalog
conn.execute(f"CREATE TABLE IF NOT EXISTS {runtime.catalog_alias}.raw.test (id INTEGER)")
conn.execute(f"INSERT INTO {runtime.catalog_alias}.raw.test VALUES (1)")
print("Catalog initialized")
conn.close()
PYTHON
```

## Detailed Logs

If you need more diagnostics:

```bash
# Dagster logs
docker logs dagster-daemon --tail=100

# dbt logs
docker exec -it dagster-web tail -50 /dbt/logs/dbt.log

# Postgres logs
docker logs pg --tail=50
```

## Integration Test Run

For comprehensive verification:

```bash
# Install pytest in container (if not already)
docker exec -it dagster-web pip install pytest pytest-xdist

# Run integration tests
docker exec -it dagster-web pytest \
  /opt/dagster/cascade/../tests/test_ducklake_integration.py \
  -v -s --tb=short

# Expected: Most tests pass (some may fail if data not populated yet)
```

## Quick Reference: Fixed Files

Configuration changes:
- `src/cascade/config.py:40` - catalog_alias default
- `transforms/dbt/profiles/profiles.yml:7` - schema changed to "main"
- `transforms/dbt/dbt_project.yml:17` - added +database: ducklake
- `transforms/dbt/macros/ducklake_setup.sql:100,105` - ATTACH params + SET schema

Code changes:
- `src/cascade/dlt/ducklake_destination.py:3,125-130` - retry settings
- `src/cascade/defs/ingestion/dlt_assets.py:42-67` - cleanup enhancement

## Next Steps After Verification

Once all tests pass:

1. Delete old dbt target artifacts:
   ```bash
   rm -rf transforms/dbt/target/all_dbt_assets-*
   ```

2. Run full pipeline:
   ```bash
   docker exec -it dagster-web dagster asset materialize --select "*"
   ```

3. Set up monitoring (see DIAGNOSIS_SUMMARY.md)

4. Consider partitioning optimization for production

---

**Need help?** Check `DIAGNOSIS_SUMMARY.md` for detailed troubleshooting or `FIXES.md` for technical details.

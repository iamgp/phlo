# DuckLake Pipeline Diagnosis Summary

## Executive Summary

After thorough investigation of your DuckLake pipeline, I identified **6 critical configuration issues** causing DLT hangs and dbt data placement problems. All issues have been diagnosed, fixes implemented, and comprehensive tests created.

## Critical Issues Found

### 1. dbt Creating Models in Wrong Database (CRITICAL)
- **Symptom**: dbt creates views in `memory.raw_bronze.*` instead of `ducklake.bronze.*`
- **Impact**: Data transformations not visible to other processes, breaking the pipeline
- **Root Cause**: dbt profiles.yml using `:memory:` path without proper schema configuration
- **Fix Applied**: Updated profiles.yml schema from "raw" to "main", added `+database: ducklake` to dbt_project.yml

### 2. Catalog Alias Mismatch (HIGH)
- **Symptom**: Python code defaults to "dbt", .env uses "ducklake"
- **Impact**: Connection failures and catalog lookup errors
- **Root Cause**: Inconsistent default values across codebase
- **Fix Applied**: Updated config.py default from "dbt" to "ducklake"

### 3. DLT Concurrent Write Contention (HIGH)
- **Symptom**: DLT pipelines hang or timeout during concurrent execution
- **Impact**: Pipeline failures, especially with daily partitions
- **Root Cause**: Insufficient retry settings for Postgres catalog lock contention
- **Fix Applied**: Increased retry count to 200, wait time to 150ms, backoff to 2.5x

### 4. Incomplete Connection Cleanup (MEDIUM)
- **Symptom**: Connections left open after DLT failures
- **Impact**: Resource leaks and potential deadlocks
- **Root Cause**: Cleanup only closed connection, not full client
- **Fix Applied**: Enhanced cleanup to rollback transactions and close full client stack

### 5. dbt Bootstrap Not Setting Default Schema (MEDIUM)
- **Symptom**: Models created in wrong schema despite catalog attachment
- **Impact**: Schema proliferation, data not findable
- **Root Cause**: Bootstrap macro attached catalog but didn't SET schema
- **Fix Applied**: Added `SET schema` command after catalog attachment

### 6. Missing ATTACH Parameters (LOW)
- **Symptom**: Catalog not created if missing
- **Impact**: First-run failures
- **Root Cause**: ATTACH command missing CREATE_IF_NOT_EXISTS flag
- **Fix Applied**: Added CREATE_IF_NOT_EXISTS and explicit DATA_PATH to ATTACH

## Files Modified

### Configuration Files
- `src/cascade/config.py` - Fixed default catalog alias
- `transforms/dbt/profiles/profiles.yml` - Changed schema from "raw" to "main"
- `transforms/dbt/dbt_project.yml` - Added `+database: ducklake`
- `transforms/dbt/macros/ducklake_setup.sql` - Enhanced ATTACH and added SET schema

### Application Code
- `src/cascade/dlt/ducklake_destination.py` - Increased retry settings, added dataclasses import
- `src/cascade/defs/ingestion/dlt_assets.py` - Enhanced connection cleanup

## Testing & Validation

### Created Test Suite
`tests/test_ducklake_integration.py` - Comprehensive integration tests covering:
1. DuckLake connection configuration
2. Extension installation
3. Catalog attachment
4. Schema creation
5. DLT destination functionality
6. End-to-end data flow (DLT → dbt → query)
7. Concurrent write operations

### Created Diagnostic Script
`scripts/check_ducklake_health.py` - Health monitoring script that checks:
1. Connection configuration
2. Extension loading
3. Catalog attachment
4. Schema existence
5. Table inventory by layer
6. Row counts across layers
7. Postgres catalog health
8. Active locks and queries

## Next Steps

### 1. Restart Services (REQUIRED)
```bash
cd /Users/garethprice/Developer/cascade
docker compose down
docker compose up -d
```

### 2. Run Health Check
```bash
# From host
python scripts/check_ducklake_health.py

# Or from container
docker exec -it dagster-web python /opt/dagster/cascade/../scripts/check_ducklake_health.py
```

### 3. Test DLT Ingestion
```bash
# Test single partition
docker exec -it dagster-web dagster asset materialize --select entries --partition 2024-01-15

# Test concurrent partitions (verify no hanging)
docker exec -it dagster-web dagster asset materialize --select entries \
  --partition 2024-01-13 \
  --partition 2024-01-14 \
  --partition 2024-01-15
```

### 4. Test dbt Transformation
```bash
# Run dbt build
docker exec -it dagster-web dbt build \
  --project-dir /dbt \
  --profiles-dir /dbt/profiles \
  --target ducklake

# Verify data location
docker exec -it dagster-web dbt run \
  --project-dir /dbt \
  --profiles-dir /dbt/profiles \
  --select stg_entries
```

### 5. Verify Data Flow
```bash
# Check data landed in correct location
docker exec -it dagster-web python <<EOF
import duckdb
from cascade.ducklake import build_ducklake_runtime_config, configure_ducklake_connection

conn = duckdb.connect(":memory:")
runtime = build_ducklake_runtime_config()
configure_ducklake_connection(conn, runtime, read_only=True)

print("Raw entries:", conn.execute(f"SELECT count(*) FROM {runtime.catalog_alias}.raw.entries").fetchone()[0])
print("Bronze entries:", conn.execute(f"SELECT count(*) FROM {runtime.catalog_alias}.bronze.stg_entries").fetchone()[0])
conn.close()
EOF
```

### 6. Run Integration Tests
```bash
# Install test dependencies if needed
pip install pytest pytest-xdist

# Run tests
pytest tests/test_ducklake_integration.py -v -s

# Or from container
docker exec -it dagster-web pytest /opt/dagster/cascade/../tests/test_ducklake_integration.py -v
```

## Expected Behavior After Fixes

### DLT Ingestion
- Creates ephemeral `:memory:` DuckDB connection
- Attaches to DuckLake catalog `ducklake` (Postgres + MinIO)
- Writes data to `ducklake.raw.entries`
- Multiple concurrent writes succeed without hanging
- Clean connection cleanup after completion

### dbt Transformation
- Bootstrap macro attaches catalog as `ducklake`
- Sets default schema to `raw`
- Creates models in `ducklake.bronze.*`, `ducklake.silver.*`, `ducklake.gold.*`
- Sources correctly reference `ducklake.raw.entries`
- All queries use DuckLake catalog, not ephemeral memory

### Dagster Orchestration
- Daily partitions materialize independently
- Concurrent partition backfills complete successfully
- No hanging on DLT operations
- Clean asset lineage through all layers

## Monitoring Recommendations

### 1. Add Postgres Catalog Monitoring
```sql
-- Monitor lock contention (run on Postgres)
SELECT
    relation::regclass,
    mode,
    granted,
    pid,
    now() - query_start as duration
FROM pg_locks
JOIN pg_stat_activity USING (pid)
WHERE datname = 'ducklake_catalog'
ORDER BY duration DESC;
```

### 2. Track DLT Pipeline Metrics
Add to Dagster asset metadata:
- Rows inserted
- Execution time
- Retry attempts
- Concurrent writes

### 3. Monitor dbt Model Locations
Periodically verify models in correct schemas:
```sql
SELECT
    table_schema,
    table_name,
    table_type
FROM ducklake.information_schema.tables
WHERE table_schema IN ('raw', 'bronze', 'silver', 'gold')
ORDER BY table_schema, table_name;
```

## Common Troubleshooting

### Issue: DLT Still Hangs
1. Check Postgres locks: See monitoring SQL above
2. Verify retry settings in logs
3. Increase `ducklake_retry_count` further if needed
4. Consider adding exponential jitter to retry backoff

### Issue: dbt Models Still in Wrong Place
1. Run: `dbt debug` to verify connection
2. Check dbt logs for actual SQL being executed
3. Verify `USE ducklake` appears in logs
4. Manually test: `dbt run --select stg_entries --debug`

### Issue: "Table Not Found" Errors
1. Run health check script
2. Verify catalog alias in all configs matches
3. Check sources.yml database field
4. Manually query: `PRAGMA database_list;` in DuckDB

### Issue: Data Not Flowing Between Layers
1. Check each layer independently:
   - Raw: `SELECT count(*) FROM ducklake.raw.entries`
   - Bronze: `SELECT count(*) FROM ducklake.bronze.stg_entries`
   - Silver: `SELECT count(*) FROM ducklake.silver.fct_glucose_readings`
2. Verify view/table types are correct
3. Check dbt run results for errors
4. Test dbt models individually

## Performance Tuning

### For Heavy Concurrent Workloads
1. Increase Postgres `max_connections`
2. Add connection pooling (PgBouncer)
3. Partition large tables in DuckLake
4. Use dbt incremental materializations

### For Large Data Volumes
1. Enable DuckLake data inlining for small inserts
2. Configure target file sizes for compaction
3. Use Parquet compression (zstd recommended)
4. Partition by date for time-series data

## Documentation References

- DuckLake: `/Users/garethprice/Developer/cascade/docs/ducklake.select`
- Spec: `/Users/garethprice/Developer/cascade/spec.md`
- Fixes: `/Users/garethprice/Developer/cascade/FIXES.md`
- Tests: `/Users/garethprice/Developer/cascade/tests/test_ducklake_integration.py`
- Health Check: `/Users/garethprice/Developer/cascade/scripts/check_ducklake_health.py`

## Success Criteria

Pipeline is working correctly when:
1. Health check script shows all ✓
2. DLT can materialize 3+ concurrent partitions without hanging
3. dbt models created in `ducklake.bronze.*` (not `memory.*`)
4. Data queryable through all layers (raw → bronze → silver → gold)
5. No long-running locks in Postgres catalog
6. Integration tests pass

---

**Next Action**: Run the health check, then restart services and test a single partition materialization.

# Common Errors and Solutions

Quick reference for resolving common Cascade errors.

## Top 10 Errors

### 1. Asset Not Found in Dagster UI

**Error Message**:
```
DagsterInvalidDefinitionError: Asset 'my_asset' not found
```

**Cause**: Domain not registered for auto-discovery

**Solution**:
```python
# Add import to src/cascade/defs/ingestion/__init__.py
from cascade.defs.ingestion import my_domain  # noqa: F401
```

**Then restart Dagster**:
```bash
docker restart dagster-webserver
```

**Details**: [TROUBLESHOOTING_GUIDE.md#asset-not-found](./TROUBLESHOOTING_GUIDE.md#asset-not-found)

---

### 2. unique_key Field Not in Schema

**Error Message**:
```
KeyError: 'observation_id'
```

**Cause**: `unique_key` in decorator doesn't match schema field name

**Solution**:
```python
# Check your decorator
@cascade_ingestion(
    unique_key="id",  # Must match a field in validation_schema
    validation_schema=MySchema,
    ...
)

# Check your schema has this field
class MySchema(pa.DataFrameModel):
    id: Series[str]  # Field must exist
    ...
```

**Details**: [Error Message Audit](./audit/error_message_audit.md#scenario-2)

---

### 3. Invalid Cron Expression

**Error Message**:
```
ValueError: Invalid cron expression: 'every hour'
```

**Cause**: Cron string is not in standard format

**Solution**:
```python
# Use standard cron format: minute hour day month weekday
@cascade_ingestion(
    cron="0 */1 * * *",  # Every hour at minute 0
    # NOT: cron="every hour"
    ...
)
```

**Common cron patterns**:
- `"0 */1 * * *"` - Every hour
- `"*/15 * * * *"` - Every 15 minutes
- `"0 0 * * *"` - Daily at midnight
- `"0 9 * * MON"` - Every Monday at 9am

**Test your cron**: https://crontab.guru/

**Details**: [Error Message Audit](./audit/error_message_audit.md#scenario-3)

---

### 4. Schema Validation Failed

**Error Message**:
```
pandera.errors.SchemaError: Column 'temperature' failed validation
failure cases:
   index  failure_case
0     42         -150.5
```

**Cause**: Data violates Pandera schema constraints

**Solution**:
```python
# Check constraint in schema
class MySchema(pa.DataFrameModel):
    temperature: Series[float] = pa.Field(
        ge=-100,  # -150.5 violates this constraint
        le=100,
    )
```

**Fix options**:
1. Clean data before validation
2. Adjust schema constraint if value is valid
3. Add data filtering in asset function

**Details**: [Error Message Audit](./audit/error_message_audit.md#scenario-4)

---

### 5. Missing Required Schema Parameter

**Error Message**:
```
ValueError: Either 'validation_schema' or 'iceberg_schema' must be provided
```

**Cause**: Decorator missing schema parameter

**Solution**:
```python
# Add validation_schema (recommended)
@cascade_ingestion(
    table_name="my_table",
    unique_key="id",
    validation_schema=MySchema,  # Add this
    group="my_group",
)
```

**Best practice**: Always use `validation_schema` - Iceberg schema is auto-generated.

**Details**: [Error Message Audit](./audit/error_message_audit.md#scenario-5)

---

### 6. DLT Pipeline Failed

**Error Message**:
```
dlt.pipeline.exceptions.PipelineStepFailed: Pipeline step 'extract' failed
Caused by: requests.exceptions.ConnectionError: Connection refused
```

**Cause**: Usually API connection issue, credentials, or network problem

**Common causes**:
1. API endpoint is down
2. Invalid API credentials
3. Network connectivity issue
4. Rate limit exceeded

**Solution**:
```bash
# 1. Check API status page
# 2. Verify credentials in .env
# 3. Test connection manually
curl https://api.example.com/endpoint

# 4. Check Dagster logs
docker logs dagster-webserver

# 5. Retry materialization
docker exec dagster-webserver dagster asset materialize \
  --select my_asset --partition 2024-01-15
```

**Details**: [Error Message Audit](./audit/error_message_audit.md#scenario-6)

---

### 7. Iceberg Table Doesn't Exist

**Error Message**:
```
pyiceberg.exceptions.NoSuchTableError: Table does not exist: raw.my_table
```

**Cause**: Asset not yet materialized

**Solution**:
```bash
# Materialize the asset first
docker exec dagster-webserver dagster asset materialize \
  --select my_asset --partition 2024-01-15

# Or via Dagster UI
# http://localhost:3000 → Assets → my_asset → Materialize
```

**Note**: Tables are created on first materialization, not when asset is defined.

**Details**: [Error Message Audit](./audit/error_message_audit.md#scenario-7)

---

### 8. Docker Service Not Running

**Error Message**:
```
requests.exceptions.ConnectionError: ('Connection aborted.', ConnectionRefusedError(111, 'Connection refused'))
```

**Cause**: Nessie, MinIO, Trino, or Dagster not running

**Solution**:
```bash
# Check service status
docker compose ps

# Start services
make up-core up-query

# Check logs
docker logs nessie
docker logs minio
docker logs trino
docker logs dagster-webserver

# Verify connection
curl http://localhost:19120/api/v2/config  # Nessie
curl http://localhost:9001  # MinIO console
```

**Details**: [Error Message Audit](./audit/error_message_audit.md#scenario-8)

---

### 9. Import Error in Python Code

**Error Message**:
```
ModuleNotFoundError: No module named 'cascade'
```

**Cause**: Cascade not installed or PYTHONPATH not set

**Solution**:
```bash
# Inside Docker container (preferred)
docker exec -it dagster-webserver bash
pip install -e /app

# Or set PYTHONPATH
export PYTHONPATH=/home/user/cascade/src:$PYTHONPATH
```

---

### 10. Asset Shows in UI But Won't Materialize

**Error Message**: No clear error, just "Failed" status

**Cause**: Various - check logs for details

**Solution**:
```bash
# 1. Check Dagster logs
docker logs dagster-webserver | tail -100

# 2. Check asset run logs in UI
# Click on failed run → View logs

# 3. Common issues:
# - API credentials missing/invalid
# - Schema validation failures
# - Network timeouts
# - Iceberg catalog connection issues

# 4. Restart services if needed
docker restart dagster-webserver
docker restart nessie
```

---

## Error Categories

### Configuration Errors

| Error | Cause | Quick Fix |
|-------|-------|-----------|
| Asset not found | Missing domain import | Add import to `__init__.py` |
| unique_key not in schema | Field name mismatch | Match field names exactly |
| Invalid cron | Wrong format | Use standard cron format |
| Missing schema | No validation_schema | Add Pandera schema |

### Runtime Errors

| Error | Cause | Quick Fix |
|-------|-------|-----------|
| Schema validation failed | Data violates constraints | Check Pandera schema constraints |
| DLT pipeline failed | API/network issue | Check credentials, connection |
| Table doesn't exist | Asset not materialized | Materialize asset first |
| Connection refused | Service not running | Start Docker services |

### Development Errors

| Error | Cause | Quick Fix |
|-------|-------|-----------|
| ModuleNotFoundError | Import issues | Install cascade in editable mode |
| Permission denied | File permissions | Check Docker volume mounts |
| Port already in use | Port conflict | Stop conflicting service or change port |

---

## Debugging Workflow

When you encounter an error:

1. **Read the error message carefully**
   - Look for field names, file paths, line numbers

2. **Check this guide**
   - Search for similar error message
   - Try suggested solution

3. **Check logs**
   ```bash
   # Dagster logs
   docker logs dagster-webserver | tail -100

   # All service logs
   make logs
   ```

4. **Verify configuration**
   - Schema field names match unique_key
   - Domain is registered in `__init__.py`
   - Cron expression is valid
   - Docker services are running

5. **Try minimal reproduction**
   - Test with simple data
   - Test schema validation separately
   - Test API connection manually

6. **Search documentation**
   - [TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md)
   - [WORKFLOW_DEVELOPMENT_GUIDE.md](./WORKFLOW_DEVELOPMENT_GUIDE.md)

7. **Ask for help**
   - [GitHub Discussions](https://github.com/iamgp/cascade/discussions)
   - [GitHub Issues](https://github.com/iamgp/cascade/issues)

---

## Prevention Best Practices

### 1. Validate Schema Early

```python
# Test schema validation before full pipeline
import pandas as pd

test_data = pd.DataFrame([{...}])
MySchema.validate(test_data)  # Fails fast if schema is wrong
```

### 2. Match Field Names Exactly

```python
# unique_key must match schema field exactly
@cascade_ingestion(
    unique_key="id",  # Must match field name below
    validation_schema=MySchema,
)

class MySchema(pa.DataFrameModel):
    id: Series[str]  # Exact match
```

### 3. Test Cron Expressions

Use https://crontab.guru/ to validate cron expressions before using them.

### 4. Use Environment Variables for Credentials

```bash
# .env file
API_KEY=your_key_here

# In code
import os
api_key = os.getenv("API_KEY")
```

### 5. Check Docker Services Before Materializing

```bash
# Quick health check
docker compose ps

# All services should show "Up" or "healthy"
```

### 6. Use Descriptive Asset Names

```python
# Good
def weather_observations(partition_date: str):
    pass

# Bad
def data(partition_date: str):  # Too generic
    pass
```

### 7. Add Logging

```python
def my_asset(partition_date: str):
    print(f"Processing partition: {partition_date}")
    # ... your code ...
    print(f"Fetched {len(data)} rows")
    return source
```

---

## Getting More Help

### Documentation

- **Full Troubleshooting**: [TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md)
- **Workflow Development**: [WORKFLOW_DEVELOPMENT_GUIDE.md](./WORKFLOW_DEVELOPMENT_GUIDE.md)
- **Testing**: [TESTING_GUIDE.md](./TESTING_GUIDE.md)
- **Architecture**: [architecture.md](./architecture.md)

### Community

- **GitHub Discussions**: https://github.com/iamgp/cascade/discussions
- **GitHub Issues**: https://github.com/iamgp/cascade/issues

### Tips for Asking Questions

1. **Include error message**: Full stack trace
2. **Include context**: What were you trying to do?
3. **Include code**: Schema, decorator config, asset function
4. **Include environment**: Docker logs, service status
5. **Include what you tried**: Debugging steps taken

---

**Found a solution not listed here?** Contribute to this guide via pull request!

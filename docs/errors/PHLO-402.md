# PHLO-402: Iceberg Write Error

**Error Type:** Iceberg Write Error
**Severity:** High
**Exception Class:** `PhloError`

## Description

This error occurs when data cannot be written to an Iceberg table. Write operations include appending new data, overwriting partitions, and upserts. Failures can stem from schema mismatches between the data and table, invalid partition specifications, S3 storage issues, or insufficient permissions.

## Common Causes

1. **Schema mismatch**
   - DataFrame columns don't match table schema
   - Column types differ (e.g., writing string to int column)
   - Missing required columns

2. **Partition spec invalid**
   - Partition column doesn't exist in data
   - Partition values contain invalid characters
   - Partition field type mismatch

3. **S3 write failed**
   - MinIO/S3 storage full
   - S3 endpoint unreachable
   - Write timeout on large files

4. **Insufficient permissions**
   - S3 bucket policy denies write access
   - MinIO credentials invalid
   - Read-only access configured

## Solutions

### Solution 1: Align data schema with table schema

```python
from pyiceberg.catalog import load_catalog
import pandas as pd

catalog = load_catalog("default")
table = catalog.load_table("bronze.dlt_weather_observations")

# Check expected schema
print("Table schema:")
for field in table.schema().fields:
    print(f"  {field.name}: {field.field_type}")

# Ensure DataFrame matches
df = pd.DataFrame([{
    "observation_id": "obs-001",
    "station_id": "KSFO",
    "temperature": 18.5,
    "timestamp": "2024-01-15T12:00:00",
}])

# ✅ Verify columns match
table_columns = {f.name for f in table.schema().fields}
df_columns = set(df.columns)
missing = table_columns - df_columns
extra = df_columns - table_columns

if missing:
    print(f"❌ Missing columns: {missing}")
if extra:
    print(f"⚠️ Extra columns (will be ignored): {extra}")
```

### Solution 2: Fix column types

```python
import pandas as pd

# ❌ Wrong types
df = pd.DataFrame([{
    "temperature": "18.5",     # String, should be float
    "station_id": 12345,       # Int, should be string
}])

# ✅ Correct types
df = pd.DataFrame([{
    "temperature": 18.5,       # Float
    "station_id": "KSFO",     # String
}])

# Or cast explicitly
df["temperature"] = df["temperature"].astype(float)
df["station_id"] = df["station_id"].astype(str)
```

### Solution 3: Check S3/MinIO access

```bash
# Verify MinIO is running
curl -s http://localhost:9000/minio/health/live

# Check bucket exists
phlo minio ls local/warehouse/

# Check disk space
phlo minio admin info local/
```

### Solution 4: Verify write permissions

```python
from pyiceberg.catalog import load_catalog
import pyarrow as pa

catalog = load_catalog("default")
table = catalog.load_table("bronze.dlt_weather_observations")

# Test write with minimal data
test_table = pa.table({
    "observation_id": ["test-001"],
    "station_id": ["TEST"],
    "temperature": [0.0],
    "timestamp": ["2024-01-01T00:00:00"],
})

try:
    table.append(test_table)
    print("✅ Write succeeded")
except Exception as e:
    print(f"❌ Write failed: {e}")
```

## Examples

### ❌ Incorrect: Schema mismatch

```python
import pandas as pd

# DataFrame has wrong column names
df = pd.DataFrame([{
    "temp": 18.5,              # ❌ Should be "temperature"
    "station": "KSFO",         # ❌ Should be "station_id"
}])

table.append(df)  # Fails with schema mismatch
```

### ✅ Correct: Matching schema

```python
import pandas as pd

df = pd.DataFrame([{
    "observation_id": "obs-001",
    "station_id": "KSFO",
    "temperature": 18.5,
    "timestamp": "2024-01-15T12:00:00",
}])

table.append(df)  # ✅ Columns match table schema
```

## Debugging Steps

1. **Compare data and table schemas**

   ```python
   from pyiceberg.catalog import load_catalog

   catalog = load_catalog("default")
   table = catalog.load_table("bronze.dlt_weather_observations")

   print("Table schema:")
   for field in table.schema().fields:
       print(f"  {field.name}: {field.field_type} (optional={field.optional})")

   print("\nDataFrame schema:")
   print(df.dtypes)
   ```

2. **Check S3 storage health**

   ```bash
   # MinIO health
   curl -s http://localhost:9000/minio/health/live

   # List warehouse contents
   phlo minio ls --recursive local/warehouse/

   # Check disk usage
   phlo minio admin info local/
   ```

3. **Review write error details**

   ```bash
   docker logs dagster-webserver 2>&1 | grep -i "write\|append\|iceberg" | tail -20
   ```

4. **Test with PyArrow directly**

   ```python
   import pyarrow as pa

   # Convert to PyArrow and check types
   arrow_table = pa.Table.from_pandas(df)
   print(arrow_table.schema)
   ```

## Related Errors

- [PHLO-400: Iceberg Catalog Error](./PHLO-400.md) - Catalog connection failures
- [PHLO-401: Iceberg Table Error](./PHLO-401.md) - Table operation failures
- [PHLO-007: Table Not Found](./PHLO-007.md) - Table doesn't exist
- [PHLO-008: Infrastructure Error](./PHLO-008.md) - MinIO/S3 unavailable
- [PHLO-200: Schema Conversion Error](./PHLO-200.md) - Schema type mapping issues

## Prevention

1. **Validate data before writing**

   ```python
   from workflows.schemas.weather import WeatherObservations

   # Pandera validation catches issues before Iceberg write
   WeatherObservations.validate(df)
   ```

2. **Use Phlo decorators**
   - `phlo.ingest.dlt(...)` handles schema alignment and writes automatically
   - Validation runs before writes, catching mismatches early

3. **Monitor storage capacity**

   ```bash
   # Add to monitoring/alerting
   phlo minio admin info --json local/ | python -c "
   import sys, json
   info = json.load(sys.stdin)
   print(f'Used: {info.get(\"used\", \"unknown\")}')
   "
   ```

4. **Test writes in CI**

   ```python
   def test_write_to_iceberg():
       catalog = load_catalog("default")
       table = catalog.load_table("bronze.dlt_weather_observations")

       test_data = pa.table({
           "observation_id": ["ci-test-001"],
           "station_id": ["TEST"],
           "temperature": [0.0],
           "timestamp": ["2024-01-01T00:00:00"],
       })

       table.append(test_data)
       # Clean up test data
   ```

## Additional Resources

- [PyIceberg Write API](https://py.iceberg.apache.org/)
- [Apache Iceberg Spec — Data Files](https://iceberg.apache.org/spec/#data-files)
- [MinIO Documentation](https://min.io/docs/)
- [PyArrow Documentation](https://arrow.apache.org/docs/python/)

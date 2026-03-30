# PHLO-401: Iceberg Table Error

**Error Type:** Iceberg Table Error
**Severity:** High
**Exception Class:** `PhloError`

## Description

This error occurs when Iceberg table operations fail. This covers operations like loading table metadata, reading table data, updating table properties, or managing table snapshots. It is distinct from [PHLO-007](./PHLO-007.md) (table not found) and [PHLO-402](./PHLO-402.md) (write failures).

## Common Causes

1. **Table not found**
   - Table doesn't exist in the namespace
   - Wrong table name or namespace
   - Table was dropped

2. **Schema mismatch**
   - Table schema evolved incompatibly
   - Attempting to read with wrong schema version
   - Column types changed

3. **Concurrent modification**
   - Two processes modifying the same table
   - Optimistic concurrency conflict
   - Stale metadata reference

4. **Permissions**
   - Insufficient permissions to read/modify table
   - S3 bucket policy denying access
   - Nessie branch protection

## Solutions

### Solution 1: Verify table exists

```python
from pyiceberg.catalog import load_catalog
from pyiceberg.exceptions import NoSuchTableError

catalog = load_catalog("default")

try:
    table = catalog.load_table("bronze.dlt_weather_observations")
    print(f"✅ Table found: {table.metadata.schema()}")
except NoSuchTableError:
    print("❌ Table does not exist")
    print("Available tables:")
    for tbl in catalog.list_tables("bronze"):
        print(f"  - {tbl}")
```

### Solution 2: Check table schema

```python
from pyiceberg.catalog import load_catalog

catalog = load_catalog("default")
table = catalog.load_table("bronze.dlt_weather_observations")

# Inspect current schema
schema = table.schema()
print("Current schema:")
for field in schema.fields:
    print(f"  {field.name}: {field.field_type} (optional={field.optional})")
```

### Solution 3: Handle concurrent modifications

```python
from pyiceberg.catalog import load_catalog
from pyiceberg.exceptions import CommitFailedException

catalog = load_catalog("default")
table = catalog.load_table("bronze.dlt_weather_observations")

try:
    # Perform table operation
    with table.update_schema() as update:
        update.add_column("new_field", "string")
except CommitFailedException:
    # Refresh metadata and retry
    table = catalog.load_table("bronze.dlt_weather_observations")
    with table.update_schema() as update:
        update.add_column("new_field", "string")
```

### Solution 4: Refresh stale table reference

```python
from pyiceberg.catalog import load_catalog

catalog = load_catalog("default")

# Always load fresh table reference before operations
table = catalog.load_table("bronze.dlt_weather_observations")
scan = table.scan()
df = scan.to_pandas()
print(f"✅ Read {len(df)} rows")
```

## Examples

### ❌ Incorrect: Reusing stale table reference

```python
table = catalog.load_table("bronze.observations")
# ... long-running process ...
# ❌ Table metadata may be stale
df = table.scan().to_pandas()
```

### ✅ Correct: Reload before operations

```python
# ✅ Fresh reference before read
table = catalog.load_table("bronze.observations")
df = table.scan().to_pandas()
```

## Debugging Steps

1. **List tables in namespace**

   ```python
   from pyiceberg.catalog import load_catalog

   catalog = load_catalog("default")
   for ns in catalog.list_namespaces():
       tables = catalog.list_tables(ns)
       print(f"{ns}: {tables}")
   ```

2. **Inspect table metadata**

   ```python
   table = catalog.load_table("bronze.dlt_weather_observations")
   print(f"Schema: {table.schema()}")
   print(f"Snapshots: {table.metadata.snapshots}")
   print(f"Properties: {table.properties}")
   ```

3. **Check Nessie branch**

   ```bash
   curl -s http://localhost:19120/api/v2/trees/main | python -m json.tool
   ```

4. **Verify S3 data files**

   ```bash
   phlo minio ls local/warehouse/bronze/dlt_weather_observations/
   ```

## Related Errors

- [PHLO-007: Table Not Found](./PHLO-007.md) - Table doesn't exist
- [PHLO-400: Iceberg Catalog Error](./PHLO-400.md) - Catalog-level failures
- [PHLO-402: Iceberg Write Error](./PHLO-402.md) - Write-specific failures
- [PHLO-200: Schema Conversion Error](./PHLO-200.md) - Schema conversion issues

## Prevention

1. **Use fresh table references**
   - Always call `catalog.load_table()` before critical operations
   - Don't cache table objects across long-running processes

2. **Handle concurrency**

   ```python
   from pyiceberg.exceptions import CommitFailedException

   MAX_RETRIES = 3
   for attempt in range(MAX_RETRIES):
       try:
           table = catalog.load_table(table_name)
           # ... perform operation ...
           break
       except CommitFailedException:
           if attempt == MAX_RETRIES - 1:
               raise
   ```

3. **Monitor table health**

   ```python
   def check_table_health(table_name: str):
       catalog = load_catalog("default")
       table = catalog.load_table(table_name)
       snapshots = table.metadata.snapshots
       print(f"Table: {table_name}")
       print(f"  Schema fields: {len(table.schema().fields)}")
       print(f"  Snapshots: {len(snapshots)}")
   ```

4. **Test table operations in CI**

   ```python
   def test_table_readable():
       catalog = load_catalog("default")
       table = catalog.load_table("bronze.dlt_weather_observations")
       df = table.scan(limit=1).to_pandas()
       assert len(df) >= 0
   ```

## Additional Resources

- [PyIceberg Table API](https://py.iceberg.apache.org/)
- [Apache Iceberg Spec — Table Metadata](https://iceberg.apache.org/spec/#table-metadata)
- [Nessie Branching](https://projectnessie.org/features/transactions/)

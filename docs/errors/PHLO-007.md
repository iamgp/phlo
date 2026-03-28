# PHLO-007: Table Not Found

**Error Type:** Runtime Error
**Severity:** High
**Exception Class:** `PhloTableError`

## Description

This error occurs when an Iceberg table cannot be found in the catalog. Phlo uses Nessie as the Iceberg catalog and stores tables in S3-compatible storage (MinIO). When a referenced table doesn't exist in the catalog, this error is raised.

## Common Causes

1. **Table not yet created**
   - Ingestion asset hasn't run yet
   - Table creation failed silently on first run

2. **Wrong table name**
   - Typo in table reference
   - Asset name doesn't match expected table name
   - Snake_case vs other naming mismatch

3. **Wrong namespace**
   - Table exists in a different Nessie namespace/branch
   - Referencing wrong catalog database

4. **Catalog permissions**
   - Nessie user lacks read access
   - S3/MinIO credentials missing or expired

## Solutions

### Solution 1: Verify the table exists in the catalog

```python
from pyiceberg.catalog import load_catalog

catalog = load_catalog("default")

# List all tables
for namespace in catalog.list_namespaces():
    for table in catalog.list_tables(namespace):
        print(f"{namespace}.{table}")
```

### Solution 2: Run the ingestion asset first

If the table hasn't been created yet, materialize the ingestion asset:

```bash
# Via Dagster UI or CLI
dagster asset materialize --select weather_observations
```

Or trigger via Phlo:

```bash
phlo services start
# Then materialize through the Dagster UI at http://localhost:3000
```

### Solution 3: Check table naming

Phlo uses snake_case for table names derived from asset names:

```python
# Asset name -> Table name
# weather_observations -> dlt_weather_observations (ingestion tables)

# ❌ Wrong table reference
catalog.load_table("default.WeatherObservations")

# ✅ Correct table reference
catalog.load_table("default.dlt_weather_observations")
```

### Solution 4: Verify catalog connection

```python
from pyiceberg.catalog import load_catalog

try:
    catalog = load_catalog("default")
    namespaces = catalog.list_namespaces()
    print(f"✅ Catalog connected. Namespaces: {namespaces}")
except Exception as e:
    print(f"❌ Catalog connection failed: {e}")
```

## Examples

### ❌ Incorrect: Wrong namespace

```python
# Table is in "bronze" namespace, not "default"
table = catalog.load_table("default.weather_observations")
```

### ✅ Correct: Right namespace

```python
table = catalog.load_table("bronze.dlt_weather_observations")
```

### ❌ Incorrect: CamelCase table name

```python
table = catalog.load_table("default.WeatherObservations")
```

### ✅ Correct: snake_case table name

```python
table = catalog.load_table("default.dlt_weather_observations")
```

## Debugging Steps

1. **List all tables in catalog**

   ```bash
   docker exec dagster-webserver python -c "
   from pyiceberg.catalog import load_catalog
   catalog = load_catalog('default')
   for ns in catalog.list_namespaces():
       for tbl in catalog.list_tables(ns):
           print(f'{ns}.{tbl}')
   "
   ```

2. **Check Nessie API**

   ```bash
   curl http://localhost:19120/api/v2/trees/main
   ```

3. **Verify services are running**

   ```bash
   phlo services list --json
   ```

4. **Check S3/MinIO storage**

   ```bash
   # List buckets
   phlo minio ls local/
   ```

## Related Errors

- [PHLO-008: Infrastructure Error](./PHLO-008.md) - Catalog service unavailable
- [PHLO-400: Iceberg Catalog Error](./PHLO-400.md) - Catalog operations failed
- [PHLO-401: Iceberg Table Error](./PHLO-401.md) - Table operations failed
- [PHLO-006: Ingestion Failed](./PHLO-006.md) - Ingestion that creates tables failed

## Prevention

1. **Use Phlo asset dependencies**
   - Ensure downstream assets declare dependencies on ingestion assets
   - Dagster will enforce execution order

2. **Add table existence checks**

   ```python
   from pyiceberg.catalog import load_catalog
   from pyiceberg.exceptions import NoSuchTableError

   def table_exists(table_name: str) -> bool:
       catalog = load_catalog("default")
       try:
           catalog.load_table(table_name)
           return True
       except NoSuchTableError:
           return False
   ```

3. **Follow naming conventions**
   - Asset names in snake_case
   - Ingestion assets use `dlt_<table_name>` prefix
   - Database objects in lowercase

## Additional Resources

- [PyIceberg Documentation](https://py.iceberg.apache.org/)
- [Nessie REST API](https://projectnessie.org/nessie-latest/api/)
- [Phlo Storage Architecture](../reference/architecture.md)

# PHLO-400: Iceberg Catalog Error

**Error Type:** Iceberg Catalog Error
**Severity:** Critical
**Exception Class:** `IcebergCatalogError`

## Description

This error occurs when Iceberg catalog operations fail. Phlo uses Nessie as the Iceberg catalog for managing table metadata, namespaces, and branching. When the catalog is unavailable, misconfigured, or rejects operations, this error is raised.

## Common Causes

1. **Catalog not initialized**
   - Nessie service not started
   - Catalog configuration missing from environment
   - First-time setup not completed

2. **Connection failed**
   - Nessie endpoint unreachable
   - Network timeout
   - DNS resolution failure

3. **Permissions denied**
   - Catalog user lacks required permissions
   - Authentication token expired
   - Namespace access restricted

4. **S3/MinIO unavailable**
   - MinIO service not running
   - S3 bucket doesn't exist
   - S3 credentials invalid

## Solutions

### Solution 1: Start catalog services

```bash
# Start all Phlo services (includes Nessie + MinIO)
phlo services start

# Verify Nessie is running
curl -s http://localhost:19120/api/v2/config | python -m json.tool
```

### Solution 2: Verify catalog configuration

Check that catalog settings are correct in `.phlo/.env`:

```bash
# .phlo/.env
NESSIE_URI=http://localhost:19120/api/v2
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=password
```

### Solution 3: Test catalog connection

```python
from pyiceberg.catalog import load_catalog

try:
    catalog = load_catalog("default")
    namespaces = catalog.list_namespaces()
    print(f"✅ Catalog connected. Namespaces: {namespaces}")
except Exception as e:
    print(f"❌ Catalog error: {e}")
```

### Solution 4: Create missing namespace

```python
from pyiceberg.catalog import load_catalog

catalog = load_catalog("default")

# Create namespace if it doesn't exist
existing = [ns[0] for ns in catalog.list_namespaces()]
if "bronze" not in existing:
    catalog.create_namespace("bronze")
    print("✅ Created 'bronze' namespace")
```

## Examples

### ❌ Incorrect: No catalog error handling

```python
from pyiceberg.catalog import load_catalog

catalog = load_catalog("default")
table = catalog.load_table("bronze.observations")  # Fails silently if catalog down
```

### ✅ Correct: Handle catalog errors

```python
from pyiceberg.catalog import load_catalog
from phlo.exceptions import IcebergCatalogError

try:
    catalog = load_catalog("default")
    table = catalog.load_table("bronze.observations")
except Exception as e:
    raise IcebergCatalogError(
        message="Failed to connect to Iceberg catalog",
        suggestions=[
            "Run 'phlo services start' to start infrastructure",
            "Check Nessie: curl http://localhost:19120/api/v2/config",
            "Verify NESSIE_URI in .phlo/.env",
        ],
        cause=e,
    )
```

## Debugging Steps

1. **Check Nessie health**

   ```bash
   curl -s http://localhost:19120/api/v2/config
   ```

2. **List catalog contents**

   ```bash
   curl -s http://localhost:19120/api/v2/trees/main | python -m json.tool
   ```

3. **Check Nessie container**

   ```bash
   docker ps -a --filter "name=nessie"
   docker logs nessie --tail=50
   ```

4. **Check MinIO health**

   ```bash
   curl -s http://localhost:9000/minio/health/live
   ```

5. **Verify S3 buckets exist**

   ```bash
   phlo minio ls local/
   ```

6. **Test PyIceberg connection**

   ```python
   from pyiceberg.catalog import load_catalog

   catalog = load_catalog("default")
   print("Namespaces:", catalog.list_namespaces())
   for ns in catalog.list_namespaces():
       print(f"  Tables in {ns}:", catalog.list_tables(ns))
   ```

## Related Errors

- [PHLO-401: Iceberg Table Error](./PHLO-401.md) - Table-level operations failed
- [PHLO-402: Iceberg Write Error](./PHLO-402.md) - Write operations failed
- [PHLO-007: Table Not Found](./PHLO-007.md) - Specific table not in catalog
- [PHLO-008: Infrastructure Error](./PHLO-008.md) - General infrastructure failures

## Prevention

1. **Start services before development**

   ```bash
   phlo services start
   phlo services list --json
   ```

2. **Add catalog connectivity tests**

   ```python
   # tests/test_infrastructure.py
   from pyiceberg.catalog import load_catalog

   def test_catalog_connected():
       catalog = load_catalog("default")
       namespaces = catalog.list_namespaces()
       assert len(namespaces) > 0, "No namespaces found in catalog"
   ```

3. **Use health checks in CI/CD**

   ```bash
   #!/bin/bash
   # scripts/wait-for-services.sh
   echo "Waiting for Nessie..."
   until curl -sf http://localhost:19120/api/v2/config > /dev/null; do
       sleep 2
   done
   echo "✅ Nessie ready"
   ```

4. **Configure connection timeouts**

   ```python
   from pyiceberg.catalog import load_catalog

   catalog = load_catalog(
       "default",
       **{"uri": "http://localhost:19120/api/v2", "timeout": 10},
   )
   ```

## Additional Resources

- [Nessie Documentation](https://projectnessie.org/)
- [Nessie REST API](https://projectnessie.org/nessie-latest/api/)
- [PyIceberg Catalog Configuration](https://py.iceberg.apache.org/)
- [Service Packages Guide](../guides/service-packages.md)

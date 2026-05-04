# PHLO-008: Infrastructure Error

**Error Type:** Infrastructure Error
**Severity:** Critical
**Exception Class:** `PhloInfrastructureError`

## Description

This error occurs when infrastructure services required by Phlo are unavailable or not responding. Phlo depends on several services (Dagster, Nessie, MinIO, Trino, Postgres) and this error is raised when connections to these services fail.

## Common Causes

1. **Services not running**
   - `phlo services start` not executed
   - Docker containers crashed or stopped
   - Docker daemon not running

2. **Connection refused**
   - Service is starting up (not ready yet)
   - Port conflict with another application
   - Service bound to wrong interface

3. **Authentication failed**
   - Credentials in `.phlo/.env` incorrect
   - Credentials rotated but not updated
   - Environment variables not loaded

4. **Resource exhaustion**
   - Docker out of disk space
   - Insufficient memory for containers
   - Too many open connections

## Solutions

### Solution 1: Start Phlo services

```bash
# Start all services
phlo services start

# Verify services are running
phlo services list --json
```

### Solution 2: Check Docker status

```bash
# Check Docker is running
docker info

# Check container status
docker ps -a --filter "label=phlo"

# Restart crashed containers
phlo services restart
```

### Solution 3: Check service logs

```bash
# View logs for a specific service
phlo services logs -f dagster-webserver

# Check all services
phlo services logs -f
```

### Solution 4: Verify connection settings

Check `.phlo/.env` has correct connection details:

```bash
# .phlo/.env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
NESSIE_URI=http://localhost:19120/api/v2
MINIO_ENDPOINT=http://localhost:9000
TRINO_HOST=localhost
TRINO_PORT=8080
```

Test connectivity:

```bash
# Postgres
pg_isready -h localhost -p 5432

# Nessie
curl -s http://localhost:19120/api/v2/config | head -1

# MinIO
curl -s http://localhost:9000/minio/health/live

# Trino
curl -s http://localhost:8080/v1/info
```

## Examples

### ❌ Incorrect: Assuming services are running

```python
from pyiceberg.catalog import load_catalog

# ❌ No check — will fail if Nessie is down
catalog = load_catalog("default")
tables = catalog.list_tables("bronze")
```

### ✅ Correct: Check service availability

```python
from phlo.exceptions import PhloInfrastructureError
from pyiceberg.catalog import load_catalog

try:
    catalog = load_catalog("default")
    tables = catalog.list_tables("bronze")
except Exception as e:
    raise PhloInfrastructureError(
        message="Cannot connect to Iceberg catalog (Nessie)",
        suggestions=[
            "Run 'phlo services start' to start infrastructure",
            "Check Nessie is running: curl http://localhost:19120/api/v2/config",
            "Review logs: phlo services logs -f nessie",
        ],
        cause=e,
    )
```

## Debugging Steps

1. **Check all service health**

   ```bash
   phlo services list --json
   ```

2. **View container status**

   ```bash
   docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
   ```

3. **Check resource usage**

   ```bash
   docker stats --no-stream
   ```

4. **Review service logs for errors**

   ```bash
   phlo services logs -f dagster-webserver
   phlo services logs -f nessie
   phlo services logs -f minio
   phlo services logs -f trino
   phlo services logs -f postgres
   ```

5. **Check Docker disk usage**

   ```bash
   docker system df
   ```

6. **Reset services**

   ```bash
   phlo services stop
   phlo services reset
   phlo services start
   ```

## Service Port Reference

| Service           | Default Port | Health Check URL                          |
| ----------------- | ------------ | ----------------------------------------- |
| Dagster Webserver | 3000         | `http://localhost:3000`                    |
| Nessie            | 19120        | `http://localhost:19120/api/v2/config`     |
| MinIO API         | 9000         | `http://localhost:9000/minio/health/live`  |
| MinIO Console     | 9001         | `http://localhost:9001`                    |
| Trino             | 8080         | `http://localhost:8080/v1/info`            |
| Postgres          | 5432         | `pg_isready -h localhost -p 5432`         |

## Related Errors

- [PHLO-006: Ingestion Failed](./PHLO-006.md) - Ingestion fails due to infra issues
- [PHLO-007: Table Not Found](./PHLO-007.md) - Table missing (catalog may be down)
- [PHLO-400: Iceberg Catalog Error](./PHLO-400.md) - Catalog-specific infra failures

## Prevention

1. **Start services before development**

   ```bash
   phlo services start
   phlo services list --json  # Verify all healthy
   ```

2. **Add health checks to workflows**

   ```python
   import requests

   def check_infrastructure():
       services = {
           "Nessie": "http://localhost:19120/api/v2/config",
           "MinIO": "http://localhost:9000/minio/health/live",
           "Trino": "http://localhost:8080/v1/info",
       }
       for name, url in services.items():
           try:
               requests.get(url, timeout=5).raise_for_status()
           except Exception:
               raise PhloInfrastructureError(
                   message=f"{name} is not available at {url}",
                   suggestions=[
                       f"Check {name} container: docker logs {name.lower()}",
                       "Run 'phlo services restart' to restart all services",
                   ],
               )
   ```

3. **Monitor with Docker health checks**
   - Phlo services include Docker health checks
   - Use `docker ps` to see health status
   - Set up alerting on container restarts

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Service Packages Guide](../guides/service-packages.md)
- [Troubleshooting Guide](../operations/troubleshooting.md)

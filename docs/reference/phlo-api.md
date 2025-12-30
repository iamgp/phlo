# phlo-api

Observatory backend API for Phlo infrastructure management.

## Overview

The `phlo-api` is a FastAPI-based backend service that provides the Observatory UI with access to:

- **Plugin & Service Management**: Discover and manage plugins and services
- **Data Querying**: Execute queries against Trino and Iceberg tables
- **Orchestration**: Interact with Dagster assets and runs
- **Data Catalog**: Manage Nessie branches and catalog metadata
- **Quality Monitoring**: Query data quality check results
- **Logging**: Search and correlate logs via Loki
- **Lineage Tracking**: Row-level lineage queries
- **Maintenance**: Iceberg maintenance operation status
- **Search**: Unified search across assets, tables, and columns

## Quick Start

```bash
# Start the API service
phlo services start --service phlo-api

# Or run natively in dev mode (no Docker)
phlo services start --native
```

Access the API at:

- **Base URL**: http://localhost:4000
- **Health Check**: http://localhost:4000/health
- **OpenAPI Docs**: http://localhost:4000/docs
- **Metrics**: http://localhost:4000/metrics

## Complete API Reference

See the full API reference documentation in the phlo-api package:

**[phlo-api API Reference](../../packages/phlo-api/docs/api-reference.md)**

This includes detailed documentation for all endpoints:

- Core endpoints (health, config, plugins, services, registry)
- Trino query engine (connection, preview, profiling, metrics, query execution)
- Iceberg tables (list, schema, metadata)
- Dagster assets (health, assets, history)
- Nessie catalog (branches, commits, merge, diff)
- Data quality (overview, checks, history)
- Logging (Loki integration, run logs, asset logs)
- Row lineage (ancestors, descendants, journey)
- Maintenance (status, metrics)
- Search index (assets, tables, columns)

## Key Features

### 1. Read-Only Query Guardrails

The API enforces read-only mode by default for ad-hoc queries:

- Blocks `INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, `ALTER`, `TRUNCATE`, `MERGE`
- Prevents multiple statements (SQL injection protection)
- 30-second query timeout
- 10,000 row limit

### 2. Caching

Intelligent caching for frequently accessed data:

- **Tables list**: 1 minute TTL
- **Table schema**: 5 minutes TTL
- In-memory cache (can be extended with Redis)

### 3. Connection Flexibility

All endpoints support URL overrides via query parameters for testing:

```bash
# Use different Trino instance
curl "http://localhost:4000/api/trino/preview/my_table?trino_url=http://trino-prod:8080"

# Use different Dagster instance
curl "http://localhost:4000/api/dagster/assets?dagster_url=http://localhost:3000/graphql"
```

### 4. Log Correlation

Loki endpoints support correlation by:

- `run_id`: Dagster run identifier
- `asset_key`: Asset name
- `job_name`: Dagster job name
- `partition_key`: Partition identifier
- `check_name`: Quality check name

### 5. Row-Level Lineage

Track individual row provenance through transformations:

```bash
# Get full lineage journey for a row
curl http://localhost:4000/api/lineage/rows/abc-123/journey
```

## Configuration

Configure via environment variables:

```bash
# API Server
PHLO_API_PORT=4000
HOST=0.0.0.0

# Backend Services
TRINO_URL=http://trino:10005
DAGSTER_GRAPHQL_URL=http://dagster:3000/graphql
NESSIE_URL=http://nessie:19120/api/v2
LOKI_URL=http://loki:3100
```

## Architecture

The API is structured as:

```
phlo-api/
├── main.py                      # Core endpoints (config, plugins, services)
└── observatory_api/
    ├── trino.py                 # Query execution
    ├── iceberg.py               # Table catalog
    ├── dagster.py               # Asset management
    ├── nessie.py                # Version control
    ├── quality.py               # Quality checks
    ├── loki.py                  # Log queries
    ├── lineage.py               # Row lineage
    ├── maintenance.py           # Maintenance metrics
    └── search.py                # Unified search
```

Each router is independently importable and can be disabled by removing the import in `main.py`.

## Development

### Running Locally

```bash
# Install in editable mode
cd packages/phlo-api
pip install -e .

# Run directly
python -m phlo_api.main

# Or via uvicorn
uvicorn phlo_api.main:app --reload --port 4000
```

### Adding New Endpoints

1. Create a new router in `observatory_api/`:

```python
# observatory_api/my_feature.py
from fastapi import APIRouter
router = APIRouter(tags=["my_feature"])

@router.get("/status")
async def get_status():
    return {"status": "ok"}
```

2. Register in `main.py`:

```python
from phlo_api.observatory_api.my_feature import router as my_feature_router
app.include_router(my_feature_router, prefix="/api/my-feature")
```

## Monitoring

The API automatically exposes Prometheus metrics at `/metrics`:

```bash
curl http://localhost:4000/metrics
```

Metrics include:

- HTTP request counts and duration
- Active requests
- Error rates

These metrics are automatically scraped by Prometheus when the observability stack is running.

## Troubleshooting

### API Won't Start

```bash
# Check logs
docker logs phlo-api-1

# Or if running natively
docker logs dagster-webserver  # Check native service logs
```

### Backend Connection Errors

Test each backend service:

```bash
# Trino
curl http://localhost:10005/v1/info

# Dagster
curl http://localhost:3000/graphql

# Nessie
curl http://localhost:19120/api/v2/config

# Loki
curl http://localhost:3100/ready
```

### Slow Queries

- Check Trino query history at http://localhost:10005/ui
- Use smaller `limit` values for data preview
- Check table partitioning and use partition filters
- Monitor query execution times in response metadata

## Next Steps

- [phlo-api Package README](../../packages/phlo-api/README.md)
- [phlo-api Complete API Reference](../../packages/phlo-api/docs/api-reference.md)
- [Observatory Package](../../packages/phlo-observatory/README.md)
- [CLI Reference](cli-reference.md)

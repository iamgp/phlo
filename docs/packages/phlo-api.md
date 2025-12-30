# phlo-api

Backend API service for Phlo Observatory.

## Overview

`phlo-api` is a FastAPI-based backend service that exposes Phlo internals to the Observatory UI. It provides endpoints for lineage, quality checks, assets, branches, and metadata.

## Installation

```bash
pip install phlo-api
# or
phlo plugin install api
```

## Configuration

| Variable        | Default   | Description     |
| --------------- | --------- | --------------- |
| `PHLO_API_PORT` | `4000`    | API server port |
| `HOST`          | `0.0.0.0` | API server host |

## Features

### Auto-Configuration

| Feature               | How It Works                                            |
| --------------------- | ------------------------------------------------------- |
| **Metrics Labels**    | Exposes Prometheus metrics at `/metrics`                |
| **Service Discovery** | Automatically scraped by Prometheus                     |
| **Health Check**      | Provides `/health` endpoint for container orchestration |

## Usage

### Starting the Service

```bash
# Start the API service
phlo services start --service phlo-api

# Or run in native mode (better for ARM Macs)
phlo services start --native
```

## API Routes

| Route                        | Method   | Description               |
| ---------------------------- | -------- | ------------------------- |
| `/health`                    | GET      | Health check              |
| `/api/config`                | GET      | Project configuration     |
| `/api/plugins`               | GET      | List all plugins          |
| `/api/plugins/{type}`        | GET      | List plugins by type      |
| `/api/plugins/{type}/{name}` | GET      | Get plugin details        |
| `/api/services`              | GET      | List all services         |
| `/api/services/{name}`       | GET      | Get service details       |
| `/api/registry`              | GET      | Plugin registry           |
| `/api/lineage/*`             | GET      | Data lineage queries      |
| `/api/quality/*`             | GET      | Quality check results     |
| `/api/dagster/*`             | GET      | Dagster asset information |
| `/api/nessie/*`              | GET      | Nessie branch management  |
| `/api/iceberg/*`             | GET      | Iceberg table operations  |
| `/api/trino/*`               | GET/POST | Query execution           |
| `/api/loki/*`                | GET      | Log queries               |
| `/api/maintenance/*`         | GET      | Maintenance operations    |
| `/api/search/*`              | GET      | Unified search            |

### Example Requests

```bash
# Health check
curl http://localhost:4000/health

# Get lineage for a table
curl "http://localhost:4000/api/lineage?table=bronze.users"

# Get quality check results
curl "http://localhost:4000/api/quality?asset=bronze.users"

# List Nessie branches
curl http://localhost:4000/api/nessie/branches

# Execute a query
curl -X POST http://localhost:4000/api/trino/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM bronze.users LIMIT 10"}'
```

## Endpoints

| Endpoint         | URL                             |
| ---------------- | ------------------------------- |
| **API Base**     | `http://localhost:4000`         |
| **Health**       | `http://localhost:4000/health`  |
| **Metrics**      | `http://localhost:4000/metrics` |
| **OpenAPI Docs** | `http://localhost:4000/docs`    |
| **ReDoc**        | `http://localhost:4000/redoc`   |

## Entry Points

| Entry Point             | Plugin                 |
| ----------------------- | ---------------------- |
| `phlo.plugins.services` | `PhloApiServicePlugin` |

## Related Packages

- [phlo-observatory](phlo-observatory.md) - Frontend UI
- [phlo-dagster](phlo-dagster.md) - Asset information
- [phlo-nessie](phlo-nessie.md) - Branch management
- [phlo-lineage](phlo-lineage.md) - Lineage data

## Next Steps

- [API Reference](../reference/phlo-api.md) - Full API documentation
- [Observability Setup](../setup/observability.md) - API monitoring

# phlo-api (/docs/packages/phlo-api)



Overview [#overview]

`phlo-api` is a FastAPI-based backend service that exposes Phlo internals to the Observatory UI. It provides endpoints for lineage, quality checks, assets, branches, and metadata.

Installation [#installation]

```bash
pip install phlo-api
# or
phlo plugin install api
```

Configuration [#configuration]

| Variable                     | Default   | Description                                                                               |
| ---------------------------- | --------- | ----------------------------------------------------------------------------------------- |
| `PHLO_API_PORT`              | `4000`    | API server port                                                                           |
| `HOST`                       | `0.0.0.0` | API server host                                                                           |
| `PHLO_QUERY_ENGINE_URL`      | none      | Explicit query-engine HTTP endpoint for `/api/trino/*` and catalog-backed metadata routes |
| `PHLO_QUERY_CATALOG`         | none      | Default query catalog when request payloads do not provide one                            |
| `PHLO_DEFAULT_REF`           | none      | Default ref/schema context when request payloads do not provide one                       |
| `PHLO_API_DISCOVERY_SCHEMAS` | none      | Comma-separated schema list for `/api/iceberg/tables` and `/api/search/index` discovery   |

`/api/trino/*` and `/api/iceberg/*` remain compatibility route names. The backing URL, catalog, ref, and discovery schemas are resolved from explicit config or `query_engine` capability metadata; the API no longer silently assumes the bundled Trino/Nessie defaults.

Features [#features]

Auto-Configuration [#auto-configuration]

| Feature               | How It Works                                            |
| --------------------- | ------------------------------------------------------- |
| **Metrics Labels**    | Exposes Prometheus metrics at `/metrics`                |
| **Service Discovery** | Automatically scraped by Prometheus                     |
| **Health Check**      | Provides `/health` endpoint for container orchestration |

Usage [#usage]

Starting the Service [#starting-the-service]

```bash
# Start the API service
phlo services start --service phlo-api

# Or run in native mode (better for ARM Macs)
phlo services start --native
```

API Routes [#api-routes]

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

Example Requests [#example-requests]

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

Endpoints [#endpoints]

| Endpoint         | URL                             |
| ---------------- | ------------------------------- |
| **API Base**     | `http://localhost:4000`         |
| **Health**       | `http://localhost:4000/health`  |
| **Metrics**      | `http://localhost:4000/metrics` |
| **OpenAPI Docs** | `http://localhost:4000/docs`    |
| **ReDoc**        | `http://localhost:4000/redoc`   |

Entry Points [#entry-points]

| Entry Point             | Plugin                 |
| ----------------------- | ---------------------- |
| `phlo.plugins.services` | `PhloApiServicePlugin` |

Related Packages [#related-packages]

* [phlo-observatory](phlo-observatory.md) - Frontend UI
* [phlo-dagster](phlo-dagster.md) - Asset information
* [phlo-nessie](phlo-nessie.md) - Branch management
* [phlo-lineage](phlo-lineage.md) - Lineage data

Next Steps [#next-steps]

* [API Reference](../reference/phlo-api.md) - Full API documentation
* [Observability Setup](../setup/observability.md) - API monitoring

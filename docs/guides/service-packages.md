# Service Packages

Phlo services are distributed as Python packages. Each service package ships its own `service.yaml`
definition and registers a `phlo.plugins.services` entry point for CLI discovery.

## Architecture

Phlo services are organized into **core** and **package** services:

### Core Services

Core services are bundled with `pip install phlo` and cannot be removed:

- **Observatory** - Data platform UI for visibility and lineage
- **phlo-api** - Backend API exposing phlo internals to Observatory

### Package Services

Package services are installed separately and can be swapped for alternatives:

```bash
# Install default services (recommended)
pip install phlo[defaults]

# Or install individually
pip install phlo-dagster phlo-postgres phlo-trino
```

Default package services:

- `phlo-dagster` - Data orchestration platform
- `phlo-postgres` - PostgreSQL for Dagster metadata
- `phlo-minio` - S3-compatible object storage
- `phlo-nessie` - Git-like catalog for Iceberg
- `phlo-trino` - Distributed SQL query engine

Optional packages:

- `phlo-superset` - Business intelligence
- `phlo-pgweb` - PostgreSQL web admin
- `phlo-postgrest` - Auto-generated REST API
- `phlo-hasura` - GraphQL API
- `phlo-prometheus` - Metrics [observability]
- `phlo-grafana` - Dashboards [observability]
- `phlo-loki` - Log aggregation [observability]
- `phlo-alloy` - Log shipping [observability]

## Customizing Services

Override service settings in your `phlo.yaml`:

```yaml
name: my-lakehouse

services:
  # Override a package service
  observatory:
    ports:
      - "8080:3000"
    environment:
      DEBUG: "true"

  # Disable a default service
  superset:
    enabled: false

  # Add a custom inline service
  custom-api:
    type: inline
    image: my-registry/api:latest
    ports:
      - "4000:4000"
    depends_on:
      - trino
```

### Override Behavior

| Setting          | Behavior                      |
| ---------------- | ----------------------------- |
| `ports`          | Replaces package defaults     |
| `environment`    | Merges (user values override) |
| `volumes`        | Appends to package defaults   |
| `depends_on`     | Replaces package defaults     |
| `command`        | Replaces package defaults     |
| `enabled: false` | Excludes service entirely     |

## Discovering Services

```bash
# List installed services
phlo services list

# Show all including optional profiles
phlo services list --all

# JSON output
phlo services list --json
```

Example output:

```
CORE SERVICES (bundled with phlo):
  ✓ observatory: Phlo Observatory - Data platform visibility and lineage UI
  ✓ phlo-api: Phlo API - Backend service exposing phlo internals

ORCHESTRATION (packages):
  ✓ dagster: Data orchestration platform
  ✓ dagster-daemon: Dagster daemon for schedules and sensors

BI (packages):
  ✓ superset: Apache Superset for business intelligence
```

## Development Mode

Mount local package sources into containers for live development:

```bash
phlo services init --dev --phlo-source /path/to/phlo
phlo services start
```

Dev mode uses the `dev` section in each service's `service.yaml` to override commands, volumes, and environment.

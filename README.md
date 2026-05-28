<img src="./.github/readme-header.png" alt="Phlo" width="900">

# The Pythonic lakehouse framework.

Build lakehouse pipelines in Python, without the boilerplate.

## Why Phlo

Most lakehouse projects start in Python and quickly spill into YAML, Compose files, orchestration config, catalog setup, quality checks, and a pile of small scripts. Phlo keeps those pieces in one project.

Use the CLI to create a project, start the local stack, materialize assets, run checks, and inspect what happened. Add provider packages when you need them: Dagster for orchestration, DLT or Sling for ingestion, dbt for transforms, Iceberg or Delta for tables, Trino for query, and Observatory when you want a UI.

## What You Get

- A project layout for `phlo.yaml`, workflows, schemas, transforms, tests, local runtime state, and project plugins.
- Starters for CSV ingestion, REST API ingestion, dbt medallion projects, Sling replication, and Observatory demos.
- Python decorators for registering assets without hand-writing provider boilerplate.
- Local service commands for generating, starting, checking, logging, and stopping the stack.
- Packages for Dagster, MinIO, Nessie, Trino, Iceberg, dbt, PostgreSQL, Observatory, and other lakehouse services.
- Plugin hooks for custom commands, services, assets, resources, catalogs, and Observatory extensions.

## Quick Start

Prerequisites: Python 3.11 or later, `uv`, and Docker/Podman.

```bash
# Install Phlo with the default local stack packages
uv pip install "phlo[defaults]"

# Create a project from the CSV batch starter
phlo init my-lakehouse --template csv-batch
cd my-lakehouse
uv pip install -e .

# Generate and start the local service stack
phlo services init
phlo services start

# Run the generated asset for a completed daily partition
phlo materialize dlt_events --partition 2025-01-15
```

## What It Looks Like

The `csv-batch` starter gives you a DLT-backed asset with a validation schema and a daily partition:

```python
from pathlib import Path

import dlt
import pandas as pd
import phlo

from workflows.schemas.csv import EventsSchema


@phlo.ingestion(
    table_name="events",
    unique_key="event_id",
    validation_schema=EventsSchema,
    group="csv",
    freshness_hours=(1, 24),
)
def csv_events(partition_date: str) -> object:
    events = pd.read_csv(Path("data/events.csv"))
    events["event_id"] = events["id"].astype(str) + "-" + partition_date
    rows = events.to_dict(orient="records")
    return dlt.resource(rows, name="events")
```

## Architecture

Phlo's core stays small. Provider packages register services, commands, assets, resources, and catalog adapters through Python entry points. The CLI reads the active project and wires together the packages you installed.

| Layer | Packages |
| --- | --- |
| Orchestration | `phlo-dagster` |
| Ingestion | `phlo-dlt`, `phlo-sling` |
| Quality | `phlo-pandera` |
| Transforms | `phlo-dbt` |
| Table formats | `phlo-iceberg`, `phlo-delta`, `phlo-clickhouse` |
| Storage | `phlo-minio`, `phlo-rustfs` |
| Catalog | `phlo-nessie`, `phlo-openmetadata` |
| Query | `phlo-trino` |
| API and UI | `phlo-api`, `phlo-observatory`, `phlo-mcp`, `phlo-hasura`, `phlo-postgrest`, `phlo-pgweb`, `phlo-superset` |
| Observability | `phlo-otel`, `phlo-clickstack`, `phlo-grafana`, `phlo-prometheus`, `phlo-loki`, `phlo-alloy`, `phlo-alerting` |
| Dev and test | `phlo-testing` |

## Documentation

- [Installation Guide](docs/getting-started/installation.md)
- [Quickstart Guide](docs/getting-started/quickstart.md)
- [Core Concepts](docs/getting-started/core-concepts.md)
- [Choosing Components](docs/guides/choosing-components.md)
- [Workflow Development](docs/guides/workflow-development.md)
- [Plugin Development](docs/guides/plugin-development.md)
- [Operations Guide](docs/operations/operations-guide.md)
- [CLI Reference](docs/reference/cli-reference.md)

## Development

```bash
uv pip install -e .
make check
```

Useful local service commands:

```bash
phlo services init
phlo services start
phlo services status
phlo services logs -f
phlo services stop
phlo doctor --verbose
```

<p align="center">
  <img src="docs/assets/phlo.png" alt="Phlo" width="400">
</p>

<p align="center">
  <strong>Modern data lakehouse platform. Plugin-driven. Storage-agnostic.</strong>
</p>

<p align="center">
  <a href="https://github.com/phlohouse/phlo/actions/workflows/ci.yml"><img src="https://github.com/phlohouse/phlo/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/phlo/"><img src="https://img.shields.io/pypi/v/phlo" alt="PyPI"></a>
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+">
</p>

## Features

- **Template-first projects** — `phlo init` creates focused starters for CSV, REST APIs, dbt medallion projects, Sling replication, and observability demos
- **Decorator-driven ingestion** — `phlo-dlt` and `phlo-sling` register assets without hand-written Dagster boilerplate
- **Type-safe quality contracts** — `phlo-pandera` schemas validate data before it lands in managed tables
- **Capability plugins** — packages contribute services, CLI commands, assets, resources, catalogs, hooks, and Observatory surfaces through Python entry points
- **Storage-agnostic data plane** — Iceberg, Delta, ClickHouse, Trino, MinIO, RustFS, Nessie, and PostgreSQL can be composed as needed
- **Operator surfaces** — `phlo-api`, Observatory, MCP, PostgREST, Hasura, Superset, pgweb, and observability packages expose runtime state and actions
- **Local-first operations** — `phlo services` generates and runs the project stack through Docker or Podman

## What It Looks Like

```python
from pathlib import Path

import pandas as pd
import pandera.pandas as pa
from pandera.typing import Series

import phlo


class EventsSchema(pa.DataFrameModel):
    id: Series[int] = pa.Field(ge=1)
    name: Series[str]
    value: Series[int] = pa.Field(ge=0)

    class Config:
        strict = True
        coerce = True


@phlo.ingest.dlt(
    table_name="events",
    unique_key="id",
    validation_schema=EventsSchema,
    group="demo",
    freshness_hours=(1, 24),
)
def events(partition_date: str):
    return pd.read_csv(Path("data/events.csv"))
```

`phlo.ingest` is the provider-neutral ingestion namespace. Use `phlo.ingest.dlt(...)`
for Python, REST, and DataFrame sources; `phlo.ingest.sling(...)` for replication;
or `phlo.ingest.provider("name")` for third-party ingestion providers. Existing
`@phlo.ingestion(...)` workflows remain supported as a DLT compatibility alias.

## Prerequisites

- [uv](https://github.com/astral-sh/uv) — Python package manager
- [Docker](https://www.docker.com/) — Container runtime

## Quick Start

```bash
# Install with default plugins
uv pip install phlo[defaults]

# Initialize a runnable local starter
phlo init my-project --template csv-batch
cd my-project

# Generate service configuration, start services, and materialize
phlo services init
phlo services start
phlo materialize dlt_events --partition 2026-05-04
```

## Documentation

Full documentation source lives under [docs/index.md](docs/index.md). The published site is generated with `pymdx`, matching the GitHub Pages workflow:

```bash
pymdx generate src/phlo --docs docs --output docs-site
pymdx build docs-site
```

Primary entry points:

- [Installation Guide](docs/getting-started/installation.md)
- [Quickstart Guide](docs/getting-started/quickstart.md)
- [Core Concepts](docs/getting-started/core-concepts.md)
- [Developer Guide](docs/guides/developer-guide.md)
- [Plugin Development](docs/guides/plugin-development.md)
- [Workflow Development](docs/guides/workflow-development.md)
- [CLI Reference](docs/reference/cli-reference.md)
- [Configuration Reference](docs/reference/configuration-reference.md)
- [Operations Guide](docs/operations/operations-guide.md)

## Development

```bash
uv pip install -e .    # Install Phlo in dev mode
make check             # Lint, format, typecheck, and test (parallel)

# Services
phlo services start    # Start infrastructure
phlo services stop     # Stop services
phlo services logs -f  # View logs

# Individual gates
uv run ruff check .    # Lint
uv run ruff format .   # Format
uv run ty check        # Typecheck
uv run pytest          # Test
```

## Architecture

Phlo is a monorepo of composable packages — install only what you need:

| Layer             | Packages                                                                                  |
| ----------------- | ----------------------------------------------------------------------------------------- |
| **Orchestration** | `phlo-dagster`                                                                            |
| **Ingestion**     | `phlo-dlt`, `phlo-sling`                                                                  |
| **Quality**       | `phlo-pandera`                                                                            |
| **Transforms**    | `phlo-dbt`                                                                                |
| **Table formats** | `phlo-iceberg`, `phlo-delta`, `phlo-clickhouse`                                           |
| **Infrastructure**  | `phlo-traefik`, `phlo-postgres`, `phlo-oauth2-proxy`                                    |
| **Storage**       | `phlo-minio`, `phlo-rustfs`                                                               |
| **Catalog**       | `phlo-nessie`, `phlo-openmetadata`                                                        |
| **Query**         | `phlo-trino`                                                                              |
| **Observability** | `phlo-otel`, `phlo-clickstack`, `phlo-grafana`, `phlo-prometheus`, `phlo-loki`, `phlo-alloy`, `phlo-alerting` |
| **UI**            | `phlo-observatory`, `phlo-pgweb`, `phlo-superset`                                         |
| **API**           | `phlo-api`, `phlo-mcp`, `phlo-hasura`, `phlo-postgrest`                                  |
| **Dev/Test**      | `phlo-testing`                                                                            |

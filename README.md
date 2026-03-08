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

- **Decorator-driven development** — `@phlo.ingestion` and `@phlo.quality` replace hundreds of lines of boilerplate
- **Write-Audit-Publish pattern** — Git-like branching with automatic quality gates and promotion
- **Type-safe data quality** — Pandera schemas enforce validation at ingestion time
- **Plugin architecture** — 12 plugin types: sources, quality, ingestion, transforms, services, hooks, catalogs, assets, resources, orchestrators, and CLI commands
- **Storage-agnostic** — Iceberg, Delta, or bring-your-own via table-format plugins
- **Observatory UI** — Web-based data exploration, lineage, and monitoring
- **Observability** — OpenTelemetry traces, metrics, and logs via `phlo-otel`; Grafana/Prometheus/Loki stack
- **Production-ready** — Auto-publishing, configurable merge strategies, freshness policies, data migrations

## What It Looks Like

```python
import phlo

@phlo.ingestion(
    table_name="events",
    unique_key="id",
    validation_schema=EventSchema,
    group="api",
    cron="0 */1 * * *",
    freshness_hours=(1, 24),
)
def api_events(partition_date: str):
    return rest_api(...)  # Any DLT source


@phlo.quality(
    table="bronze.events",
    checks=[
        NullCheck(columns=["id", "timestamp"]),
        RangeCheck(column="value", min_value=0, max_value=100),
        UniqueCheck(columns=["id"]),
        FreshnessCheck(column="timestamp", max_age_hours=24),
    ],
)
def events_quality():
    pass
```

## Prerequisites

- [uv](https://github.com/astral-sh/uv) — Python package manager
- [Docker](https://www.docker.com/) — Container runtime

## Quick Start

```bash
# Install with default plugins
uv pip install phlo[defaults]

# Initialize a new project
phlo init my-project
cd my-project

# Start services and materialize
phlo services start
phlo materialize --select "dlt_glucose_entries+"
```

## Documentation

Full documentation at [docs/index.md](docs/index.md):

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
| **Ingestion**     | `phlo-dlt`                                                                                |
| **Quality**       | `phlo-pandera`                                                                            |
| **Transforms**    | `phlo-dbt`                                                                                |
| **Table formats** | `phlo-iceberg`, `phlo-delta`                                                              |
| **Storage**       | `phlo-minio`                                                                              |
| **Catalog**       | `phlo-nessie`, `phlo-openmetadata`                                                        |
| **Query**         | `phlo-trino`                                                                              |
| **Metadata**      | `phlo-postgres`                                                                           |
| **Observability** | `phlo-otel`, `phlo-clickstack`, `phlo-grafana`, `phlo-prometheus`, `phlo-loki`, `phlo-alloy` |
| **UI**            | `phlo-observatory`, `phlo-pgweb`, `phlo-superset`                                         |
| **API**           | `phlo-api`, `phlo-hasura`, `phlo-postgrest`                                               |
| **Dev/Test**      | `phlo-testing`                                                                            |

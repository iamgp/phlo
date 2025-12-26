<p align="center">
  <img src="docs/assets/phlo.png" alt="Phlo" width="400">
</p>

<p align="center">
  <strong>Modern data lakehouse platform built on Dagster, DLT, Iceberg, Nessie, and dbt.</strong>
</p>

<p align="center">
  <a href="https://github.com/iamgp/phlo/actions/workflows/ci.yml"><img src="https://github.com/iamgp/phlo/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/phlo/"><img src="https://img.shields.io/pypi/v/phlo" alt="PyPI"></a>
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+">
</p>

## Features

- **Decorator-driven development** - Reduce boilerplate by 74% with `@phlo.ingestion` and `@phlo.quality`
- **Write-Audit-Publish pattern** - Git-like branching with automatic quality gates and promotion
- **Type-safe data quality** - Pandera schemas enforce validation and generate Iceberg tables
- **Plugin architecture** - Extensible via service, source, quality, and transformation plugins
- **Observatory UI** - Web-based interface for data exploration, lineage, and monitoring
- **Production-ready patterns** - Auto-publishing to Postgres, configurable merge strategies, freshness policies
- **Modern tooling** - Built on Dagster, DLT, Iceberg, Nessie, dbt, and Trino

## Quick Start

```bash
# Install with default services
uv pip install phlo[defaults]

# Initialize a new project
phlo init my-project
cd my-project

# Start services and run
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
- [CLI Reference](docs/reference/cli-reference.md)
- [Configuration Reference](docs/reference/configuration-reference.md)
- [Operations Guide](docs/operations/operations-guide.md)
- [Blog Series](docs/blog/README.md) - 13-part deep dive

## Development

```bash
# Services
phlo services start    # Start all services
phlo services stop     # Stop services
phlo services logs -f  # View logs

# Development
uv pip install -e .    # Install Phlo
ruff check src/        # Lint
ruff format src/       # Format
basedpyright src/      # Type check
phlo test              # Run tests
```

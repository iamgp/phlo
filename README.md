<p align="center">
  <img src="docs/assets/phlo.png" alt="Phlo" width="400">
</p>

<p align="center">
  <strong>Modern data lakehouse platform built on Dagster, DLT, Iceberg, Nessie, and dbt.</strong>
</p>

<p align="center">
  <a href="https://github.com/iamgp/phlo/actions/workflows/ci.yml"><img src="https://github.com/iamgp/phlo/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/phlo/"><img src="https://img.shields.io/pypi/v/phlo" alt="PyPI"></a>
  <a href="https://pypi.org/project/phlo/"><img src="https://img.shields.io/pypi/pyversions/phlo" alt="Python"></a>
</p>

## Features

- **Write-Audit-Publish pattern** - Branch isolation with automatic promotion
- **@phlo_ingestion decorator** - 74% less boilerplate for data ingestion
- **Configurable merge strategies** - Append-only or upsert with deduplication (first/last/hash)
- **@phlo_quality decorator** - Declarative quality checks
- **Auto-publishing** - Marts automatically published to Postgres for BI
- **CLI tools** - `phlo services`, `phlo materialize`, `phlo create-workflow`
- **Infrastructure config** - Multi-project support with phlo.yaml

## Quick Start

```bash
# Install with uv
uv add phlo

# Or with pip
pip install phlo

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

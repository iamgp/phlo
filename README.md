# Phlo

Modern data lakehouse platform built on Dagster, DLT, Iceberg, Nessie, and dbt.

## Features

- **Write-Audit-Publish pattern** - Branch isolation with automatic promotion
- **@phlo.ingestion decorator** - 74% less boilerplate for data ingestion
- **@phlo.quality decorator** - Declarative quality checks
- **Auto-publishing** - Marts automatically published to Postgres for BI
- **CLI tools** - `phlo services`, `phlo materialize`, `phlo create-workflow`

## Quick Start

```bash
# Clone and start services
git clone https://github.com/iamgp/phlo.git
cd phlo
cp .env.example .env
phlo services start

# Materialize the example pipeline
phlo materialize --select "dlt_glucose_entries+"
```

## Documentation

Full documentation at [docs/index.md](docs/index.md):

- [Quickstart Guide](docs/getting-started/quickstart.md)
- [CLI Reference](docs/guides/cli.md)
- [Architecture](docs/reference/architecture.md)
- [Blog Series](docs/blog/README.md) - 12-part deep dive

## Development

```bash
make up          # Start services
make down        # Stop services
make rebuild     # Rebuild Dagster container

ruff check src/  # Lint
ruff format src/ # Format
```

# Agents Configuration for Phlo

Guidelines for AI agents and developers working on the Phlo monorepo.

## Development Principles

- Early stage: no backward compatibility guarantees.
- Keep code clean and organized; aim for zero technical debt.
- Implement features properly to scale beyond 1,000 users.
- Avoid compatibility shims, workarounds, and placeholders.
- Prefer explicit, testable behavior; update docs for user-visible changes.

## Repository Layout (Monorepo)

- `src/phlo/` - Core CLI/runtime (config, discovery, hooks, services, logging).
- `packages/` - Workspace packages (phlo-dlt, phlo-dbt, phlo-dagster, phlo-quality, phlo-observatory, etc.).
- `tests/` - Repo-level tests; package tests live in `packages/*/tests`.
- `registry/` - Plugin registry schema + published metadata.
- `templates/` - Project scaffolding templates.
- `docs/` - Documentation site content.
- `scripts/` - Developer automation helpers.

## Tooling & Commands

### Setup

```bash
uv pip install -e .
```

### All Checks

```bash
make check
```

### Python Quality

```bash
uv run ruff check .
uv run ruff format .
uv run ty check
```

### Tests

```bash
uv run pytest
```

### Services

```bash
phlo services start
phlo services stop
phlo services logs -f dagster-webserver
```

### dbt (when services are running)

```bash
docker exec dagster-webserver dbt run --select model_name
docker exec dagster-webserver dbt test --select tag:dataset_name
docker exec dagster-webserver dbt compile
```

## Architecture Snapshot

- Orchestration: Dagster assets + sensors.
- Ingestion: DLT + `@phlo_ingestion` decorator (phlo-dlt).
- Quality: `@phlo_quality` + Pandera schemas (phlo-quality).
- Transformations: dbt for SQL models and medallion layers.
- Storage: Iceberg tables on S3-compatible storage (MinIO) with Nessie catalog.
- Query: Trino.
- Metadata: Postgres (operational metadata and marts).
- UI/Observability: phlo-observatory plus metrics/alerting packages.

## Conventions

- Python 3.11+, line length 100.
- Type checking: ty.
- Lint/format: ruff.
- Absolute imports only.
- Commits follow Conventional Commits.
- Configuration via `phlo.config.settings` (reads `.phlo/.env` and `.phlo/.env.local`).
- Project templates use:
  - `workflows/` for ingestion/quality assets and `transforms/dbt/` for dbt projects.
  - Pandera schemas in `workflows/schemas/{domain}.py`.
  - Asset names in snake_case; ingestion assets use `dlt_<table_name>`.
  - Database objects in lowercase.

# Agents Configuration for LakehouseKit

## Build/Lint/Test Commands
- **Development setup**: `cd dagster && uv pip install -e .` (Python dependencies)
- **Type checking**: `basedpyright lakehousekit/` (from dagster/ dir)
- **Linting**: `ruff check lakehousekit/` and `ruff format lakehousekit/` (from dagster/ dir)
- **Services**: `make up` (start all), `make down` (stop), `make rebuild` (rebuild Dagster)
- **Asset validation**: `dagster dev --workspace dagster/workspace.yaml`
- **Single asset test**: `dagster asset materialize --select entries` (Nightscout data)
- **dbt commands**: `docker compose exec dagster-web dbt run/test --select model_name`

## Architecture & Structure
- **Data lakehouse** with MinIO (S3-compatible), PostgreSQL, DuckDB/DuckLake for analytics
- **Core orchestrator**: Dagster with assets in `lakehousekit/defs/` (ingestion, transform, publishing, quality, metadata)
- **Transform layer**: dbt models with 4-layer architecture (bronze → silver → gold → marts)
- **Databases**: PostgreSQL for catalog/metadata, DuckDB for analytical queries and DuckLake managed tables
- **Storage**: MinIO bucket `lake` with prefix `ducklake/` for managed tables
- **Services**: Superset (dashboards), DataHub (metadata catalog)
- **Configuration**: Centralized in `lakehousekit/config.py` using Pydantic settings from `.env`

## Code Style & Conventions
- **Python 3.11+**, line length 100, ruff + basedpyright for linting/typing
- **Imports**: Use absolute imports, organize with ruff (E, F, I, N, UP, B, A, C4, SIM rules)
- **Asset definitions**: Modular approach in `defs/` subdirectories, auto-discovered by Dagster
- **Configuration**: Use `lakehousekit.config.config` singleton, environment variables from `.env`
- **Error handling**: Use Pydantic validation, tenacity for retries, structured logging
- **Naming**: snake_case for Python, lowercase for databases/schemas, descriptive asset names
- **Dependencies**: Managed with `uv`, pinned versions in `pyproject.toml`, Docker for services

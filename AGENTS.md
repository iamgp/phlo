# Agents Configuration for Phlo

## Build/Lint/Test Commands

- **Development setup**: `cd dagster && uv pip install -e .` (Python dependencies)
- **Type checking**: `basedpyright phlo/` (from services/dagster/ dir)
- **Linting**: `ruff check phlo/` and `ruff format phlo/` (from services/dagster/ dir)
- **Services**: `make up` (start all), `make down` (stop), `make rebuild` (rebuild Dagster)
- **Asset validation**: `dagster dev --workspace dagster/workspace.yaml`
- **Single asset test**: `dagster asset materialize --select entries` (Nightscout data)
- **dbt commands**: `docker compose exec dagster-web dbt run/test --select model_name`
- **dbt testing**: `dbt test --select tag:dataset_name` (comprehensive schema + business logic tests)

## CLI Commands

### Asset Materialization & Backfills

- **Single materialization**: `phlo materialize asset_name --partition 2024-01-01`
- **Date range backfill**: `phlo backfill glucose_entries --start-date 2024-01-01 --end-date 2024-01-31`
- **Explicit partitions**: `phlo backfill glucose_entries --partitions 2024-01-01,2024-01-15,2024-01-31`
- **Parallel backfill**: `phlo backfill glucose_entries --start-date 2024-01-01 --end-date 2024-12-31 --parallel 4`
- **Resume backfill**: `phlo backfill --resume` (continues after interruption)
- **Dry-run preview**: `phlo backfill glucose_entries --start-date 2024-01-01 --end-date 2024-01-31 --dry-run`

### Log Access & Filtering

- **View recent logs**: `phlo logs` (last 100 logs)
- **Filter by asset**: `phlo logs --asset glucose_entries`
- **Filter by job**: `phlo logs --job weather_pipeline`
- **Filter by level**: `phlo logs --level ERROR` (DEBUG, INFO, WARNING, ERROR)
- **Time-based filter**: `phlo logs --since 1h` (last hour, supports h/m/d)
- **Tail mode**: `phlo logs --follow` (real-time updates)
- **Specific run**: `phlo logs --run-id abc123`
- **Full output**: `phlo logs --full` (no truncation)
- **JSON output**: `phlo logs --json` (for scripting)

## Architecture & Structure

- **Data lakehouse** with MinIO (S3-compatible), PostgreSQL, DuckDB/DuckLake for analytics
- **Core orchestrator**: Dagster with assets in `phlo/defs/` (ingestion, transform, publishing, quality, metadata)
- **Transform layer**: dbt models with 4-layer architecture (bronze → silver → gold → marts)
- **Databases**: PostgreSQL for catalog/metadata, DuckDB for analytical queries and DuckLake managed tables
- **Storage**: MinIO bucket `lake` with prefix `ducklake/` for managed tables
- **Services**: Superset (dashboards), DataHub (metadata catalog)
- **Configuration**: Centralized in `phlo/config.py` using Pydantic settings from `.env`

## Testing Strategy

### Data Quality Testing

- **Pandera schemas**: Type-safe validation in `phlo/schemas/` with Dagster integration
- **Dagster asset checks**: Runtime quality validation with detailed error reporting
- **dbt tests**: Comprehensive testing across bronze/silver/gold/mart layers

### dbt Test Patterns

- **Schema tests**: YAML-based column validation (not_null, unique, accepted_values, relationships)
- **Business logic tests**: Custom SQL tests for complex rules and cross-table validation
- **Data integrity tests**: Referential integrity, range validation, statistical checks
- **Incremental logic tests**: Proper handling of incremental updates and deduplication

### Test Organization

- **Bronze layer**: Basic schema validation and data type checks
- **Silver layer**: Business logic validation and enrichment accuracy
- **Gold layer**: Curated data integrity and incremental processing
- **Mart layer**: Dashboard-ready data validation and aggregation accuracy

### Required dbt Packages

```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: 1.1.1
  - package: calogica/dbt_expectations
    version: 0.10.0
  - package: dbt-labs/dbt_date
    version: 0.10.0
```

## Code Style & Conventions

- **Python 3.11+**, line length 100, ruff + basedpyright for linting/typing
- **Imports**: Use absolute imports, organize with ruff (E, F, I, N, UP, B, A, C4, SIM rules)
- **Asset definitions**: Modular approach in `defs/` subdirectories, auto-discovered by Dagster
- **Configuration**: Use `phlo.config.config` singleton, environment variables from `.env`
- **Error handling**: Use Pydantic validation, tenacity for retries, structured logging
- **Naming**: snake_case for Python, lowercase for databases/schemas, descriptive asset names
- **Dependencies**: Managed with `uv`, pinned versions in `pyproject.toml`, Docker for services

To materialise assets, run the following command:

```
docker exec dagster-web dagster asset materialize --select
      "dlt_glucose_entries,stg_glucose_entries,fct_glucose_readings,mrt_glucose_readings,fct_daily_glucose_metrics,mrt_glucose_hourly_patterns" --partition "2025-11-04" -m phlo.definitions
```

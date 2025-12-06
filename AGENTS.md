# Agents Configuration for Phlo

Guidelines for AI agents and developers working on the Phlo codebase.

## Development Philosophy

- Early development: no users, no backward compatibility concerns
- Keep code clean and organized; aim for zero technical debt
- Do not create compatibility shims or workarounds
- Implement features properly to scale beyond 1,000 users
- Do not present half-baked solutions
- Do not add placeholders

## Build/Lint/Test Commands

### Development Setup

```bash
# Install dependencies
uv pip install -e .

# Type checking
basedpyright src/phlo/

# Linting and formatting
ruff check src/phlo/
ruff format src/phlo/
```

### Service Management

```bash
# Start all services
phlo services start

# Stop services
phlo services stop

# View logs
phlo services logs -f dagster-webserver
```

### Testing

```bash
# Run all tests
phlo test

# Run specific tests
phlo test tests/test_ingestion.py

# Unit tests only
phlo test -m unit

# Skip integration tests (no Docker required)
phlo test --local
```

### Asset Operations

```bash
# Materialize asset
phlo materialize dlt_glucose_entries

# Materialize with partition
phlo materialize dlt_glucose_entries --partition 2024-01-01

# Materialize with downstream
phlo materialize dlt_glucose_entries+
```

### dbt Operations

```bash
# Run dbt models
docker exec phlo-dagster-webserver-1 dbt run --select model_name

# Test dbt models
docker exec phlo-dagster-webserver-1 dbt test --select tag:dataset_name

# Compile dbt (required after model changes)
docker exec phlo-dagster-webserver-1 dbt compile
```

## Architecture & Structure

### Core Components

- **Orchestration**: Dagster with assets in `src/phlo/defs/`
  - `ingestion/` - DLT-based data ingestion with `@phlo.ingestion` decorator
  - `transform/` - dbt integration for SQL transformations
  - `publishing/` - Publishing marts to PostgreSQL for BI
  - `quality/` - Data quality checks with `@phlo.quality` decorator
  - `sensors/` - Branch lifecycle automation (creation, promotion, cleanup)

- **Storage**: MinIO (S3-compatible) + Nessie (Git-like catalog) + Iceberg (table format)
- **Query Engine**: Trino for distributed SQL queries
- **Transform Layer**: dbt with bronze → silver → gold → marts architecture
- **Metadata**: PostgreSQL for operational metadata
- **Configuration**: `src/phlo/config.py` using Pydantic settings from `.env`

### Key Files & Directories

```
src/phlo/
├── cli/                 # CLI commands (services, materialize, test, etc.)
├── config.py            # Centralized configuration (Pydantic settings)
├── defs/                # Dagster asset definitions
│   ├── ingestion/       # Data ingestion assets
│   ├── transform/       # dbt integration
│   ├── publishing/      # Publishing to PostgreSQL
│   ├── quality/         # Quality check assets
│   └── sensors/         # Branch lifecycle sensors
├── ingestion/           # Ingestion framework (@phlo.ingestion)
│   ├── decorator.py     # Main decorator implementation
│   └── dlt_helpers.py   # DLT and Iceberg integration
├── quality/             # Quality framework (@phlo.quality)
│   ├── decorator.py     # Quality decorator implementation
│   └── checks.py        # Built-in quality checks
├── schemas/             # Pandera validation schemas
│   └── converter.py     # Pandera → Iceberg type mapping
└── framework/           # Framework discovery and loading

transforms/dbt/          # dbt project
├── models/
│   ├── bronze/          # Staging models
│   ├── silver/          # Cleaned/conformed data
│   ├── gold/            # Aggregated metrics
│   └── marts/           # BI-ready tables
└── tests/               # dbt data tests
```

## Code Style & Conventions

### Python Standards

- **Version**: Python 3.11+
- **Line length**: 100 characters
- **Type checking**: basedpyright with strict mode
- **Linting**: ruff (E, F, I, N, UP, B, A, C4, SIM rules)
- **Formatting**: ruff format
- **Imports**: Absolute imports only, sorted with ruff

### Naming Conventions

- **Python code**: snake_case for functions, classes, variables
- **Database objects**: lowercase for schemas, tables, columns
- **Asset names**: Descriptive, prefixed by type (e.g., `dlt_glucose_entries`, `publish_daily_aggregates`)
- **Decorator-generated assets**: Follow `dlt_{table_name}` convention

### Code Organization

- **One asset per file** in appropriate subdirectory
- **Pandera schemas** in `src/phlo/schemas/{domain}.py`
- **Configuration** via environment variables, accessed through `phlo.config.settings`
- **Error handling**: Use Pydantic validation, structured logging
- **No backwards compatibility shims** - clean implementation only

### Dependencies

- **Package manager**: uv (fast Python package installer)
- **Dependencies**: Pinned in `pyproject.toml`
- **Services**: Docker Compose for infrastructure

## Testing Strategy

### Unit Tests

```bash
# Fast unit tests only
phlo test -m unit

# Specific module
phlo test tests/test_schemas.py
```

### Integration Tests

```bash
# Full integration tests (requires Docker)
phlo test

# Skip integration tests
phlo test --local
```

### Data Quality Testing

- **Pandera schemas**: Type-safe validation in `src/phlo/schemas/`
- **Dagster asset checks**: Generated by `@phlo.quality` decorator
- **dbt tests**: Schema and data tests in `transforms/dbt/tests/`

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

## Common Development Tasks

### Adding a New Ingestion Workflow

1. Define Pandera schema in `src/phlo/schemas/{domain}.py`
2. Create ingestion asset in `src/phlo/defs/ingestion/{domain}/{workflow}.py`
3. Use `@phlo.ingestion` decorator with schema and DLT source
4. Register in `src/phlo/defs/ingestion/__init__.py`
5. Test with `phlo materialize {asset_name}`

### Adding a dbt Model

1. Create SQL file in `transforms/dbt/models/{layer}/`
2. Add schema YAML with tests
3. Compile: `docker exec phlo-dagster-webserver-1 dbt compile`
4. Test: `docker exec phlo-dagster-webserver-1 dbt test --select {model_name}`
5. Materialize via Dagster UI or CLI

### Adding Quality Checks

1. Create quality asset in `src/phlo/defs/quality/{domain}.py`
2. Use `@phlo.quality` decorator with check types
3. Checks automatically become Dagster asset checks
4. View results in Dagster UI

## Documentation

User-facing documentation is in `docs/`:

- See `docs/guides/developer-guide.md` for decorator usage
- See `docs/reference/cli-reference.md` for CLI commands
- See `docs/getting-started/core-concepts.md` for architecture overview

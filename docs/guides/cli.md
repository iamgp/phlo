# Phlo CLI Guide

Command-line interface for Phlo workflows.

## Installation

The Phlo CLI is automatically available after installing Phlo:

```bash
# Install Phlo
pip install -e .

# Verify installation
phlo --version
```

---

## Commands Overview

| Command | Description | Speed |
|---------|-------------|-------|
| `phlo test` | Run tests with optional local mode | Fast (< 5s local) |
| `phlo materialize` | Materialize assets via Docker | Medium (30-60s) |
| `phlo backfill` | Backfill partitioned assets | Medium |
| `phlo logs` | View and filter pipeline logs | Fast |
| `phlo create-workflow` | Interactive workflow scaffolding | Fast (< 10s) |
| `phlo schema` | Manage Pandera schemas | Fast |
| `phlo catalog` | Interact with Iceberg catalog | Fast |
| `phlo branch` | Manage Nessie branches | Fast |
| `phlo metrics` | View pipeline and data metrics | Fast |
| `phlo lineage` | View asset dependencies | Fast |
| `phlo plugin` | Manage Phlo plugins | Fast |
| `phlo contract` | Manage data contracts | Fast |
| `phlo api` | API layer management | Fast |

---

## phlo test

Run tests for Phlo workflows.

### Usage

```bash
phlo test [ASSET_NAME] [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `ASSET_NAME` | (Optional) Run tests for specific asset |
| `--local` | Run tests locally without Docker |
| `--coverage` | Generate coverage report |
| `-v, --verbose` | Verbose output |
| `-m, --marker MARKER` | Run tests with specific pytest marker |

### Examples

**Run all tests**:
```bash
phlo test
```

**Run tests for specific asset**:
```bash
phlo test weather_observations
```

**Run unit tests only (skip Docker integration tests)**:
```bash
phlo test --local
```

**Generate coverage report**:
```bash
phlo test --coverage
# Opens htmlcov/index.html
```

**Run integration tests only**:
```bash
phlo test -m integration
```

**Verbose output**:
```bash
phlo test -v
```

### Performance

| Mode | Docker Required | Speed | Best For |
|------|----------------|-------|----------|
| `phlo test --local` | ❌ No | < 5s | Unit tests, CI/CD |
| `phlo test` | ✅ Yes | 30-60s | Integration tests |

### Test Markers

Mark your tests with pytest markers:

```python
import pytest

# Unit test (runs with --local)
def test_schema():
    pass

# Integration test (skipped with --local)
@pytest.mark.integration
def test_full_pipeline():
    pass
```

---

## phlo materialize

Materialize Dagster assets via Docker.

### Usage

```bash
phlo materialize ASSET_NAME [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `ASSET_NAME` | Asset to materialize |
| `-p, --partition DATE` | Partition date (YYYY-MM-DD) |
| `--select SELECTOR` | Asset selector expression |
| `--dry-run` | Show command without executing |

### Examples

**Materialize asset**:
```bash
phlo materialize weather_observations
```

**Materialize with partition**:
```bash
phlo materialize weather_observations --partition 2024-01-15
```

**Use Dagster selector**:
```bash
phlo materialize --select "tag:weather"
phlo materialize --select "*weather*"
```

**Dry run (show command without executing)**:
```bash
phlo materialize weather_observations --dry-run
# Output: docker exec dagster-webserver dagster asset materialize --select weather_observations
```

### Requirements

- Docker services must be running
- `dagster-webserver` container must be up

```bash
# Start services
make up-core up-query

# Verify services
docker ps | grep dagster-webserver
```

### Behind the Scenes

`phlo materialize` is a convenience wrapper for:

```bash
docker exec dagster-webserver dagster asset materialize --select <asset>
```

---

## phlo create-workflow

Interactive workflow scaffolding.

### Usage

```bash
phlo create-workflow [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--type TYPE` | Workflow type (ingestion, transform, quality) | Prompt |
| `--domain DOMAIN` | Domain name (e.g., weather, stripe) | Prompt |
| `--table TABLE` | Table name | Prompt |
| `--unique-key KEY` | Unique key field for deduplication | Prompt |
| `--cron CRON` | Cron schedule expression | `"0 */1 * * *"` |
| `--api-base-url URL` | REST API base URL | Prompt |

### Examples

**Interactive mode** (recommended for first-time users):
```bash
phlo create-workflow

# Prompts:
# Workflow type: ingestion
# Domain name: weather
# Table name: observations
# Unique key field: id
# Cron schedule: 0 */1 * * *
# API base URL: https://api.openweathermap.org/data/3.0
```

**Command-line mode** (for automation):
```bash
phlo create-workflow \
  --type ingestion \
  --domain weather \
  --table observations \
  --unique-key id \
  --cron "0 */1 * * *" \
  --api-base-url "https://api.example.com/v1"
```

### What It Creates

The command generates 3 files:

1. **Pandera schema** (`src/phlo/schemas/{domain}.py`)
2. **Ingestion asset** (`src/phlo/defs/ingestion/{domain}/{table}.py`)
3. **Test file** (`tests/test_{domain}_{table}.py`)

And auto-registers the domain in `src/phlo/defs/ingestion/__init__.py`.

### Example Output

```bash
🚀 Creating ingestion workflow for weather.observations...

✅ Created files:

  ✓ src/phlo/schemas/weather.py
  ✓ src/phlo/defs/ingestion/weather/observations.py
  ✓ tests/test_weather_observations.py

📝 Next steps:
  1. Edit schema: src/phlo/schemas/weather.py
  2. Configure API: src/phlo/defs/ingestion/weather/observations.py
  3. Restart Dagster: docker restart dagster-webserver
  4. Test: phlo test weather
  5. Materialize: phlo materialize observations
```

### File Templates

Generated files include:
- ✅ Complete TODOs for customization
- ✅ Inline documentation
- ✅ Best practices examples
- ✅ Common API patterns (authentication, pagination, etc.)

### After Creation

1. **Edit schema** - Add your fields to the Pandera schema
2. **Configure API** - Update the DLT rest_api configuration
3. **Restart Dagster** - `docker restart dagster-webserver`
4. **Test locally** - `phlo test {domain} --local`
5. **Materialize** - `phlo materialize {table}`

---

## phlo api

API infrastructure management commands.

### phlo api setup-postgrest

Set up PostgREST authentication infrastructure in PostgreSQL.

#### Usage

```bash
phlo api setup-postgrest [OPTIONS]
```

#### What It Does

Sets up the core PostgREST authentication infrastructure:
- PostgreSQL extensions (pgcrypto for password hashing)
- Auth schema with users table
- JWT signing and verification functions
- Database roles (authenticator, anon, authenticated, analyst, admin)
- Row-Level Security (RLS) setup

**Note:** This only sets up authentication infrastructure. You create your own API views based on your data.

#### Options

| Option | Description |
|--------|-------------|
| `--host TEXT` | PostgreSQL host (default: from `POSTGRES_HOST` env var or 'localhost') |
| `--port INTEGER` | PostgreSQL port (default: from `POSTGRES_PORT` env var or 5432) |
| `--database TEXT` | PostgreSQL database name (default: from `POSTGRES_DB` env var or 'lakehouse') |
| `--user TEXT` | PostgreSQL user (default: from `POSTGRES_USER` env var or 'lake') |
| `--password TEXT` | PostgreSQL password (default: from `POSTGRES_PASSWORD` env var) |
| `--force` | Force re-setup even if already exists |
| `-q, --quiet` | Suppress output |

#### Examples

**Basic setup** (uses environment variables):
```bash
phlo api setup-postgrest
```

**Specify connection details**:
```bash
phlo api setup-postgrest --host localhost --port 10000 --database lakehouse
```

**Force re-setup**:
```bash
phlo api setup-postgrest --force
```

**Quiet mode**:
```bash
phlo api setup-postgrest -q
```

#### What Gets Created

**Schemas:**
- `auth` - Private schema for user authentication (not exposed via API)

**Tables:**
- `auth.users` - User accounts with bcrypt-hashed passwords

**Functions:**
- `auth.sign_jwt()` - Sign JWT tokens with HS256
- `auth.verify_jwt()` - Verify and decode JWT tokens
- `api.login()` - Authenticate users and return JWT tokens

**Roles:**
- `authenticator` - PostgREST connection role (can switch to other roles)
- `anon` - Unauthenticated users
- `authenticated` - Base role for authenticated users
- `analyst` - Analyst role with read access
- `admin` - Administrator role with full access

**Default Users:**
| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | admin |
| `analyst` | `analyst123` | analyst |

⚠️ **Important:** Change these passwords in production!

#### After Setup

1. **Create your API views** (your responsibility):
```sql
-- In your SQL files or dbt models
CREATE VIEW api.my_data AS
SELECT * FROM marts.my_mart;
```

2. **Start PostgREST**:
```bash
docker-compose --profile api up -d postgrest
```

3. **Test authentication**:
```bash
curl -X POST http://localhost:10018/rpc/login \
  -H "Content-Type: application/json" \
  -d '{"username": "analyst", "password": "analyst123"}'
```

#### Idempotent Operation

This command is safe to run multiple times:
- Checks if setup already exists
- Skips if already complete (unless `--force` is used)
- Creates only missing components

#### From Python

```python
from phlo.api.postgrest import setup_postgrest

# Use environment variables
setup_postgrest()

# Or specify connection details
setup_postgrest(
    host="localhost",
    port=10000,
    database="lakehouse",
    user="lake",
    password="lakepass"
)
```

#### Requirements

- PostgreSQL 12+ with superuser access
- `psycopg2-binary` Python package (install with: `pip install psycopg2-binary`)

#### See Also

- [PostgREST Deployment Guide](../setup/postgrest.md)
- [PostgREST Migration PRD](./prd-postgrest-migration.md)
- [PostgREST Examples](../migrations/postgrest/examples/)

### phlo api generate-views

Auto-generate PostgREST API views from dbt models.

#### Usage

```bash
phlo api generate-views [OPTIONS]
```

#### Options

| Option | Description |
|--------|-------------|
| `--output FILE` | Write SQL to file |
| `--apply` | Apply directly to database |
| `--diff` | Show changes only |
| `--models PATTERN` | Filter models (e.g., `mrt_*`) |

#### Examples

```bash
# Print generated SQL
phlo api generate-views

# Write to file
phlo api generate-views --output views.sql

# Apply directly
phlo api generate-views --apply

# Filter to mart models only
phlo api generate-views --models "mrt_*"
```

### phlo api hasura

Manage Hasura GraphQL configuration.

#### Usage

```bash
phlo api hasura <subcommand> [OPTIONS]
```

#### Subcommands

| Command | Description |
|---------|-------------|
| `track` | Auto-track tables in Hasura |
| `permissions sync` | Sync permissions from config |
| `export` | Export Hasura metadata |
| `apply` | Apply metadata file |
| `status` | Show tracking status |

#### Examples

```bash
# Track all untracked tables
phlo api hasura track

# Track specific schema
phlo api hasura track --schema api

# Sync permissions from config
phlo api hasura permissions sync

# Export/import metadata
phlo api hasura export --output hasura.yaml
phlo api hasura apply --input hasura.yaml
```

---

## phlo backfill

Backfill partitioned assets with date ranges.

### Usage

```bash
phlo backfill ASSET_NAME [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--start-date DATE` | Start date (YYYY-MM-DD) |
| `--end-date DATE` | End date (YYYY-MM-DD) |
| `--partitions LIST` | Explicit partition list (comma-separated) |
| `--parallel N` | Run N partitions in parallel |
| `--resume` | Resume interrupted backfill |
| `--dry-run` | Preview without executing |

### Examples

```bash
# Backfill date range
phlo backfill glucose_entries --start-date 2024-01-01 --end-date 2024-01-31

# Explicit partitions
phlo backfill glucose_entries --partitions 2024-01-01,2024-01-15,2024-01-31

# Parallel execution
phlo backfill glucose_entries --start-date 2024-01-01 --end-date 2024-12-31 --parallel 4

# Resume after interruption
phlo backfill --resume

# Dry-run preview
phlo backfill glucose_entries --start-date 2024-01-01 --end-date 2024-01-31 --dry-run
```

---

## phlo logs

View and filter pipeline logs.

### Usage

```bash
phlo logs [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--asset NAME` | Filter by asset name |
| `--job NAME` | Filter by job name |
| `--level LEVEL` | Filter by log level (DEBUG, INFO, WARNING, ERROR) |
| `--since DURATION` | Time filter (e.g., `1h`, `30m`, `7d`) |
| `--follow` | Tail logs in real-time |
| `--run-id ID` | Filter by specific run |
| `--full` | Show full output (no truncation) |
| `--json` | Output as JSON |

### Examples

```bash
# View recent logs
phlo logs

# Filter by asset
phlo logs --asset glucose_entries

# Filter by level and time
phlo logs --level ERROR --since 1h

# Real-time tail
phlo logs --follow

# JSON output for scripting
phlo logs --json | jq '.[] | select(.level == "ERROR")'
```

---

## phlo schema

Manage and inspect Pandera schemas.

### Usage

```bash
phlo schema <subcommand> [OPTIONS]
```

### Subcommands

| Command | Description |
|---------|-------------|
| `list` | List all schemas |
| `show` | Show schema details |
| `diff` | Compare schema versions |
| `validate` | Validate schema file |

### Examples

```bash
# List all schemas
phlo schema list
phlo schema list --domain nightscout

# Show schema details
phlo schema show RawGlucoseEntries
phlo schema show RawGlucoseEntries --iceberg  # Show Iceberg equivalent

# Compare versions
phlo schema diff RawGlucoseEntries --old HEAD~1
phlo schema diff schemas/v1.py schemas/v2.py

# Validate schema
phlo schema validate src/phlo/schemas/glucose.py
```

---

## phlo catalog

Interact with the Iceberg catalog via Nessie.

### Usage

```bash
phlo catalog <subcommand> [OPTIONS]
```

### Subcommands

| Command | Description |
|---------|-------------|
| `tables` | List all tables |
| `describe` | Show table metadata |
| `history` | Show snapshot history |
| `sync` | Sync to OpenMetadata |

### Examples

```bash
# List tables
phlo catalog tables
phlo catalog tables --namespace raw

# Describe table
phlo catalog describe raw.glucose_entries

# Show history
phlo catalog history raw.glucose_entries
phlo catalog history raw.glucose_entries --limit 50

# Sync to OpenMetadata
phlo catalog sync
phlo catalog sync --tables           # Tables only
phlo catalog sync --models           # dbt models only
phlo catalog sync --dry-run          # Preview changes
```

---

## phlo branch

Manage Nessie branches for data versioning.

### Usage

```bash
phlo branch <subcommand> [OPTIONS]
```

### Subcommands

| Command | Description |
|---------|-------------|
| `list` | List all branches |
| `create` | Create new branch |
| `delete` | Delete branch |
| `merge` | Merge branches |
| `diff` | Show differences |

### Examples

```bash
# List branches
phlo branch list
phlo branch list --all  # Include tags

# Create branch
phlo branch create feature/new-model
phlo branch create feature/experiment --from dev

# Delete branch
phlo branch delete feature/old-branch
phlo branch delete feature/old-branch --force

# Merge
phlo branch merge feature/new-model main
phlo branch merge feature/new-model main --dry-run

# Compare branches
phlo branch diff main feature/new-model
```

---

## phlo metrics

View pipeline and data metrics.

### Usage

```bash
phlo metrics [subcommand] [OPTIONS]
```

### Subcommands

| Command | Description |
|---------|-------------|
| `summary` | Show metrics overview |
| `asset` | Per-asset metrics |
| `export` | Export metrics |

### Examples

```bash
# Summary dashboard
phlo metrics
phlo metrics summary --period 7d

# Per-asset metrics
phlo metrics asset glucose_entries
phlo metrics asset glucose_entries --runs 20

# Export metrics
phlo metrics export --format csv --output metrics.csv
phlo metrics export --format json --period 30d
```

---

## phlo lineage

View asset dependencies and impact analysis.

### Usage

```bash
phlo lineage <subcommand> [OPTIONS]
```

### Subcommands

| Command | Description |
|---------|-------------|
| `show` | Display dependency tree |
| `export` | Export lineage graph |
| `impact` | Show downstream impact |

### Examples

```bash
# Show dependencies
phlo lineage show glucose_entries
phlo lineage show glucose_entries --upstream
phlo lineage show glucose_entries --downstream
phlo lineage show glucose_entries --depth 2

# Export
phlo lineage export --format dot --output lineage.dot
phlo lineage export --format mermaid --output lineage.md

# Impact analysis
phlo lineage impact glucose_entries
```

### Example Output

```
glucose_entries
├── [upstream]
│   └── (external) Nightscout API
└── [downstream]
    ├── stg_glucose_entries (dbt)
    │   ├── fct_glucose_readings (dbt)
    │   │   ├── mrt_glucose_readings (dbt)
    │   │   └── fct_daily_glucose_metrics (dbt)
```

---

## phlo plugin

Manage Phlo plugins.

### Usage

```bash
phlo plugin <subcommand> [OPTIONS]
```

### Subcommands

| Command | Description |
|---------|-------------|
| `list` | List installed plugins |
| `info` | Show plugin details |
| `check` | Validate plugins |
| `create` | Scaffold new plugin |

### Examples

```bash
# List plugins
phlo plugin list
phlo plugin list --type sources

# Plugin info
phlo plugin info jsonplaceholder

# Validate plugins
phlo plugin check

# Create new plugin
phlo plugin create my-custom-source --type source
```

### Example Output

```
Installed Plugins

Sources:
  NAME          VERSION  SOURCE
  rest_api      built-in phlo.ingestion
  jsonplaceholder 1.0.0  phlo-plugin-example

Quality Checks:
  NAME          VERSION  SOURCE
  null_check    built-in phlo.quality
  threshold_check 1.0.0  phlo-plugin-example

Transforms:
  NAME          VERSION  SOURCE
  uppercase     1.0.0    phlo-plugin-example
```

---

## phlo contract

Manage data contracts between producers and consumers.

### Usage

```bash
phlo contract <subcommand> [OPTIONS]
```

### Subcommands

| Command | Description |
|---------|-------------|
| `list` | List all contracts |
| `show` | Show contract details |
| `validate` | Validate against live schema |
| `check` | Check changes in PR |

### Examples

```bash
# List contracts
phlo contract list

# Show contract
phlo contract show glucose_readings

# Validate contract
phlo contract validate glucose_readings

# Check PR changes
phlo contract check --pr
```

### Contract Format

Contracts are defined in YAML in the `contracts/` directory:

```yaml
# contracts/glucose_readings.yaml
name: glucose_readings
version: 1.0.0
owner: data-team

schema:
  required_columns:
    - name: reading_id
      type: string
      constraints:
        unique: true
        nullable: false
    - name: sgv
      type: integer
      constraints:
        min: 20
        max: 600

sla:
  freshness_hours: 2
  quality_threshold: 0.99

consumers:
  - name: analytics-team
    usage: BI dashboards
```

---

## Global Options

All commands support:

| Option | Description |
|--------|-------------|
| `--help` | Show help message |
| `--version` | Show version |

### Examples

```bash
# Show help
phlo --help
phlo test --help
phlo materialize --help
phlo create-workflow --help

# Show version
phlo --version
```

---

## Comparison with Manual Approach

| Task | Manual | With CLI | Time Saved |
|------|--------|----------|------------|
| **Create workflow** | 15-20 min | 5-10 min | 50-67% |
| **Run tests** | `pytest tests/` | `phlo test` | Slight |
| **Materialize asset** | `docker exec dagster-webserver dagster asset materialize ...` | `phlo materialize {asset}` | 70% fewer keystrokes |
| **Local testing** | Manual pytest markers | `phlo test --local` | Easier |

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run tests
        run: |
          phlo test --local --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### GitLab CI

```yaml
test:
  image: python:3.11
  script:
    - pip install -e ".[dev]"
    - phlo test --local --coverage
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

---

## Troubleshooting

### "phlo: command not found"

**Solution**:
```bash
# Install in editable mode
pip install -e .

# Or ensure PATH includes Python scripts directory
export PATH="$HOME/.local/bin:$PATH"
```

### "Docker not found or dagster-webserver container not running"

**Solution**:
```bash
# Start Docker services
make up-core up-query

# Verify
docker ps | grep dagster-webserver
```

### "Test file not found"

**Solution**:
```bash
# List available test files
ls tests/test_*.py

# Use exact asset name
phlo test weather_observations  # Looks for tests/test_weather_observations.py
```

### "Files already exist" (create-workflow)

**Solution**:
```bash
# Check existing files
ls src/phlo/schemas/
ls src/phlo/defs/ingestion/

# Delete old files if you want to regenerate
rm src/phlo/schemas/weather.py
rm -r src/phlo/defs/ingestion/weather/
rm tests/test_weather_observations.py
```

---

## Best Practices

### 1. Use `--local` for Fast Iteration

```bash
# Fast feedback loop
phlo test --local

# Only run full integration tests when needed
phlo test -m integration
```

### 2. Use `--dry-run` Before Production Materializations

```bash
# Check command first
phlo materialize critical_asset --dry-run

# Then execute
phlo materialize critical_asset
```

### 3. Create Workflows with CLI

```bash
# Consistent structure
phlo create-workflow

# vs manual (error-prone)
# 1. Create schema file
# 2. Create asset file
# 3. Create test file
# 4. Register domain
# 5. Fix import errors
```

### 4. Add Coverage Checks to CI

```yaml
- name: Run tests with coverage
  run: phlo test --coverage

- name: Check coverage threshold
  run: |
    coverage report --fail-under=80
```

---

## Advanced Usage

### Custom Test Organization

```python
# conftest.py
import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running"
    )

# Run fast tests only
# phlo test -m "not slow and not integration"
```

### Selective Asset Materialization

```bash
# Materialize all assets in a group
phlo materialize --select "group:weather"

# Materialize all dependencies
phlo materialize --select "weather_observations+"

# Materialize all dependents
phlo materialize --select "+weather_observations"
```

---

## Next Steps

- **Create your first workflow**: `phlo create-workflow`
- **Test it locally**: `phlo test {domain} --local`
- **Materialize data**: `phlo materialize {table}`
- **Read testing guide**: [TESTING_GUIDE.md](./TESTING_GUIDE.md)

---

## Feedback

Found a bug or have a feature request?
- **GitHub Issues**: https://github.com/iamgp/phlo/issues
- **GitHub Discussions**: https://github.com/iamgp/phlo/discussions

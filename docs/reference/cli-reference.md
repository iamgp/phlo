# CLI Reference

Complete reference for the Phlo command-line interface.

## Installation

```bash
# Using pip
pip install -e .

# Using uv (recommended)
uv pip install -e .
```

Verify:

```bash
phlo --version
```

## Global Options

```bash
phlo --help              # Show help
phlo --version           # Show version
```

## Command Overview

```bash
phlo init                # Initialize new project
phlo services            # Manage infrastructure services
phlo dev                 # Start development server
phlo create-workflow     # Create new workflow
phlo materialize         # Materialize assets
phlo test                # Run tests
phlo status              # Show asset status
phlo branch              # Manage Nessie branches
phlo catalog             # Catalog operations
phlo config              # Configuration management
```

## Services Commands

Manage Docker infrastructure services.

Services are provided by installed service packages (e.g., `phlo-dagster`, `phlo-trino`). Install
core services with:

```bash
uv pip install -e ".[core-services]"
```

Optional services can be added later:

```bash
phlo plugin install phlo-observatory
```

### phlo services init

Initialize infrastructure directory and configuration.

```bash
phlo services init
```

**What it does**:

- Creates `.phlo/` directory
- Generates Docker Compose configurations
- Sets up network and volume definitions

**Options**:

```bash
--force              # Overwrite existing configuration
```

**Example**:

```bash
phlo services init --force
```

### phlo services start

Start all infrastructure services.

```bash
phlo services start [OPTIONS]
```

**Options**:

```bash
--native                 # Run native dev services (phlo-api, Observatory) as subprocesses
--profile PROFILE        # Additional service profiles
--detach, -d             # Run in background
--build                  # Rebuild containers before starting
```

**Profiles**:

- `observability`: Prometheus, Grafana, Loki
- `api`: PostgREST, Hasura
- `catalog`: OpenMetadata

**Examples**:

```bash
# Start core services
phlo services start

# Start with observability
phlo services start --profile observability

# Run Observatory/phlo-api without Docker (useful on ARM Macs)
phlo services start --native

# Develop the phlo framework from a local monorepo (Dagster container installs editable from source)
phlo services init --force --dev --phlo-source /path/to/phlo
phlo services start

# Multiple profiles
phlo services start --profile observability --profile api

# Rebuild and start
phlo services start --build
```

**Services started**:

- PostgreSQL (port 10000)
- MinIO (ports 10001-10002)
- Nessie (port 10003)
- Trino (port 10005)
- Dagster webserver (port 10006)
- Dagster daemon

### phlo services stop

Stop all running services.

```bash
phlo services stop [OPTIONS]
```

**Options**:

```bash
--volumes, -v        # Remove volumes (deletes all data)
--remove-orphans     # Remove containers for services not in compose file
```

**Examples**:

```bash
# Stop services (preserve data)
phlo services stop

# Stop and delete all data
phlo services stop --volumes
```

### phlo services status

Show status of all services.

```bash
phlo services status
```

**Output**:

```
SERVICE              STATUS    PORTS
postgres             running   10000
minio                running   10001-10002
nessie               running   10003
trino                running   10005
dagster-webserver    running   10006
dagster-daemon       running
```

### phlo services logs

View service logs.

```bash
phlo services logs [OPTIONS] [SERVICE]
```

**Options**:

```bash
--follow, -f         # Follow log output
--tail N             # Show last N lines
--timestamps         # Show timestamps
```

**Examples**:

```bash
# All logs
phlo services logs

# Follow specific service
phlo services logs -f dagster-webserver

# Last 100 lines
phlo services logs --tail 100 trino
```

## Project Commands

### phlo init

Initialize a new Phlo project.

```bash
phlo init [PROJECT_NAME] [OPTIONS]
```

**Options**:

```bash
--template TEMPLATE      # Project template (default: basic)
--directory PATH         # Target directory
--no-git                 # Don't initialize git repository
```

**Templates**:

- `basic`: Minimal project structure
- `complete`: Full example with ingestion and transformations

**Example**:

```bash
phlo init my-lakehouse --template complete
cd my-lakehouse
```

**Creates**:

```
my-lakehouse/
├── .env.example
├── workflows/
│   ├── ingestion/
│   └── schemas/
├── transforms/
│   └── dbt/
├── tests/
└── phlo.yaml
```

### phlo dev

Start Dagster development server.

```bash
phlo dev [OPTIONS]
```

**Options**:

```bash
--port PORT          # Port for webserver (default: 10006)
--host HOST          # Host to bind (default: 0.0.0.0)
--workspace PATH     # Path to workspace.yaml
```

**Example**:

```bash
phlo dev --port 3000
```

Opens Dagster UI at http://localhost:10006

## Workflow Commands

### phlo create-workflow

Interactive workflow creation wizard.

```bash
phlo create-workflow [OPTIONS]
```

**Options**:

```bash
--type TYPE          # Workflow type: ingestion, quality, transform
--domain DOMAIN      # Domain/namespace (e.g., api, files)
--table TABLE        # Table name
--unique-key KEY     # Unique key column
--non-interactive    # Non-interactive mode (requires all options)
```

**Interactive prompts**:

1. Workflow type (ingestion/quality/transform)
2. Domain name
3. Table name
4. Unique key column
5. Validation schema (optional)
6. Schedule (cron expression)

**Example (interactive)**:

```bash
phlo create-workflow
```

**Example (non-interactive)**:

```bash
phlo create-workflow \
  --type ingestion \
  --domain github \
  --table events \
  --unique-key id
```

**Creates**:

```
workflows/
├── ingestion/
│   └── github/
│       └── events.py
└── schemas/
    └── github.py
```

## Asset Commands

### phlo materialize

Materialize Dagster assets.

```bash
phlo materialize [ASSET_KEYS...] [OPTIONS]
```

**Options**:

```bash
--select SELECTOR        # Asset selection query
--partition PARTITION    # Specific partition to materialize
--tags TAG=VALUE         # Filter by tags
--all                    # Materialize all assets
```

**Selection Syntax**:

```bash
asset_name               # Single asset
asset_name+              # Asset and downstream
+asset_name              # Asset and upstream
asset_name*              # Asset and all dependencies
tag:group_name           # All assets with tag
*                        # All assets
```

**Examples**:

```bash
# Single asset
phlo materialize dlt_glucose_entries

# Asset and downstream
phlo materialize dlt_glucose_entries+

# Specific partition
phlo materialize dlt_glucose_entries --partition 2025-01-15

# By tag
phlo materialize --select "tag:nightscout"

# Multiple assets
phlo materialize asset1 asset2 asset3

# All assets
phlo materialize --all
```

## Testing Commands

### phlo test

Run tests.

```bash
phlo test [TEST_PATH] [OPTIONS]
```

**Options**:

```bash
--local              # Skip Docker integration tests
--verbose, -v        # Verbose output
--marker, -m MARKER  # Run tests with marker
--keyword, -k EXPR   # Run tests matching keyword
--coverage           # Generate coverage report
```

**Markers**:

- `integration`: Integration tests requiring Docker
- `unit`: Fast unit tests
- `slow`: Slow-running tests

**Examples**:

```bash
# All tests
phlo test

# Specific test file
phlo test tests/test_ingestion.py

# Unit tests only
phlo test -m unit

# Skip integration tests
phlo test --local

# Specific test
phlo test -k test_glucose_ingestion

# With coverage
phlo test --coverage
```

## Branch Commands

Manage Nessie catalog branches.

### phlo branch create

Create a new branch.

```bash
phlo branch create BRANCH_NAME [OPTIONS]
```

**Options**:

```bash
--from REF           # Create from reference (default: main)
--description DESC   # Branch description
```

**Examples**:

```bash
# Create from main
phlo branch create dev

# Create from specific commit
phlo branch create feature --from abc123

# With description
phlo branch create dev --description "Development branch"
```

### phlo branch list

List all branches.

```bash
phlo branch list [OPTIONS]
```

**Options**:

```bash
--pattern PATTERN    # Filter by pattern
--show-hashes        # Show commit hashes
```

**Example**:

```bash
phlo branch list
phlo branch list --pattern "pipeline/*"
```

### phlo branch merge

Merge branches.

```bash
phlo branch merge SOURCE TARGET [OPTIONS]
```

**Options**:

```bash
--strategy STRATEGY  # Merge strategy (default: normal)
--no-ff              # Create merge commit even if fast-forward
```

**Examples**:

```bash
# Merge dev to main
phlo branch merge dev main

# Force merge commit
phlo branch merge dev main --no-ff
```

### phlo branch delete

Delete a branch.

```bash
phlo branch delete BRANCH_NAME [OPTIONS]
```

**Options**:

```bash
--force, -f          # Force delete even if not merged
```

**Examples**:

```bash
phlo branch delete old-feature
phlo branch delete old-feature --force
```

## Catalog Commands

### phlo catalog sync

Sync metadata to OpenMetadata catalog.

```bash
phlo catalog sync [OPTIONS]
```

**Options**:

```bash
--database DB        # Sync specific database
--table TABLE        # Sync specific table
--force              # Force re-sync
```

**Examples**:

```bash
# Sync all
phlo catalog sync

# Sync specific database
phlo catalog sync --database bronze

# Sync specific table
phlo catalog sync --database bronze --table events
```

### phlo lineage show

Display asset lineage.

```bash
phlo lineage show [ASSET] [OPTIONS]
```

**Options**:

```bash
--format FORMAT      # Output format: text, dot, json
--depth N            # Maximum depth to traverse
--upstream           # Show upstream only
--downstream         # Show downstream only
```

**Examples**:

```bash
phlo lineage show dlt_glucose_entries
phlo lineage show --format dot > lineage.dot
phlo lineage show --downstream dlt_glucose_entries
```

## Configuration Commands

### phlo config show

Display current configuration.

```bash
phlo config show [OPTIONS]
```

**Options**:

```bash
--format FORMAT      # Output format: yaml, json, env
--secrets            # Show secrets (masked by default)
```

**Examples**:

```bash
phlo config show
phlo config show --format json
phlo config show --secrets
```

### phlo config validate

Validate configuration files.

```bash
phlo config validate [FILE]
```

**Examples**:

```bash
# Validate .env
phlo config validate .env

# Validate phlo.yaml
phlo config validate phlo.yaml
```

## Utility Commands

### phlo status

Show asset status and freshness.

```bash
phlo status [OPTIONS]
```

**Options**:

```bash
--stale              # Show only stale assets
--failed             # Show only failed assets
--group GROUP        # Filter by group
```

**Example**:

```bash
phlo status
phlo status --stale
phlo status --group nightscout
```

### phlo validate-schema

Validate Pandera schemas.

```bash
phlo validate-schema SCHEMA_PATH [OPTIONS]
```

**Options**:

```bash
--data DATA_PATH     # Validate against sample data
```

**Example**:

```bash
phlo validate-schema src/phlo/schemas/events.py
phlo validate-schema src/phlo/schemas/events.py --data sample.parquet
```

### phlo validate-workflow

Validate workflow configuration.

```bash
phlo validate-workflow WORKFLOW_PATH
```

**Example**:

```bash
phlo validate-workflow workflows/ingestion/api/events.py
```

## Environment Variables

CLI behavior can be customized with environment variables:

```bash
# Dagster home directory
export DAGSTER_HOME=~/.dagster

# Workspace YAML location
export DAGSTER_WORKSPACE=/path/to/workspace.yaml

# Phlo configuration
export PHLO_CONFIG=/path/to/phlo.yaml

# Log level
export PHLO_LOG_LEVEL=DEBUG
```

## Exit Codes

```bash
0    # Success
1    # General error
2    # Command not found
3    # Invalid arguments
4    # Configuration error
5    # Service error
```

## Examples Cookbook

### Complete Workflow Setup

```bash
# 1. Create project
phlo init my-project
cd my-project

# 2. Initialize infrastructure
phlo services init

# 3. Start services
phlo services start

# 4. Create workflow
phlo create-workflow

# 5. Run tests
phlo test

# 6. Materialize
phlo materialize --all
```

### Development Workflow

```bash
# Start Observatory/phlo-api natively (no Docker)
phlo services start --native

# Create feature branch
phlo branch create feature-new-workflow

# Create workflow
phlo create-workflow

# Test workflow
phlo test workflows/ingestion/api/events.py

# Materialize to test
phlo materialize dlt_events --partition 2025-01-15

# Merge to main
phlo branch merge feature-new-workflow main
```

### Troubleshooting Workflow

```bash
# Check service status
phlo services status

# View logs
phlo services logs -f dagster-webserver

# Check asset status
phlo status --failed

# Validate configuration
phlo config validate

# Re-materialize failed asset
phlo materialize failed_asset
```

## Next Steps

- [Configuration Reference](configuration.md) - Detailed configuration options
- [Developer Guide](../guides/developer-guide.md) - Building workflows
- [Troubleshooting](../operations/troubleshooting.md) - Common issues

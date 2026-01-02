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

**Core Commands:**

```bash
phlo init                # Initialize new project
phlo services            # Manage infrastructure services
phlo plugin              # Manage plugins
phlo dev                 # Start development server
phlo test                # Run tests
phlo config              # Configuration management
phlo env                 # Environment exports
```

**Workflow Commands:**

```bash
phlo create-workflow     # Create new workflow
phlo validate-workflow   # Validate workflow configuration
```

**Asset Commands:**

```bash
phlo materialize         # Materialize assets
phlo backfill            # Backfill partitioned assets
phlo status              # Show asset status
phlo logs                # Query structured logs
```

**Data Catalog Commands:**

```bash
phlo branch              # Manage Nessie branches
phlo catalog             # Catalog operations (tables, describe, history)
phlo lineage             # Asset lineage (show, export)
```

**Quality Commands:**

```bash
phlo schema              # Manage Pandera schemas
phlo validate-schema     # Validate Pandera schemas
```

**Optional Plugin Commands** (requires installation):

```bash
phlo postgrest           # PostgREST management
phlo hasura              # Hasura GraphQL management
phlo publishing          # dbt publishing layer
phlo metrics             # Prometheus metrics
phlo alerts              # Alerting rules
phlo openmetadata        # OpenMetadata catalog
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
phlo services init [OPTIONS]
```

**What it does**:

- Creates `.phlo/` directory
- Generates Docker Compose configurations
- Sets up network and volume definitions
- Creates `phlo.yaml` config file

**Options**:

```bash
--force              # Overwrite existing configuration
--name NAME          # Project name (default: directory name)
--dev                # Development mode: mount local phlo source
--no-dev             # Explicitly disable dev mode
--phlo-source PATH   # Path to phlo repo or src/phlo for dev mode
```

**Examples**:

```bash
# Basic initialization
phlo services init

# Force overwrite existing
phlo services init --force

# With custom project name
phlo services init --name my-lakehouse

# Development mode with local source
phlo services init --dev --phlo-source /path/to/phlo
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
--profile PROFILE    # Stop only services in specified profile
--service SERVICE    # Stop specific service(s)
--stop-native        # Also stop native subprocess services
```

**Examples**:

```bash
# Stop all services (preserve data)
phlo services stop

# Stop and delete all data
phlo services stop --volumes

# Stop specific profile
phlo services stop --profile observability

# Stop specific services
phlo services stop --service postgres,minio
```

### phlo services list

List available services with status.

```bash
phlo services list [OPTIONS]
```

**Options**:

```bash
--all                # Show all services including optional
--json               # Output as JSON
```

**Examples**:

```bash
phlo services list
phlo services list --all
phlo services list --json
```

### phlo services add

Add an optional service to the project.

```bash
phlo services add SERVICE_NAME [OPTIONS]
```

**Options**:

```bash
--no-start           # Don't start the service after adding
```

**Examples**:

```bash
phlo services add prometheus
phlo services add grafana --no-start
```

### phlo services remove

Remove a service from the project.

```bash
phlo services remove SERVICE_NAME [OPTIONS]
```

**Options**:

```bash
--keep-running       # Don't stop the service
```

**Examples**:

```bash
phlo services remove prometheus
phlo services remove grafana --keep-running
```

### phlo services reset

Reset infrastructure by stopping services and deleting volumes.

```bash
phlo services reset [OPTIONS]
```

**Options**:

```bash
--service SERVICE    # Reset only specific service(s)
-y, --yes            # Skip confirmation
```

**Examples**:

```bash
phlo services reset
phlo services reset --service postgres
phlo services reset -y
```

### phlo services restart

Restart services (stop + start).

```bash
phlo services restart [OPTIONS]
```

**Options**:

```bash
--build              # Rebuild containers before starting
--profile PROFILE    # Restart services in profile
--service SERVICE    # Restart specific service(s)
--dev                # Enable dev mode when restarting
```

**Examples**:

```bash
phlo services restart
phlo services restart --build
phlo services restart --service dagster
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

## Plugin Commands

Manage Phlo plugins for extending functionality.

### phlo plugin list

List all installed plugins.

```bash
phlo plugin list [OPTIONS]
```

**Options**:

```bash
--type TYPE          # Filter by plugin type (sources, quality, transforms, services, hooks, dagster, cli)
--json               # Output as JSON
```

**Examples**:

```bash
# List all plugins
phlo plugin list

# List only source connectors
phlo plugin list --type sources

# List hook plugins
phlo plugin list --type hooks

# JSON output
phlo plugin list --json
```

**Output**:

```
Services:
  NAME              VERSION    DESCRIPTION
  dagster           0.1.0      Dagster orchestration engine
  postgres          0.1.0      PostgreSQL database
  trino             0.1.0      Distributed SQL query engine

Sources:
  NAME              VERSION    DESCRIPTION
  rest_api          1.0.0      REST API connector
  jsonplaceholder   1.0.0      JSONPlaceholder example source

Quality Checks:
  NAME              VERSION    DESCRIPTION
  null_check        1.0.0      Null value validation
  threshold_check   1.0.0      Threshold validation
```

### phlo plugin search

Search available plugins in the registry.

```bash
phlo plugin search [QUERY] [OPTIONS]
```

**Options**:

```bash
--type TYPE          # Filter by plugin type
--json               # Output as JSON
--tag TAG            # Filter by tag
```

**Examples**:

```bash
# Search for PostgreSQL-related plugins
phlo plugin search postgres

# Search for quality check plugins
phlo plugin search --type quality

# Search for hook plugins
phlo plugin search --type hooks

# Search by tag
phlo plugin search --tag observability
```

### phlo plugin install

Install a plugin from the registry.

```bash
phlo plugin install PLUGIN_NAME [OPTIONS]
```

**Options**:

```bash
--version VERSION    # Specific version to install
--upgrade            # Upgrade if already installed
```

**Examples**:

```bash
# Install a plugin
phlo plugin install phlo-superset

# Install specific version
phlo plugin install phlo-superset --version 0.2.0

# Upgrade existing
phlo plugin install phlo-superset --upgrade
```

### phlo plugin info

Show detailed information about a plugin.

```bash
phlo plugin info PLUGIN_NAME [OPTIONS]
```

**Options**:

```bash
--type TYPE          # Plugin type (auto-detected if omitted)
--json               # Output as JSON
```

**Examples**:

```bash
# Get plugin info (auto-detect type)
phlo plugin info dagster

# Specify type
phlo plugin info rest_api --type sources

# JSON output
phlo plugin info dagster --json
```

**Output**:

```
dagster
Type: services
Version: 0.1.0
Author: Phlo Team
Description: Dagster orchestration engine for workflow management
License: MIT
Homepage: https://github.com/iamgp/phlo
Tags: orchestration, core, service

Service Details:
  Container: dagster-webserver
  Ports: 10006
  Dependencies: postgres
```

### phlo plugin update

Update plugins to latest versions.

```bash
phlo plugin update [PLUGIN_NAME] [OPTIONS]
```

**Options**:

```bash
--all                # Update all plugins
--check              # Check for updates without installing
```

**Examples**:

```bash
# Update specific plugin
phlo plugin update phlo-superset

# Update all plugins
phlo plugin update --all

# Check for updates
phlo plugin update --check
```

### phlo plugin create

Create a new plugin scaffold (for plugin development).

```bash
phlo plugin create PLUGIN_NAME --type TYPE [OPTIONS]
```

**Options**:

```bash
--type TYPE          # Plugin type: source, quality, transform, service
--path PATH          # Custom output path
--author AUTHOR      # Author name
--description DESC   # Plugin description
```

**Examples**:

```bash
# Create source connector plugin
phlo plugin create my-api-source --type source

# Create quality check plugin
phlo plugin create my-validation --type quality

# Create hook plugin
phlo plugin create my-hooks --type hook

# Create with custom path
phlo plugin create my-plugin --type source --path ./plugins/my-plugin
```

**Creates**:

```
phlo-plugin-my-api-source/
├── pyproject.toml           # Package config with entry points
├── README.md                # Documentation
├── src/
│   └── phlo_my_api_source/
│       ├── __init__.py
│       └── plugin.py        # Plugin implementation
└── tests/
    └── test_plugin.py       # Test suite
```

### phlo plugin check

Validate installed plugins.

```bash
phlo plugin check [OPTIONS]
```

**Options**:

```bash
--json               # Output as JSON
```

**Examples**:

```bash
# Validate all plugins
phlo plugin check

# JSON output
phlo plugin check --json
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
├── .env.example          # Local secrets template (.phlo/.env.local)
├── workflows/
│   ├── ingestion/
│   ├── schemas/
│   └── transforms/
│       └── dbt/
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
--port PORT          # Port for webserver (default: 3000)
--host HOST          # Host to bind (default: 127.0.0.1)
--workspace PATH     # Path to workspace.yaml
```

**Example**:

```bash
phlo dev --port 3000
```

Opens Dagster UI at http://localhost:3000

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

## Logging & Monitoring Commands

### phlo logs

Query and filter structured logs from Dagster runs.

```bash
phlo logs [OPTIONS]
```

**Options**:

```bash
--asset NAME         # Filter by asset name
--job NAME           # Filter by job name
--level LEVEL        # Filter by log level: DEBUG, INFO, WARNING, ERROR
--since TIME         # Filter by time (e.g., 1h, 30m, 2d)
--run-id ID          # Get logs for specific run
--follow, -f         # Tail mode - follow new logs in real-time
--full               # Don't truncate long messages
--limit N            # Number of logs to retrieve (default: 100)
--json               # JSON output for scripting
```

**Examples**:

```bash
# View recent logs
phlo logs

# Filter by asset
phlo logs --asset dlt_glucose_entries

# Filter by log level
phlo logs --level ERROR

# Logs from last hour
phlo logs --since 1h

# Follow logs in real-time
phlo logs --follow

# Logs for specific run
phlo logs --run-id abc-123-def

# JSON output for processing
phlo logs --json --limit 500
```

### phlo backfill

Backfill partitioned assets over a date range.

```bash
phlo backfill [ASSET_NAME] [OPTIONS]
```

**Arguments**:

- `ASSET_NAME` (optional): Asset to backfill

**Options**:

```bash
--start-date DATE    # Start date (YYYY-MM-DD)
--end-date DATE      # End date (YYYY-MM-DD)
--partitions DATES   # Comma-separated partition dates (YYYY-MM-DD,...)
--parallel N         # Number of concurrent partitions (default: 1)
--resume             # Resume last backfill, skipping completed partitions
--dry-run            # Show what would be executed without running
--delay SECS         # Delay between parallel executions in seconds (default: 0.0)
```

**Examples**:

```bash
# Backfill for date range
phlo backfill dlt_glucose_entries --start-date 2025-01-01 --end-date 2025-01-31

# Specific partitions
phlo backfill dlt_glucose_entries --partitions 2025-01-15,2025-01-16,2025-01-17

# Parallel backfill (5 concurrent)
phlo backfill dlt_glucose_entries --start-date 2025-01-01 --end-date 2025-01-31 --parallel 5

# Resume interrupted backfill
phlo backfill dlt_glucose_entries --resume

# Dry run to see what would execute
phlo backfill dlt_glucose_entries --start-date 2025-01-01 --end-date 2025-01-07 --dry-run

# With delay between executions
phlo backfill dlt_glucose_entries --start-date 2025-01-01 --end-date 2025-01-31 --parallel 3 --delay 2.5
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

### phlo branch diff

Show differences between two branches.

```bash
phlo branch diff SOURCE_BRANCH [TARGET_BRANCH] [OPTIONS]
```

**Arguments**:

- `SOURCE_BRANCH`: Source branch to compare
- `TARGET_BRANCH`: Target branch (default: main)

**Options**:

```bash
--format FORMAT      # Output format: table, json (default: table)
```

**Examples**:

```bash
# Compare dev to main
phlo branch diff dev

# Compare two branches
phlo branch diff feature-a feature-b

# JSON output
phlo branch diff dev main --format json
```

## Catalog Commands

Manage the Iceberg catalog (Nessie-backed).

### phlo catalog tables

List all Iceberg tables in the catalog.

```bash
phlo catalog tables [OPTIONS]
```

**Options**:

```bash
--namespace NS       # Filter by namespace (e.g., bronze, silver)
--ref REF            # Nessie branch/tag reference (default: main)
--format FORMAT      # Output format: table, json (default: table)
```

**Examples**:

```bash
# List all tables
phlo catalog tables

# List tables in specific namespace
phlo catalog tables --namespace bronze

# List tables on specific branch
phlo catalog tables --ref feature-branch

# JSON output
phlo catalog tables --format json
```

### phlo catalog describe

Show detailed table metadata.

```bash
phlo catalog describe TABLE_NAME [OPTIONS]
```

**Arguments**:

- `TABLE_NAME`: Table to describe (e.g., `bronze.events`)

**Options**:

```bash
--ref REF            # Nessie branch/tag reference (default: main)
```

**Examples**:

```bash
# Describe table
phlo catalog describe bronze.events

# Describe on specific branch
phlo catalog describe bronze.events --ref dev
```

**Output**:

Shows table metadata including:

- Location
- Current snapshot ID
- Format version
- Schema (columns, types, constraints)
- Partitioning
- Properties

### phlo catalog history

Show table snapshot history.

```bash
phlo catalog history TABLE_NAME [OPTIONS]
```

**Arguments**:

- `TABLE_NAME`: Table name

**Options**:

```bash
--limit N            # Number of snapshots to show (default: 10)
--ref REF            # Nessie branch/tag reference (default: main)
```

**Examples**:

```bash
# Show recent snapshots
phlo catalog history bronze.events

# Show last 20 snapshots
phlo catalog history bronze.events --limit 20
```

### phlo lineage show

Display asset lineage in ASCII tree format.

```bash
phlo lineage show ASSET_NAME [OPTIONS]
```

**Arguments**:

- `ASSET_NAME`: Asset name to show lineage for

**Options**:

```bash
--direction DIR      # Direction: upstream, downstream, both (default: both)
--depth N            # Maximum depth to traverse
```

**Examples**:

```bash
# Show full lineage
phlo lineage show dlt_glucose_entries

# Show only upstream dependencies
phlo lineage show dlt_glucose_entries --direction upstream

# Limit depth
phlo lineage show dlt_glucose_entries --depth 2
```

### phlo lineage export

Export lineage to external formats.

```bash
phlo lineage export ASSET_NAME [OPTIONS]
```

**Arguments**:

- `ASSET_NAME`: Asset name to export lineage for

**Options**:

```bash
--format FORMAT      # Export format: dot, mermaid, json (default: dot)
--output PATH        # Output file path (required)
```

**Examples**:

```bash
# Export to Graphviz DOT
phlo lineage export dlt_glucose_entries --format dot --output lineage.dot

# Export to Mermaid diagram
phlo lineage export dlt_glucose_entries --format mermaid --output lineage.md

# Export to JSON
phlo lineage export dlt_glucose_entries --format json --output lineage.json
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
# Validate phlo.yaml
phlo config validate phlo.yaml
```

### phlo env export

Export the generated environment configuration.

```bash
phlo env export [OPTIONS]
```

**Examples**:

```bash
# Export non-secret defaults
phlo env export

# Export with secrets (from .phlo/.env.local)
phlo env export --include-secrets

# Write to a file
phlo env export --include-secrets --output env.full
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
phlo validate-schema workflows/schemas/events.py
phlo validate-schema workflows/schemas/events.py --data sample.parquet
```

### phlo validate-workflow

Validate workflow configuration.

```bash
phlo validate-workflow WORKFLOW_PATH [OPTIONS]
```

**Arguments**:

- `WORKFLOW_PATH`: Path to workflow file or directory

**Options**:

```bash
--fix                # Auto-fix issues where possible
```

**Examples**:

```bash
# Validate single workflow
phlo validate-workflow workflows/ingestion/api/events.py

# Validate directory
phlo validate-workflow workflows/ingestion/

# Auto-fix where possible
phlo validate-workflow workflows/ingestion/weather.py --fix
```

### phlo schema

Manage Pandera schemas.

```bash
phlo schema COMMAND [OPTIONS]
```

**Subcommands**:

#### list

List all available Pandera schemas.

```bash
phlo schema list [OPTIONS]
```

**Options**:

```bash
--domain DOMAIN      # Filter by domain
--format FORMAT      # Output format: table, json (default: table)
```

**Examples**:

```bash
# List all schemas
phlo schema list

# Filter by domain
phlo schema list --domain api

# JSON output
phlo schema list --format json
```

## Optional Plugin Commands

The following commands are provided by optional packages. Install the corresponding package to use these commands.

### phlo postgrest

PostgREST configuration and management.

**Installation**: `phlo plugin install phlo-postgrest`

### phlo hasura

Hasura GraphQL engine management.

**Installation**: `phlo plugin install phlo-hasura`

### phlo publishing

dbt publishing layer management.

**Installation**: `phlo plugin install phlo-dbt`

### phlo metrics

Prometheus metrics configuration.

**Installation**: `phlo plugin install phlo-metrics`

### phlo alerts

Alerting rules and notifications.

**Installation**: `phlo plugin install phlo-alerting`

### phlo openmetadata

OpenMetadata catalog integration.

**Installation**: `phlo plugin install phlo-openmetadata`

Run `phlo <command> --help` after installation for command-specific documentation.

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

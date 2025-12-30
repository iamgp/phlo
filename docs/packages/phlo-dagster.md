# phlo-dagster

Data orchestration platform for Phlo.

## Overview

`phlo-dagster` provides the core data orchestration platform for scheduling, monitoring, and managing data pipelines. It runs ingestion, transformation, and quality workflows as Dagster assets.

## Installation

```bash
pip install phlo-dagster
# or
phlo plugin install dagster
```

## Configuration

| Variable         | Default     | Description            |
| ---------------- | ----------- | ---------------------- |
| `DAGSTER_PORT`   | `3000`      | Dagster webserver port |
| `WORKFLOWS_PATH` | `workflows` | Path to workflow files |

## Features

### Auto-Configuration

This package is **fully auto-configured**:

| Feature                | How It Works                                                              |
| ---------------------- | ------------------------------------------------------------------------- |
| **Plugin Discovery**   | Auto-discovers Dagster extensions via `phlo.plugins.dagster` entry points |
| **dbt Compilation**    | Auto-compiles dbt on startup via post_start hook                          |
| **Workflow Discovery** | Auto-discovers workflows in `workflows/` directory                        |
| **Metrics Labels**     | Exposes Dagster metrics for Prometheus                                    |

### Post-Start Hook

The Dagster service automatically runs dbt compilation on startup:

```yaml
hooks:
  post_start:
    - name: dbt-compile
      command: dbt compile
```

### Plugin Discovery

Dagster extensions are auto-loaded through the plugin system:

- `@phlo_ingestion` assets from phlo-dlt
- `IcebergResource` from phlo-iceberg
- dbt assets from phlo-dbt
- Quality checks from phlo-quality

## Usage

### Starting the Service

```bash
# Start Dagster
phlo services start --service dagster

# Start with dev mode (editable install from source)
phlo services init --dev --phlo-source /path/to/phlo
phlo services start
```

### Development Server

For local development without Docker:

```bash
phlo dev                    # Start on localhost:3000
phlo dev --port 8080        # Use custom port
```

### Materializing Assets

```bash
# Via Dagster CLI
dagster asset materialize --select my_asset

# Via Phlo CLI
phlo materialize my_asset
```

## Endpoints

| Endpoint    | URL                             |
| ----------- | ------------------------------- |
| **Web UI**  | `http://localhost:3000`         |
| **GraphQL** | `http://localhost:3000/graphql` |
| **Metrics** | `http://localhost:3000/metrics` |

## Architecture

```
┌──────────────────────────────────────────┐
│           Dagster Webserver              │
│  - Asset UI                              │
│  - Run monitoring                        │
│  - Schedule management                   │
├──────────────────────────────────────────┤
│           Dagster Daemon                 │
│  - Schedule execution                    │
│  - Sensor polling                        │
│  - Auto-materialization                  │
├──────────────────────────────────────────┤
│         Phlo Plugin Extensions           │
│  - DLT Ingestion                         │
│  - dbt Transformations                   │
│  - Quality Checks                        │
│  - Iceberg Resources                     │
└──────────────────────────────────────────┘
```

## Entry Points

| Entry Point             | Plugin                                               |
| ----------------------- | ---------------------------------------------------- |
| `phlo.plugins.services` | `DagsterServicePlugin`, `DagsterDaemonServicePlugin` |
| `phlo.plugins.cli`      | Dagster CLI commands                                 |

## Related Packages

- [phlo-dlt](phlo-dlt.md) - Data ingestion
- [phlo-dbt](phlo-dbt.md) - SQL transformations
- [phlo-quality](phlo-quality.md) - Data quality checks
- [phlo-iceberg](phlo-iceberg.md) - Iceberg table access

## Next Steps

- [Workflow Development Guide](../guides/workflow-development.md) - Build data pipelines
- [Dagster Assets Guide](../guides/dagster-assets.md) - Asset patterns
- [Developer Guide](../guides/developer-guide.md) - Decorator usage

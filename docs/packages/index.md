# Phlo Packages Reference

Phlo is organized as a monorepo with individual packages that provide specific functionality. Each package can be installed independently or as part of a complete installation.

## Package Categories

### Core Framework

| Package  | Description                                                      |
| -------- | ---------------------------------------------------------------- |
| **phlo** | Core framework with CLI, plugin system, configuration, and hooks |

### Data Processing

| Package                         | Description                                                         |
| ------------------------------- | ------------------------------------------------------------------- |
| [phlo-dagster](phlo-dagster.md) | Data orchestration platform for scheduling and monitoring pipelines |
| [phlo-dbt](phlo-dbt.md)         | dbt integration for SQL transformations                             |
| [phlo-dlt](phlo-dlt.md)         | Data Load Tool integration for ingestion                            |
| [phlo-iceberg](phlo-iceberg.md) | Apache Iceberg catalog and table format support                     |
| [phlo-quality](phlo-quality.md) | Data quality validation and checks                                  |
| [phlo-lineage](phlo-lineage.md) | Data lineage tracking and visualization                             |

### Infrastructure Services

| Package                           | Description                         |
| --------------------------------- | ----------------------------------- |
| [phlo-postgres](phlo-postgres.md) | PostgreSQL database service         |
| [phlo-nessie](phlo-nessie.md)     | Git-like catalog for Iceberg tables |
| [phlo-trino](phlo-trino.md)       | Distributed SQL query engine        |
| [phlo-minio](phlo-minio.md)       | S3-compatible object storage        |

### Observability

| Package                               | Description                          |
| ------------------------------------- | ------------------------------------ |
| [phlo-grafana](phlo-grafana.md)       | Metrics visualization and dashboards |
| [phlo-prometheus](phlo-prometheus.md) | Metrics collection and alerting      |
| [phlo-loki](phlo-loki.md)             | Log aggregation                      |
| [phlo-alloy](phlo-alloy.md)           | OpenTelemetry collector              |
| [phlo-alerting](phlo-alerting.md)     | Alert management and routing         |
| [phlo-metrics](phlo-metrics.md)       | Custom metrics collection            |

### API Layer

| Package                             | Description                              |
| ----------------------------------- | ---------------------------------------- |
| [phlo-api](phlo-api.md)             | FastAPI REST endpoints for Phlo          |
| [phlo-postgrest](phlo-postgrest.md) | Auto-generated REST API from PostgreSQL  |
| [phlo-hasura](phlo-hasura.md)       | GraphQL API with real-time subscriptions |

### Data Catalog & Governance

| Package                                   | Description                          |
| ----------------------------------------- | ------------------------------------ |
| [phlo-openmetadata](phlo-openmetadata.md) | Data catalog and governance platform |

### User Interface

| Package                                 | Description                                        |
| --------------------------------------- | -------------------------------------------------- |
| [phlo-observatory](phlo-observatory.md) | Web UI for exploring data and monitoring pipelines |
| [phlo-superset](phlo-superset.md)       | Business intelligence and visualization            |
| [phlo-pgweb](phlo-pgweb.md)             | PostgreSQL web interface                           |

### Testing & Development

| Package                                   | Description                           |
| ----------------------------------------- | ------------------------------------- |
| [phlo-testing](phlo-testing.md)           | Testing utilities and fixtures        |
| [phlo-core-plugins](phlo-core-plugins.md) | Built-in plugins for common use cases |

## Installation

### Full Installation (Recommended)

Install Phlo with all default services:

```bash
uv pip install phlo[defaults]
```

This includes core data processing packages and infrastructure services.

### Minimal Installation

Install only the core framework:

```bash
uv pip install phlo
```

Then add packages as needed:

```bash
uv pip install phlo-dagster phlo-postgres phlo-trino
```

### With Optional Profiles

```bash
# With observability stack
uv pip install phlo[defaults,observability]

# With API layer
uv pip install phlo[defaults,api]

# With data catalog
uv pip install phlo[defaults,catalog]
```

## Plugin System

All packages integrate through Phlo's unified plugin system using Python entry points. When a package is installed, its plugins are automatically discovered and registered.

### Entry Point Groups

| Entry Point                   | Description                                    |
| ----------------------------- | ---------------------------------------------- |
| `phlo.plugins.services`       | Infrastructure service definitions             |
| `phlo.plugins.assets`         | Asset spec providers                            |
| `phlo.plugins.resources`      | Resource spec providers                         |
| `phlo.plugins.orchestrators`  | Orchestrator adapters                           |
| `phlo.plugins.sources`        | Data source connectors                         |
| `phlo.plugins.quality`        | Quality check implementations                  |
| `phlo.plugins.transforms`     | Data transformation plugins                    |
| `phlo.plugins.cli`            | CLI command extensions                         |
| `phlo.plugins.hooks`          | Event hook handlers                            |
| `phlo.plugins.observatory`    | Observatory UI extension manifests             |
| `phlo.plugins.catalogs`       | Catalog configurations (filter by target)      |
| `phlo.plugins.dagster`        | Legacy Dagster extensions (when needed)        |

### Discovering Installed Plugins

```bash
# List all installed plugins
phlo plugin list

# List by type
phlo plugin list --type services

# Get plugin details
phlo plugin info dagster
```

## Package Versioning

All packages in the monorepo share a synchronized version number. When installing, ensure all Phlo packages are at the same version to avoid compatibility issues.

Check installed versions:

```bash
pip list | grep phlo
```

## Creating Custom Packages

See the [Plugin Development Guide](../guides/plugin-development.md) for creating custom packages that integrate with Phlo.

## Next Steps

- [Plugin Development Guide](../guides/plugin-development.md) - Build custom plugins
- [Installation Guide](../getting-started/installation.md) - Complete installation instructions
- [CLI Reference](../reference/cli-reference.md) - CLI commands for managing packages

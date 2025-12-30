# phlo-loki

Loki log aggregation for Phlo.

## Overview

`phlo-loki` provides centralized log aggregation for the Phlo observability stack. It collects logs from all services and makes them queryable via Grafana.

## Installation

```bash
pip install phlo-loki
# or
phlo plugin install loki
```

## Profile

Part of the `observability` profile.

## Configuration

| Variable              | Default | Description          |
| --------------------- | ------- | -------------------- |
| `LOKI_PORT`           | `3100`  | Loki API port        |
| `LOKI_RETENTION_DAYS` | `7`     | Log retention period |

## Features

### Auto-Configuration

| Feature                 | How It Works                                   |
| ----------------------- | ---------------------------------------------- |
| **Log Collection**      | All Docker container logs collected via Alloy  |
| **Label Enrichment**    | Auto-labels with service name, container, etc. |
| **Grafana Integration** | Pre-configured as Grafana datasource           |

## Usage

### Starting the Service

```bash
# Start with observability profile
phlo services start --profile observability

# Or start individually
phlo services start --service loki
```

### Querying Logs

Access logs via Grafana's Explore view:

```logql
# All Dagster logs
{service="dagster"}

# Error logs from any service
{} |= "error"

# Pipeline-specific logs
{service="dagster"} |~ "pipeline.*run"

# Logs with JSON parsing
{service="dagster"} | json | level="ERROR"
```

### Log Labels

Logs are labeled with:

| Label       | Description                         |
| ----------- | ----------------------------------- |
| `service`   | Service name (dagster, trino, etc.) |
| `container` | Container name                      |
| `level`     | Log level (INFO, ERROR, etc.)       |
| `job`       | Job/pipeline name                   |

## Endpoints

| Endpoint  | URL                                       |
| --------- | ----------------------------------------- |
| **API**   | `http://localhost:3100`                   |
| **Push**  | `http://localhost:3100/loki/api/v1/push`  |
| **Query** | `http://localhost:3100/loki/api/v1/query` |

## Entry Points

| Entry Point             | Plugin              |
| ----------------------- | ------------------- |
| `phlo.plugins.services` | `LokiServicePlugin` |

## Related Packages

- [phlo-grafana](phlo-grafana.md) - Visualization
- [phlo-alloy](phlo-alloy.md) - Log shipping
- [phlo-prometheus](phlo-prometheus.md) - Metrics

## Next Steps

- [Observability Setup](../setup/observability.md) - Complete monitoring setup
- [Troubleshooting Guide](../operations/troubleshooting.md) - Debug with logs

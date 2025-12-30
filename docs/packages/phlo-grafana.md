# phlo-grafana

Grafana visualization service for Phlo.

## Overview

`phlo-grafana` provides metrics visualization and dashboards for observability. It comes pre-configured with datasources for Prometheus, Loki, Trino, and PostgreSQL.

## Installation

```bash
pip install phlo-grafana
# or
phlo plugin install grafana
```

## Profile

Part of the `observability` profile.

## Configuration

| Variable                 | Default  | Description         |
| ------------------------ | -------- | ------------------- |
| `GRAFANA_PORT`           | `3003`   | Grafana web UI port |
| `GRAFANA_VERSION`        | `11.3.1` | Grafana version     |
| `GRAFANA_ADMIN_USER`     | `admin`  | Admin username      |
| `GRAFANA_ADMIN_PASSWORD` | `admin`  | Admin password      |

## Features

### Auto-Configuration

| Feature            | How It Works                                         |
| ------------------ | ---------------------------------------------------- |
| **Datasources**    | Pre-provisioned: Prometheus, Loki, Trino, PostgreSQL |
| **Dashboards**     | Pre-provisioned dashboards in `grafana/dashboards/`  |
| **Metrics Labels** | Exposes Grafana metrics for Prometheus               |

### Pre-Configured Datasources

| Datasource | Type       | URL                    |
| ---------- | ---------- | ---------------------- |
| Prometheus | prometheus | http://prometheus:9090 |
| Loki       | loki       | http://loki:3100       |
| Trino      | trino      | http://trino:8080      |
| PostgreSQL | postgres   | postgres:5432          |

### Pre-Built Dashboards

| Dashboard         | Description                |
| ----------------- | -------------------------- |
| Phlo Overview     | High-level system health   |
| Dagster Pipelines | Pipeline execution metrics |
| Data Quality      | Quality check results      |
| Trino Queries     | Query performance          |
| MinIO Storage     | Storage utilization        |

## Usage

### Starting the Service

```bash
# Start with observability profile
phlo services start --profile observability

# Or start individually
phlo services start --service grafana
```

### Access

- **URL**: `http://localhost:3003`
- **Username**: `admin`
- **Password**: `admin`

### Creating Dashboards

1. Login to Grafana
2. Navigate to Dashboards → New Dashboard
3. Add panels with queries to your datasources
4. Save and export JSON

### Alerting

Configure alerts in Grafana:

1. Edit a panel
2. Go to Alert tab
3. Configure conditions
4. Add notification channels

## Endpoints

| Endpoint    | URL                             |
| ----------- | ------------------------------- |
| **Web UI**  | `http://localhost:3003`         |
| **API**     | `http://localhost:3003/api`     |
| **Metrics** | `http://localhost:3003/metrics` |

## Entry Points

| Entry Point             | Plugin                 |
| ----------------------- | ---------------------- |
| `phlo.plugins.services` | `GrafanaServicePlugin` |

## Related Packages

- [phlo-prometheus](phlo-prometheus.md) - Metrics collection
- [phlo-loki](phlo-loki.md) - Log aggregation
- [phlo-alerting](phlo-alerting.md) - Alert management

## Next Steps

- [Observability Setup](../setup/observability.md) - Complete monitoring setup
- [Operations Guide](../operations/operations-guide.md) - Monitoring best practices
- [Troubleshooting](../operations/troubleshooting.md) - Debug issues

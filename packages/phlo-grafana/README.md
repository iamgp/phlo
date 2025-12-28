# phlo-grafana

Grafana visualization service for Phlo.

## Description

Metrics visualization and dashboards for observability. Pre-configured with datasources for Prometheus, Loki, Trino, and PostgreSQL.

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

## Auto-Configuration

This package is **fully auto-configured**:

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

## Usage

```bash
# Start with observability profile
phlo services start --profile observability

# Or start individually
phlo services start --service grafana
```

## Endpoints

- **Web UI**: `http://localhost:3003`
- **Login**: admin / admin

## Entry Points

- `phlo.plugins.services` - Provides `GrafanaServicePlugin`

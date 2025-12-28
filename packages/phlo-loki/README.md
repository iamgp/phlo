# phlo-loki

Loki log aggregation for Phlo.

## Description

Log aggregation and querying service. Receives logs from Alloy and provides log search in Grafana.

## Installation

```bash
pip install phlo-loki
# or
phlo plugin install loki
```

## Profile

Part of the `observability` profile.

## Configuration

| Variable       | Default | Description   |
| -------------- | ------- | ------------- |
| `LOKI_PORT`    | `3100`  | Loki API port |
| `LOKI_VERSION` | `3.2.1` | Loki version  |

## Auto-Configuration

This package is **fully auto-configured**:

| Feature                | How It Works                                   |
| ---------------------- | ---------------------------------------------- |
| **Metrics Labels**     | Exposes Loki metrics for Prometheus            |
| **Grafana Datasource** | Pre-configured in Grafana as "Loki" datasource |
| **Alloy Integration**  | Receives logs from Alloy                       |

## Usage

```bash
# Start with observability profile
phlo services start --profile observability

# Or start individually
phlo services start --service loki
```

## Endpoints

- **API**: `http://localhost:3100`
- **Ready**: `http://localhost:3100/ready`

## Entry Points

- `phlo.plugins.services` - Provides `LokiServicePlugin`

# phlo-alloy

Grafana Alloy log collector for Phlo.

## Overview

`phlo-alloy` collects logs from all Docker containers and ships them to Loki for aggregation and querying.

## Installation

```bash
pip install phlo-alloy
# or
phlo plugin install alloy
```

## Profile

Part of the `observability` profile.

## Configuration

| Variable     | Default | Description     |
| ------------ | ------- | --------------- |
| `ALLOY_PORT` | `12345` | Alloy HTTP port |

## Features

### Auto-Configuration

| Feature                 | How It Works                                           |
| ----------------------- | ------------------------------------------------------ |
| **Container Discovery** | Auto-discovers all Docker containers via Docker socket |
| **Log Collection**      | Collects stdout/stderr from all containers             |
| **Loki Shipping**       | Ships logs to Loki for storage and querying            |
| **Metrics Labels**      | Exposes Alloy metrics for Prometheus                   |

### Docker Socket Access

Alloy mounts the Docker socket to discover and collect logs from all containers:

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
```

## Usage

### Starting the Service

```bash
# Start with observability profile
phlo services start --profile observability

# Or start individually
phlo services start --service alloy
```

## Endpoints

| Endpoint  | URL                              |
| --------- | -------------------------------- |
| **HTTP**  | `http://localhost:12345`         |
| **Ready** | `http://localhost:12345/-/ready` |

## Entry Points

| Entry Point             | Plugin               |
| ----------------------- | -------------------- |
| `phlo.plugins.services` | `AlloyServicePlugin` |

## Related Packages

- [phlo-loki](phlo-loki.md) - Log storage
- [phlo-grafana](phlo-grafana.md) - Log visualization
- [phlo-prometheus](phlo-prometheus.md) - Metrics collection

## Next Steps

- [Observability Setup](../setup/observability.md) - Complete monitoring setup
- [Troubleshooting Guide](../operations/troubleshooting.md) - Debug with logs

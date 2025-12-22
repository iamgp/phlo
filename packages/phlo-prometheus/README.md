# phlo-prometheus

Prometheus metrics collection service plugin for Phlo.

## Description

Metrics collection and monitoring for observability.

## Installation

```bash
pip install phlo-prometheus
# or
phlo plugin install prometheus
```

## Profile

Part of the `observability` profile.

## Configuration

| Variable          | Default | Description |
| ----------------- | ------- | ----------- |
| `PROMETHEUS_PORT` | `9090`  | Web UI port |

## Usage

```bash
phlo services start --profile observability
# or
phlo services start --service prometheus
```

## Endpoints

- **Web UI**: `http://localhost:9090`

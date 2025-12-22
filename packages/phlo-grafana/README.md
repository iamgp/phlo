# phlo-grafana

Grafana metrics visualization service plugin for Phlo.

## Description

Metrics visualization and dashboards for observability.

## Installation

```bash
pip install phlo-grafana
# or
phlo plugin install grafana
```

## Profile

Part of the `observability` profile.

## Configuration

| Variable       | Default | Description |
| -------------- | ------- | ----------- |
| `GRAFANA_PORT` | `3001`  | Web UI port |

## Usage

```bash
phlo services start --profile observability
# or
phlo services start --service grafana
```

## Endpoints

- **Web UI**: `http://localhost:3001`

# phlo-loki

Grafana Loki log aggregation service plugin for Phlo.

## Description

Log aggregation and querying for observability.

## Installation

```bash
pip install phlo-loki
# or
phlo plugin install loki
```

## Profile

Part of the `observability` profile.

## Configuration

| Variable    | Default | Description   |
| ----------- | ------- | ------------- |
| `LOKI_PORT` | `3100`  | HTTP API port |

## Usage

```bash
phlo services start --profile observability
# or
phlo services start --service loki
```

## Endpoints

- **API**: `http://localhost:3100`

# phlo-superset

Apache Superset BI service plugin for Phlo.

## Description

Apache Superset for business intelligence and data visualization.

## Installation

```bash
pip install phlo-superset
# or
phlo plugin install superset
```

## Configuration

| Variable                  | Default | Description    |
| ------------------------- | ------- | -------------- |
| `SUPERSET_PORT`           | `8088`  | Web UI port    |
| `SUPERSET_ADMIN_USER`     | `admin` | Admin username |
| `SUPERSET_ADMIN_PASSWORD` | `admin` | Admin password |

## Usage

```bash
phlo services start --service superset
```

## Dependencies

- postgres

## Endpoints

- **Web UI**: `http://localhost:8088`

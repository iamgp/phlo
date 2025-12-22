# phlo-dagster

Dagster orchestration service plugin for Phlo.

## Description

Data orchestration platform for workflows and pipelines. Includes both the webserver and daemon components.

## Installation

```bash
pip install phlo-dagster
# or
phlo plugin install dagster
```

## Configuration

| Variable             | Default  | Description                          |
| -------------------- | -------- | ------------------------------------ |
| `DAGSTER_PORT`       | `3000`   | Webserver port                       |
| `PHLO_VERSION`       | (latest) | Phlo version to install              |
| `PHLO_HOST_PLATFORM` | (auto)   | Host platform for executor selection |

## Usage

```bash
phlo services start --service dagster
```

## Dependencies

- postgres
- minio
- nessie
- trino

# phlo-nessie

Nessie catalog service plugin for Phlo.

## Description

Git-like catalog for Iceberg tables with branch/merge support.

## Installation

```bash
pip install phlo-nessie
# or
phlo plugin install nessie
```

## Configuration

| Variable      | Default | Description   |
| ------------- | ------- | ------------- |
| `NESSIE_PORT` | `19120` | REST API port |

## Usage

```bash
phlo services start --service nessie
```

## Endpoints

- **REST API**: `http://localhost:19120/api/v1`
- **Iceberg REST**: `http://localhost:19120/iceberg`

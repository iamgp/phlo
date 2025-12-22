# phlo-trino

Trino distributed SQL query engine plugin for Phlo.

## Description

Distributed SQL query engine for the data lake.

## Installation

```bash
pip install phlo-trino
# or
phlo plugin install trino
```

## Configuration

| Variable     | Default | Description |
| ------------ | ------- | ----------- |
| `TRINO_PORT` | `8080`  | HTTP port   |

## Usage

```bash
phlo services start --service trino
```

## Dependencies

- nessie
- minio

## Endpoints

- **HTTP**: `http://localhost:8080`

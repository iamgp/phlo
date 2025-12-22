# phlo-postgrest

PostgREST API service plugin for Phlo.

## Description

RESTful API automatically generated from PostgreSQL schema.

## Installation

```bash
pip install phlo-postgrest
# or
phlo plugin install postgrest
```

## Configuration

| Variable         | Default | Description   |
| ---------------- | ------- | ------------- |
| `POSTGREST_PORT` | `3001`  | REST API port |

## Usage

```bash
phlo services start --service postgrest
```

## Dependencies

- postgres

## Endpoints

- **REST API**: `http://localhost:3001`

# Phlo Services Schema

This directory contains the schema definitions for `service.yaml` files.

## Overview

Each service in `services/` is defined by a `service.yaml` file that describes:
- Service metadata (name, description, category)
- Installation behavior (default, profile)
- Dependencies on other services
- Docker container configuration
- Environment variables

The Phlo CLI reads these definitions to dynamically compose infrastructure for lakehouses.

## Schema Files

- `service.schema.yaml` - Human-readable schema documentation
- `service.schema.json` - JSON Schema for validation

## Service Categories

| Category | Description | Default? |
|----------|-------------|----------|
| `core` | Essential infrastructure (postgres, minio, nessie, trino) | Yes |
| `orchestration` | Workflow orchestration (dagster) | Yes |
| `bi` | Business intelligence (superset) | Yes |
| `admin` | Admin tools (pgweb) | Yes |
| `api` | API layer (postgrest, hasura, fastapi) | No (profile: api) |
| `observability` | Monitoring (prometheus, grafana, loki) | No (profile: observability) |

## Example service.yaml

```yaml
name: postgres
description: PostgreSQL database for metadata storage
category: core
default: true

image: postgres:16-alpine

compose:
  restart: unless-stopped
  environment:
    POSTGRES_USER: ${POSTGRES_USER:-phlo}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-phlo}
    POSTGRES_DB: ${POSTGRES_DB:-phlo}
  ports:
    - "${POSTGRES_PORT:-5432}:5432"
  volumes:
    - ./volumes/postgres:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-phlo}"]
    interval: 10s
    timeout: 5s
    retries: 10

env_vars:
  POSTGRES_USER:
    default: phlo
    description: PostgreSQL username
  POSTGRES_PASSWORD:
    default: phlo
    description: PostgreSQL password
    secret: true
  POSTGRES_DB:
    default: phlo
    description: PostgreSQL database name
  POSTGRES_PORT:
    default: 5432
    description: PostgreSQL port
```

## CLI Usage

```bash
# Initialize with default services
phlo services init

# Add optional services
phlo services add observability
phlo services add api

# List available services
phlo services list

# Remove a service
phlo services remove superset
```

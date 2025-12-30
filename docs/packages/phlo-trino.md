# phlo-trino

Trino distributed SQL query engine for Phlo.

## Overview

`phlo-trino` provides the Trino query engine for SQL access to the Iceberg lakehouse. It enables fast analytics queries across all data layers.

## Installation

```bash
pip install phlo-trino
# or
phlo plugin install trino
```

## Configuration

| Variable        | Default   | Description     |
| --------------- | --------- | --------------- |
| `TRINO_PORT`    | `8080`    | Trino HTTP port |
| `TRINO_VERSION` | `467`     | Trino version   |
| `TRINO_HOST`    | `trino`   | Trino hostname  |
| `TRINO_CATALOG` | `iceberg` | Default catalog |

## Features

### Auto-Configuration

| Feature                 | How It Works                                                                 |
| ----------------------- | ---------------------------------------------------------------------------- |
| **Catalog Discovery**   | Auto-generates catalog files from `phlo.plugins.trino_catalogs` entry points |
| **Metrics Labels**      | Exposes Trino metrics for Prometheus                                         |
| **Grafana Datasource**  | Auto-registers as Grafana datasource via labels                              |
| **Superset Connection** | Auto-registered in Superset via Superset hook                                |

### Catalog Generation

Trino catalog `.properties` files are generated from installed catalog plugins:

```python
from phlo_trino.catalog_generator import generate_catalog_files

# Discovers all TrinoCatalogPlugin instances and generates files
generate_catalog_files("/path/to/trino/catalog/")
```

### Default Catalogs

| Catalog       | Description                              |
| ------------- | ---------------------------------------- |
| `iceberg`     | Main Iceberg catalog (main branch)       |
| `iceberg_dev` | Development Iceberg catalog (dev branch) |
| `postgres`    | PostgreSQL connection for marts          |

## Usage

### Starting the Service

```bash
# Start Trino
phlo services start --service trino

# Start with all dependencies
phlo services start
```

### CLI Queries

```bash
# Run SQL query
phlo trino query "SELECT * FROM iceberg.bronze.users LIMIT 10"

# Interactive shell
docker exec -it phlo-trino-1 trino
```

### SQL Examples

```sql
-- Query bronze layer
SELECT * FROM iceberg.bronze.users LIMIT 10;

-- Query from dev branch
SELECT * FROM iceberg_dev.bronze.users LIMIT 10;

-- Time travel query
SELECT * FROM iceberg.bronze.users FOR VERSION AS OF 123456789;

-- Cross-schema join
SELECT
    u.id,
    u.name,
    e.event_count
FROM iceberg.silver.users u
JOIN iceberg.gold.user_events e ON u.id = e.user_id;

-- Query PostgreSQL marts
SELECT * FROM postgres.public.mrt_daily_summary;
```

### Programmatic Access

```python
from trino.dbapi import connect

conn = connect(
    host="localhost",
    port=8080,
    user="phlo",
    catalog="iceberg",
    schema="bronze"
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM users LIMIT 10")
results = cursor.fetchall()
```

## Endpoints

| Endpoint     | URL                             |
| ------------ | ------------------------------- |
| **HTTP API** | `http://localhost:8080`         |
| **Web UI**   | `http://localhost:8080/ui`      |
| **Metrics**  | `http://localhost:8080/v1/info` |

## Grafana Integration

Trino is automatically registered as a Grafana datasource:

```yaml
compose:
  labels:
    phlo.grafana.datasource: "true"
    phlo.grafana.datasource.type: "trino"
    phlo.grafana.datasource.name: "Trino"
```

## Entry Points

| Entry Point             | Plugin               |
| ----------------------- | -------------------- |
| `phlo.plugins.services` | `TrinoServicePlugin` |

## Related Packages

- [phlo-iceberg](phlo-iceberg.md) - Table format
- [phlo-nessie](phlo-nessie.md) - Catalog service
- [phlo-postgres](phlo-postgres.md) - Marts storage
- [phlo-grafana](phlo-grafana.md) - Visualization

## Next Steps

- [DuckDB Queries](../reference/duckdb-queries.md) - Ad-hoc analysis
- [API Reference](../reference/api.md) - REST/GraphQL access
- [dbt Development](../guides/dbt-development.md) - SQL transformations

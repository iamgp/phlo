# phlo-trino

Trino distributed SQL query engine for Phlo.

## Description

Trino query engine for querying the Iceberg lakehouse. Provides SQL access to all lakehouse tables.

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

## Auto-Configuration

This package is **fully auto-configured**:

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

### Grafana Labels

```yaml
compose:
  labels:
    phlo.grafana.datasource: "true"
    phlo.grafana.datasource.type: "trino"
    phlo.grafana.datasource.name: "Trino"
```

## Usage

```bash
# Start Trino
phlo services start --service trino

# Query via CLI
phlo trino query "SELECT * FROM iceberg.bronze.users LIMIT 10"
```

## Endpoints

- **HTTP API**: `http://localhost:8080`
- **Trino UI**: `http://localhost:8080/ui`

## Entry Points

- `phlo.plugins.services` - Provides `TrinoServicePlugin`
- `phlo.plugins.resources` - Provides `TrinoResourceProvider`

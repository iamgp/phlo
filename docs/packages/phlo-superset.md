# phlo-superset

Apache Superset BI service for Phlo.

## Overview

`phlo-superset` provides a business intelligence and data visualization platform. It connects to Trino to query the lakehouse data.

## Installation

```bash
pip install phlo-superset
# or
phlo plugin install superset
```

## Configuration

| Variable                  | Default             | Description            |
| ------------------------- | ------------------- | ---------------------- |
| `SUPERSET_PORT`           | `8088`              | Superset web UI port   |
| `SUPERSET_VERSION`        | `4.0.0`             | Superset version       |
| `SUPERSET_SECRET_KEY`     | auto-generated      | Session encryption key |
| `SUPERSET_ADMIN_USER`     | `admin`             | Admin username         |
| `SUPERSET_ADMIN_PASSWORD` | `admin`             | Admin password         |
| `SUPERSET_ADMIN_EMAIL`    | `admin@example.com` | Admin email            |

## Features

### Auto-Configuration

| Feature            | How It Works                                   |
| ------------------ | ---------------------------------------------- |
| **Trino Database** | Auto-registered on startup via post_start hook |
| **Metrics Labels** | Exposes health endpoint for Prometheus         |
| **Admin User**     | Auto-created on first startup                  |

### Post-Start Hook

```yaml
hooks:
  post_start:
    - name: add-trino-database
      command: python -m phlo_superset.hooks add-database
```

### Pre-Configured Databases

| Database           | Connection                                  |
| ------------------ | ------------------------------------------- |
| Trino (Iceberg)    | `trino://trino:8080/iceberg`                |
| PostgreSQL (Marts) | `postgresql://phlo:phlo@postgres:5432/phlo` |

## Usage

### Starting the Service

```bash
# Start Superset
phlo services start --service superset
```

### Accessing Superset

Open `http://localhost:8088` in your browser:

- Username: `admin`
- Password: `admin`

### Creating Dashboards

1. **Add a Dataset**

   - Navigate to Data → Datasets
   - Select the Trino database
   - Choose a table

2. **Create a Chart**

   - Navigate to Charts → New Chart
   - Select your dataset
   - Build your visualization

3. **Build a Dashboard**
   - Navigate to Dashboards → New Dashboard
   - Add your charts
   - Arrange and save

### SQL Lab

Use SQL Lab for ad-hoc queries:

1. Navigate to SQL → SQL Lab
2. Select a database (Trino or PostgreSQL)
3. Write and execute SQL queries
4. Save queries and export results

## Endpoints

| Endpoint   | URL                     |
| ---------- | ----------------------- |
| **Web UI** | `http://localhost:8088` |
| **Login**  | admin / admin           |

## Entry Points

| Entry Point             | Plugin                  |
| ----------------------- | ----------------------- |
| `phlo.plugins.services` | `SupersetServicePlugin` |

## Related Packages

- [phlo-trino](phlo-trino.md) - Query engine
- [phlo-postgres](phlo-postgres.md) - Marts storage
- [phlo-grafana](phlo-grafana.md) - Metrics visualization

## Next Steps

- [Installation Guide](../getting-started/installation.md) - Complete setup
- [dbt Development](../guides/dbt-development.md) - Create mart tables

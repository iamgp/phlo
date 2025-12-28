# phlo-superset

Apache Superset BI service for Phlo.

## Description

Business intelligence and data visualization platform. Connects to Trino to query the lakehouse data.

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

## Auto-Configuration

This package is **fully auto-configured**:

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

## Usage

```bash
# Start Superset
phlo services start --service superset
```

## Endpoints

- **Web UI**: `http://localhost:8088`
- **Login**: admin / admin

## Entry Points

- `phlo.plugins.services` - Provides `SupersetServicePlugin`

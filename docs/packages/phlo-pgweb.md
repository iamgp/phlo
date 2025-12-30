# phlo-pgweb

pgweb database browser for Phlo.

## Overview

`phlo-pgweb` provides a web-based PostgreSQL database browser for exploring metadata, lineage store, and operational data.

## Installation

```bash
pip install phlo-pgweb
# or
phlo plugin install pgweb
```

## Configuration

| Variable            | Default | Description       |
| ------------------- | ------- | ----------------- |
| `PGWEB_PORT`        | `8081`  | Web UI port       |
| `POSTGRES_USER`     | `phlo`  | Database user     |
| `POSTGRES_PASSWORD` | `phlo`  | Database password |
| `POSTGRES_DB`       | `phlo`  | Database name     |

## Features

### Auto-Configuration

| Feature                  | How It Works                                            |
| ------------------------ | ------------------------------------------------------- |
| **Database Connection**  | Auto-connects to Phlo's PostgreSQL using `DATABASE_URL` |
| **Service Dependencies** | Depends on `postgres` service                           |

## Usage

### Starting the Service

```bash
phlo services start --service pgweb
```

### Accessing pgweb

Open `http://localhost:8081` in your browser.

### Features

- **Query Editor**: Write and execute SQL queries
- **Table Browser**: Explore tables and columns
- **Data Export**: Export query results to CSV
- **Connection Info**: View database connection details
- **Table Statistics**: View row counts and sizes

## Dependencies

- postgres

## Endpoints

| Endpoint   | URL                     |
| ---------- | ----------------------- |
| **Web UI** | `http://localhost:8081` |

## Entry Points

| Entry Point             | Plugin               |
| ----------------------- | -------------------- |
| `phlo.plugins.services` | `PgwebServicePlugin` |

## Related Packages

- [phlo-postgres](phlo-postgres.md) - Database service
- [phlo-postgrest](phlo-postgrest.md) - REST API

## Next Steps

- [Installation Guide](../getting-started/installation.md) - Complete setup

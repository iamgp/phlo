# phlo-postgres

PostgreSQL database service for Phlo.

## Overview

`phlo-postgres` provides the core PostgreSQL database for metadata storage, lineage tracking, and operational data. It includes an optional Prometheus exporter for database metrics.

## Installation

```bash
pip install phlo-postgres
# or
phlo plugin install postgres
```

## Configuration

| Variable                 | Default  | Description            |
| ------------------------ | -------- | ---------------------- |
| `POSTGRES_PORT`          | `5432`   | PostgreSQL port        |
| `POSTGRES_USER`          | `phlo`   | Database username      |
| `POSTGRES_PASSWORD`      | `phlo`   | Database password      |
| `POSTGRES_DB`            | `phlo`   | Database name          |
| `POSTGRES_SSL_MODE`      | `prefer` | SSL mode               |
| `POSTGRES_EXPORTER_PORT` | `9187`   | Postgres exporter port |

## Features

### Auto-Configuration

| Feature                | How It Works                                               |
| ---------------------- | ---------------------------------------------------------- |
| **Grafana Datasource** | Auto-registers as Grafana datasource via labels            |
| **postgres-exporter**  | Optional Prometheus exporter for native PostgreSQL metrics |
| **Service Discovery**  | Exporter auto-scraped by Prometheus                        |

### Databases Created

| Database       | Purpose                           |
| -------------- | --------------------------------- |
| `phlo`         | Main application database         |
| `dagster`      | Dagster metadata storage          |
| `nessie`       | Nessie version store              |
| `openmetadata` | OpenMetadata catalog (if enabled) |

## Usage

### Starting the Service

```bash
# Start PostgreSQL
phlo services start --service postgres

# Start with exporter (for observability)
phlo services start --service postgres,postgres-exporter
```

### Connecting

```bash
# Via psql
psql -h localhost -p 5432 -U phlo -d phlo

# Via Docker
docker exec -it phlo-postgres-1 psql -U phlo
```

### SQLAlchemy Connection

```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://phlo:phlo@localhost:5432/phlo"
)

with engine.connect() as conn:
    result = conn.execute("SELECT * FROM marts.daily_summary")
```

### Using with Phlo Config

```python
from phlo.config import get_settings

settings = get_settings()
conn_string = settings.get_postgres_connection_string()

# Use connection string with SQLAlchemy, psycopg2, etc.
```

## Marts Schema

Gold layer data is published to the `marts` schema:

```sql
-- Query marts
SELECT * FROM marts.mrt_daily_summary;
SELECT * FROM marts.mrt_user_metrics;
```

## Endpoints

| Endpoint             | URL                             |
| -------------------- | ------------------------------- |
| **PostgreSQL**       | `localhost:5432`                |
| **Exporter Metrics** | `http://localhost:9187/metrics` |

## Grafana Integration

PostgreSQL is automatically registered as a Grafana datasource:

```yaml
compose:
  labels:
    phlo.grafana.datasource: "true"
    phlo.grafana.datasource.type: "postgres"
    phlo.grafana.datasource.name: "PostgreSQL"
```

## Entry Points

| Entry Point             | Plugin                                                   |
| ----------------------- | -------------------------------------------------------- |
| `phlo.plugins.services` | `PostgresServicePlugin`, `PostgresExporterServicePlugin` |

## Related Packages

- [phlo-postgrest](phlo-postgrest.md) - REST API
- [phlo-hasura](phlo-hasura.md) - GraphQL API
- [phlo-grafana](phlo-grafana.md) - Visualization
- [phlo-dagster](phlo-dagster.md) - Orchestration

## Next Steps

- [PostgREST Setup](../setup/postgrest.md) - REST API generation
- [Hasura Setup](../setup/hasura.md) - GraphQL API
- [API Reference](../reference/phlo-api.md) - Data access

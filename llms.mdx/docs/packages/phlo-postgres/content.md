# phlo-postgres (/docs/packages/phlo-postgres)



Overview [#overview]

`phlo-postgres` provides the core PostgreSQL database for metadata storage, lineage tracking, and operational data. It includes an optional Prometheus exporter for database metrics.

It also acts as a structured publish target for serving tables produced from the
analytical plane.

Installation [#installation]

```bash
pip install phlo-postgres
# or
phlo plugin install postgres
```

Configuration [#configuration]

| Variable                 | Default  | Description            |
| ------------------------ | -------- | ---------------------- |
| `POSTGRES_PORT`          | `5432`   | PostgreSQL port        |
| `POSTGRES_USER`          | `phlo`   | Database username      |
| `POSTGRES_PASSWORD`      | `phlo`   | Database password      |
| `POSTGRES_DB`            | `phlo`   | Database name          |
| `POSTGRES_SSL_MODE`      | `prefer` | SSL mode               |
| `POSTGRES_EXPORTER_PORT` | `9187`   | Postgres exporter port |

Features [#features]

Auto-Configuration [#auto-configuration]

| Feature                | How It Works                                               |
| ---------------------- | ---------------------------------------------------------- |
| **Grafana Datasource** | Auto-registers as Grafana datasource via labels            |
| **postgres-exporter**  | Optional Prometheus exporter for native PostgreSQL metrics |
| **Service Discovery**  | Exporter auto-scraped by Prometheus                        |

Databases Created [#databases-created]

| Database       | Purpose                           |
| -------------- | --------------------------------- |
| `phlo`         | Main application database         |
| `dagster`      | Dagster metadata storage          |
| `nessie`       | Nessie version store              |
| `openmetadata` | OpenMetadata catalog (if enabled) |

Usage [#usage]

Starting the Service [#starting-the-service]

```bash
# Start PostgreSQL
phlo services start --service postgres

# Start with exporter (for observability)
phlo services start --service postgres,postgres-exporter
```

Connecting [#connecting]

```bash
# Interactive psql shell
phlo postgres

# Open a specific database
phlo postgres --dbname phlo

# Non-interactive query
phlo postgres query "SELECT current_database()"

# Logical backup
phlo postgres dump --file backups/phlo.sql.gz

# Restore from backup
phlo postgres restore --file backups/phlo.sql.gz

# Vacuum and analyze tables
phlo postgres vacuum --analyze
```

SQLAlchemy Connection [#sqlalchemy-connection]

```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://phlo:phlo@localhost:5432/phlo"
)

with engine.connect() as conn:
    result = conn.execute("SELECT * FROM marts.daily_summary")
```

Using with Phlo Config [#using-with-phlo-config]

```python
from phlo_postgres.settings import get_settings

settings = get_settings()
conn_string = settings.get_postgres_connection_string()

# Use connection string with SQLAlchemy, psycopg2, etc.
```

Marts Schema [#marts-schema]

Gold layer data is published to the `marts` schema:

```sql
-- Query marts
SELECT * FROM marts.mrt_daily_summary;
SELECT * FROM marts.mrt_user_metrics;
```

Publish Target Role [#publish-target-role]

Within capability-native Phlo profiles, Postgres is a publish target, not a
parallel transformation plane.

Typical flow:

`DLT -> table store -> query engine/dbt -> publish target`

That means:

* transforms build on the analytical table store
* selected marts are copied into Postgres explicitly
* serving tables stay downstream of the lakehouse contract

Endpoints [#endpoints]

| Endpoint             | URL                             |
| -------------------- | ------------------------------- |
| **PostgreSQL**       | `localhost:5432`                |
| **Exporter Metrics** | `http://localhost:9187/metrics` |

Grafana Integration [#grafana-integration]

PostgreSQL is automatically registered as a Grafana datasource:

```yaml
compose:
  labels:
    phlo.grafana.datasource: "true"
    phlo.grafana.datasource.type: "postgres"
    phlo.grafana.datasource.name: "PostgreSQL"
```

Entry Points [#entry-points]

| Entry Point                       | Plugin                                                                                       |
| --------------------------------- | -------------------------------------------------------------------------------------------- |
| `phlo.plugins.services`           | `PostgresServicePlugin`, `PostgresExporterServicePlugin`, `PostgresVolumeSetupServicePlugin` |
| `phlo.plugins.resource_providers` | `PostgresResourceProvider`                                                                   |

Related Packages [#related-packages]

* [phlo-postgrest](phlo-postgrest.md) - REST API
* [phlo-hasura](phlo-hasura.md) - GraphQL API
* [phlo-grafana](phlo-grafana.md) - Visualization
* [phlo-dagster](phlo-dagster.md) - Orchestration

Next Steps [#next-steps]

* [PostgREST Setup](../setup/postgrest.md) - REST API generation
* [Hasura Setup](../setup/hasura.md) - GraphQL API
* [API Reference](../reference/phlo-api.md) - Data access

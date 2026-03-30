# phlo-pgweb (/docs/packages/phlo-pgweb)



Overview [#overview]

`phlo-pgweb` provides a web-based PostgreSQL database browser for exploring metadata, lineage store, and operational data.

Installation [#installation]

```bash
pip install phlo-pgweb
# or
phlo plugin install pgweb
```

Configuration [#configuration]

| Variable            | Default | Description       |
| ------------------- | ------- | ----------------- |
| `PGWEB_PORT`        | `8081`  | Web UI port       |
| `POSTGRES_USER`     | `phlo`  | Database user     |
| `POSTGRES_PASSWORD` | `phlo`  | Database password |
| `POSTGRES_DB`       | `phlo`  | Database name     |

Features [#features]

Auto-Configuration [#auto-configuration]

| Feature                  | How It Works                                            |
| ------------------------ | ------------------------------------------------------- |
| **Database Connection**  | Auto-connects to Phlo's PostgreSQL using `DATABASE_URL` |
| **Service Dependencies** | Depends on `postgres` service                           |

Usage [#usage]

Starting the Service [#starting-the-service]

```bash
phlo services start --service pgweb
```

Accessing pgweb [#accessing-pgweb]

Open `http://localhost:8081` in your browser.

Features [#features-1]

* **Query Editor**: Write and execute SQL queries
* **Table Browser**: Explore tables and columns
* **Data Export**: Export query results to CSV
* **Connection Info**: View database connection details
* **Table Statistics**: View row counts and sizes

Dependencies [#dependencies]

* postgres

Endpoints [#endpoints]

| Endpoint   | URL                     |
| ---------- | ----------------------- |
| **Web UI** | `http://localhost:8081` |

Entry Points [#entry-points]

| Entry Point             | Plugin               |
| ----------------------- | -------------------- |
| `phlo.plugins.services` | `PgwebServicePlugin` |

Related Packages [#related-packages]

* [phlo-postgres](phlo-postgres.md) - Database service
* [phlo-postgrest](phlo-postgrest.md) - REST API

Next Steps [#next-steps]

* [Installation Guide](../getting-started/installation.md) - Complete setup

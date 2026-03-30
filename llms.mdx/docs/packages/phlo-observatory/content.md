# phlo-observatory (/docs/packages/phlo-observatory)



Overview [#overview]

`phlo-observatory` is a web-based UI for exploring the data lakehouse. It enables viewing lineage, browsing tables, running queries, and monitoring pipeline health.

Installation [#installation]

```bash
pip install phlo-observatory
# or
phlo plugin install observatory
```

Configuration [#configuration]

Observatory configuration is primarily managed through the service definition (`service.yaml`). The following environment variables are used by the Observatory container:

| Variable              | Default                       | Description                         |
| --------------------- | ----------------------------- | ----------------------------------- |
| `OBSERVATORY_PORT`    | `3001`                        | Observatory web UI port (container) |
| `DAGSTER_GRAPHQL_URL` | `http://dagster:3000/graphql` | Dagster GraphQL endpoint            |
| `NESSIE_URL`          | `http://nessie:19120/api/v2`  | Nessie API URL                      |
| `TRINO_URL`           | `http://trino:8080`           | Trino HTTP URL                      |
| `PHLO_API_URL`        | `http://phlo-api:4000`        | Phlo API URL                        |

For persistent settings storage:

| Variable                           | Default | Description                         |
| ---------------------------------- | ------- | ----------------------------------- |
| `PHLO_OBSERVATORY_SETTINGS_DB_URL` | -       | PostgreSQL DSN for settings storage |

Features [#features]

Core Capabilities [#core-capabilities]

| Feature               | Description                                    |
| --------------------- | ---------------------------------------------- |
| **Data Explorer**     | Browse tables, view schemas, preview data      |
| **Lineage Graph**     | Interactive visualization of data flow         |
| **Asset Browser**     | View Dagster assets and materialization status |
| **Quality Dashboard** | Monitor quality check results                  |
| **Branch Management** | Create, view, and merge Nessie branches        |
| **SQL Workbench**     | Execute ad-hoc queries against Trino           |

Auto-Configuration [#auto-configuration]

| Feature            | How It Works                               |
| ------------------ | ------------------------------------------ |
| **API Connection** | Connects to phlo-api for backend data      |
| **Service URLs**   | Auto-configured from environment variables |
| **Dev Mode**       | Hot-reloading in `--dev` mode              |

Usage [#usage]

Starting the Service [#starting-the-service]

```bash
# Start Observatory
phlo services start --service observatory

# Start with native mode (better for ARM Macs)
phlo services start --native

# Start with dev mode (hot-reload)
phlo services start --dev
```

Accessing the UI [#accessing-the-ui]

Open `http://localhost:3001` in your browser.

UI Sections [#ui-sections]

Data Explorer [#data-explorer]

Browse and explore your data lakehouse:

* View all schemas and tables
* Inspect table schemas and statistics
* Preview data with pagination
* Export query results

Lineage Graph [#lineage-graph]

Visualize data dependencies:

* Interactive node-based graph
* Click tables to see details
* Filter by upstream/downstream
* Highlight specific paths

Asset Browser [#asset-browser]

Monitor Dagster assets:

* View materialization status
* See last run timestamps
* Check freshness policies
* Trigger materializations

Quality Dashboard [#quality-dashboard]

Track data quality:

* View check results over time
* Filter by status (pass/fail)
* Drill into failure details
* See violation samples

Branch Manager [#branch-manager]

Work with Nessie branches:

* List all branches
* Create new branches
* Compare branches
* Merge branches

SQL Workbench [#sql-workbench]

Run ad-hoc queries:

* Syntax highlighting
* Auto-complete for tables
* Result pagination
* Export to CSV

Endpoints [#endpoints]

| Endpoint   | URL                     |
| ---------- | ----------------------- |
| **Web UI** | `http://localhost:3001` |

Entry Points [#entry-points]

| Entry Point             | Plugin                     |
| ----------------------- | -------------------------- |
| `phlo.plugins.services` | `ObservatoryServicePlugin` |

Related Packages [#related-packages]

* [phlo-api](phlo-api.md) - Backend API
* [phlo-lineage](phlo-lineage.md) - Lineage data
* [phlo-pandera](phlo-pandera.md) - Quality checks
* [phlo-nessie](phlo-nessie.md) - Branch management

Next Steps [#next-steps]

* [Installation Guide](../getting-started/installation.md) - Complete setup
* [Quickstart](../getting-started/quickstart.md) - First steps
* [Troubleshooting](../operations/troubleshooting.md) - Debug issues

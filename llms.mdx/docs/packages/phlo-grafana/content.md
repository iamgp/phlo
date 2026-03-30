# phlo-grafana (/docs/packages/phlo-grafana)



Overview [#overview]

`phlo-grafana` provides metrics visualization and dashboards for observability. It comes pre-configured with datasources for Prometheus, Loki, Trino, and PostgreSQL.

Installation [#installation]

```bash
pip install phlo-grafana
# or
phlo plugin install grafana
```

Profile [#profile]

Part of the `observability` profile.

Configuration [#configuration]

| Variable                          | Default    | Description                                                     |
| --------------------------------- | ---------- | --------------------------------------------------------------- |
| `GRAFANA_PORT`                    | `3003`     | Grafana web UI port                                             |
| `GRAFANA_VERSION`                 | `11.3.1`   | Grafana version                                                 |
| `GRAFANA_ADMIN_USER`              | `admin`    | Admin username                                                  |
| `GRAFANA_ADMIN_PASSWORD`          | `admin`    | Admin password                                                  |
| `GRAFANA_PUBLIC_URL`              | -          | Public Grafana base URL used by observability links             |
| `GRAFANA_DASHBOARD_PATH_TEMPLATE` | `/d/{uid}` | Dashboard path template used to build links from dashboard UIDs |

Features [#features]

Auto-Configuration [#auto-configuration]

| Feature            | How It Works                                         |
| ------------------ | ---------------------------------------------------- |
| **Datasources**    | Pre-provisioned: Prometheus, Loki, Trino, PostgreSQL |
| **Dashboards**     | Pre-provisioned dashboards in `grafana/dashboards/`  |
| **Metrics Labels** | Exposes Grafana metrics for Prometheus               |

Pre-Configured Datasources [#pre-configured-datasources]

| Datasource | Type       | URL                                              |
| ---------- | ---------- | ------------------------------------------------ |
| Prometheus | prometheus | [http://prometheus:9090](http://prometheus:9090) |
| Loki       | loki       | [http://loki:3100](http://loki:3100)             |
| Trino      | trino      | [http://trino:8080](http://trino:8080)           |
| PostgreSQL | postgres   | postgres:5432                                    |

Pre-Built Dashboards [#pre-built-dashboards]

| Dashboard         | Description                |
| ----------------- | -------------------------- |
| Phlo Overview     | High-level system health   |
| Dagster Pipelines | Pipeline execution metrics |
| Data Quality      | Quality check results      |
| Trino Queries     | Query performance          |
| MinIO Storage     | Storage utilization        |

Usage [#usage]

Starting the Service [#starting-the-service]

```bash
# Start with observability profile
phlo services start --profile observability

# Or start individually
phlo services start --service grafana
```

Access [#access]

* **URL**: `http://localhost:3003`
* **Username**: `admin`
* **Password**: `admin`

Creating Dashboards [#creating-dashboards]

1. Login to Grafana
2. Navigate to Dashboards → New Dashboard
3. Add panels with queries to your datasources
4. Save and export JSON

Alerting [#alerting]

Configure alerts in Grafana:

1. Edit a panel
2. Go to Alert tab
3. Configure conditions
4. Add notification channels

Endpoints [#endpoints]

| Endpoint    | URL                             |
| ----------- | ------------------------------- |
| **Web UI**  | `http://localhost:3003`         |
| **API**     | `http://localhost:3003/api`     |
| **Metrics** | `http://localhost:3003/metrics` |

Entry Points [#entry-points]

| Entry Point             | Plugin                 |
| ----------------------- | ---------------------- |
| `phlo.plugins.services` | `GrafanaServicePlugin` |

Related Packages [#related-packages]

* [phlo-prometheus](phlo-prometheus.md) - Metrics collection
* [phlo-loki](phlo-loki.md) - Log aggregation
* [phlo-alerting](phlo-alerting.md) - Alert management

Next Steps [#next-steps]

* [Observability Setup](../setup/observability.md) - Complete monitoring setup
* [Operations Guide](../operations/operations-guide.md) - Monitoring best practices
* [Troubleshooting](../operations/troubleshooting.md) - Debug issues

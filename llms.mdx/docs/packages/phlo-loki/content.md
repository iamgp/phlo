# phlo-loki (/docs/packages/phlo-loki)



Overview [#overview]

`phlo-loki` provides centralized log aggregation for the Phlo observability stack. It collects logs from all services and makes them queryable via Grafana.

Installation [#installation]

```bash
pip install phlo-loki
# or
phlo plugin install loki
```

Profile [#profile]

Part of the `observability` profile.

Configuration [#configuration]

| Variable              | Default | Description                                      |
| --------------------- | ------- | ------------------------------------------------ |
| `LOKI_PORT`           | `3100`  | Loki API port                                    |
| `LOKI_RETENTION_DAYS` | `7`     | Log retention period                             |
| `LOKI_PUBLIC_URL`     | -       | Public Loki base URL used by observability links |
| `LOKI_LOGS_PATH`      | `/logs` | Path used for generated log query links          |

Features [#features]

Auto-Configuration [#auto-configuration]

| Feature                 | How It Works                                   |
| ----------------------- | ---------------------------------------------- |
| **Log Collection**      | All Docker container logs collected via Alloy  |
| **Label Enrichment**    | Auto-labels with service name, container, etc. |
| **Grafana Integration** | Pre-configured as Grafana datasource           |

Usage [#usage]

Starting the Service [#starting-the-service]

```bash
# Start with observability profile
phlo services start --profile observability

# Or start individually
phlo services start --service loki
```

Querying Logs [#querying-logs]

Access logs via Grafana's Explore view:

```text
# All Dagster logs
{service="dagster"}

# Error logs from any service
{} |= "error"

# Pipeline-specific logs
{service="dagster"} |~ "pipeline.*run"

# Logs with JSON parsing
{service="dagster"} | json | level="ERROR"
```

Log Labels [#log-labels]

Logs are labeled with:

| Label       | Description                         |
| ----------- | ----------------------------------- |
| `service`   | Service name (dagster, trino, etc.) |
| `container` | Container name                      |
| `level`     | Log level (INFO, ERROR, etc.)       |
| `job`       | Job/pipeline name                   |

Endpoints [#endpoints]

| Endpoint  | URL                                       |
| --------- | ----------------------------------------- |
| **API**   | `http://localhost:3100`                   |
| **Push**  | `http://localhost:3100/loki/api/v1/push`  |
| **Query** | `http://localhost:3100/loki/api/v1/query` |

Entry Points [#entry-points]

| Entry Point             | Plugin              |
| ----------------------- | ------------------- |
| `phlo.plugins.services` | `LokiServicePlugin` |

Related Packages [#related-packages]

* [phlo-grafana](phlo-grafana.md) - Visualization
* [phlo-alloy](phlo-alloy.md) - Log shipping
* [phlo-prometheus](phlo-prometheus.md) - Metrics

Next Steps [#next-steps]

* [Observability Setup](../setup/observability.md) - Complete monitoring setup
* [Troubleshooting Guide](../operations/troubleshooting.md) - Debug with logs

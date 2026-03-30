# phlo-prometheus (/docs/packages/phlo-prometheus)



Overview [#overview]

`phlo-prometheus` provides metrics collection and alerting for the Phlo observability stack. It auto-discovers and scrapes metrics from all Phlo services.

Installation [#installation]

```bash
pip install phlo-prometheus
# or
phlo plugin install prometheus
```

Profile [#profile]

Part of the `observability` profile.

Configuration [#configuration]

| Variable                     | Default  | Description                                            |
| ---------------------------- | -------- | ------------------------------------------------------ |
| `PROMETHEUS_PORT`            | `9090`   | Prometheus web UI port                                 |
| `PROMETHEUS_RETENTION_TIME`  | `15d`    | Metrics retention period                               |
| `PROMETHEUS_SCRAPE_INTERVAL` | `15s`    | Default scrape interval                                |
| `PROMETHEUS_PUBLIC_URL`      | -        | Public Prometheus base URL used by observability links |
| `PROMETHEUS_QUERY_PATH`      | `/graph` | Path used for generated metric query links             |

Features [#features]

Auto-Configuration [#auto-configuration]

| Feature               | How It Works                                       |
| --------------------- | -------------------------------------------------- |
| **Service Discovery** | Auto-discovers metrics endpoints via Docker labels |
| **Scrape Configs**    | Pre-configured for all Phlo services               |
| **Alerting Rules**    | Pre-configured alerting rules for common issues    |

Auto-Discovered Services [#auto-discovered-services]

Services with the following labels are automatically scraped:

```yaml
labels:
  phlo.metrics.enabled: "true"
  phlo.metrics.port: "8080"
  phlo.metrics.path: "/metrics"
```

Default Scrape Targets [#default-scrape-targets]

| Target              | Endpoint                              |
| ------------------- | ------------------------------------- |
| Dagster             | `dagster:3000/metrics`                |
| Trino               | `trino:8080/v1/info`                  |
| MinIO               | `minio:9000/minio/v2/metrics/cluster` |
| Nessie              | `nessie:19120/q/metrics`              |
| PostgreSQL Exporter | `postgres-exporter:9187/metrics`      |

Usage [#usage]

Starting the Service [#starting-the-service]

```bash
# Start with observability profile
phlo services start --profile observability

# Or start individually
phlo services start --service prometheus
```

Querying Metrics [#querying-metrics]

Access the Prometheus UI at `http://localhost:9090`:

```text
# Dagster run count
dagster_runs_total

# Trino query count
trino_running_queries

# MinIO storage used
minio_bucket_usage_total_bytes

# Pipeline latency
histogram_quantile(0.95, dagster_run_duration_seconds_bucket)
```

Recording Rules [#recording-rules]

Common aggregations are pre-computed:

```yaml
groups:
  - name: phlo_aggregations
    rules:
      - record: phlo:pipeline_success_rate:5m
        expr: rate(dagster_runs_total{status="success"}[5m]) / rate(dagster_runs_total[5m])
```

Alerting Rules [#alerting-rules]

Pre-configured alerts:

| Alert              | Condition                    |
| ------------------ | ---------------------------- |
| `PhloServiceDown`  | Service unreachable for > 5m |
| `PipelineFailures` | > 3 pipeline failures in 1h  |
| `HighQueryLatency` | P95 query latency > 30s      |
| `StorageNearFull`  | Storage usage > 80%          |

Endpoints [#endpoints]

| Endpoint    | URL                             |
| ----------- | ------------------------------- |
| **Web UI**  | `http://localhost:9090`         |
| **API**     | `http://localhost:9090/api/v1`  |
| **Metrics** | `http://localhost:9090/metrics` |

Entry Points [#entry-points]

| Entry Point             | Plugin                    |
| ----------------------- | ------------------------- |
| `phlo.plugins.services` | `PrometheusServicePlugin` |

Related Packages [#related-packages]

* [phlo-grafana](phlo-grafana.md) - Visualization
* [phlo-alerting](phlo-alerting.md) - Alert routing
* [phlo-loki](phlo-loki.md) - Log aggregation

Next Steps [#next-steps]

* [Observability Setup](../setup/observability.md) - Complete monitoring setup
* [Operations Guide](../operations/operations-guide.md) - Monitoring best practices

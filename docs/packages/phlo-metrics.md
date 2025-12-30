# phlo-metrics

Metrics collection and export for Phlo pipelines.

## Overview

`phlo-metrics` collects metrics from pipeline executions, quality checks, and system events. It exports to Prometheus format for scraping.

## Installation

```bash
pip install phlo-metrics
# or
phlo plugin install metrics
```

## Configuration

| Variable                     | Default | Description              |
| ---------------------------- | ------- | ------------------------ |
| `PROMETHEUS_PUSHGATEWAY_URL` | -       | Optional pushgateway URL |

## Features

### Auto-Configuration

Auto-wires with HookBus for event collection:

| Feature               | How It Works                                    |
| --------------------- | ----------------------------------------------- |
| **Hook Registration** | Receives all events via HookBus                 |
| **Metric Collection** | Auto-increments counters and gauges from events |
| **Prometheus Format** | Exports in Prometheus text format               |

### Exposure

- **Default**: Metrics available via CLI (`phlo metrics show`) or export
- **With Pushgateway**: Set `PROMETHEUS_PUSHGATEWAY_URL` to push metrics to a gateway

### Collected Metrics

| Metric                      | Type      | Description             |
| --------------------------- | --------- | ----------------------- |
| `phlo_ingestion_total`      | Counter   | Total ingestion runs    |
| `phlo_ingestion_rows`       | Counter   | Rows ingested           |
| `phlo_ingestion_duration`   | Histogram | Ingestion duration      |
| `phlo_quality_checks_total` | Counter   | Quality checks executed |
| `phlo_quality_failures`     | Counter   | Failed quality checks   |
| `phlo_transform_total`      | Counter   | Transform executions    |
| `phlo_transform_duration`   | Histogram | Transform duration      |

## Usage

### CLI Commands

```bash
# View current metrics
phlo metrics show

# Export metrics to file
phlo metrics export --format prometheus > metrics.prom

# Reset metrics
phlo metrics reset
```

### Programmatic

```python
from phlo_metrics.collector import MetricsCollector

collector = MetricsCollector()

# Increment a counter
collector.increment("custom_metric", labels={"source": "api"})

# Set a gauge
collector.set_gauge("active_pipelines", 5)

# Record a histogram observation
collector.observe("request_duration", 0.5, labels={"endpoint": "/api/data"})
```

## Entry Points

| Entry Point          | Plugin                                 |
| -------------------- | -------------------------------------- |
| `phlo.plugins.cli`   | `metrics` CLI commands                 |
| `phlo.plugins.hooks` | `MetricsHookPlugin` for event handling |

## Related Packages

- [phlo-prometheus](phlo-prometheus.md) - Metrics storage
- [phlo-grafana](phlo-grafana.md) - Metrics visualization
- [phlo-alerting](phlo-alerting.md) - Alert routing

## Next Steps

- [Observability Setup](../setup/observability.md) - Monitoring setup
- [Operations Guide](../operations/operations-guide.md) - Metrics best practices

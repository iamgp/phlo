# phlo-metrics

Metrics collection and export for Phlo pipelines.

## Description

Collects metrics from pipeline executions, quality checks, and system events. Exports to Prometheus format for scraping.

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

## Auto-Configuration

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

| Metric                      | Type    | Description             |
| --------------------------- | ------- | ----------------------- |
| `phlo_ingestion_total`      | Counter | Total ingestion runs    |
| `phlo_ingestion_rows`       | Counter | Rows ingested           |
| `phlo_quality_checks_total` | Counter | Quality checks executed |
| `phlo_quality_failures`     | Counter | Failed quality checks   |

## Usage

### CLI Commands

```bash
# View current metrics
phlo metrics show

# Export metrics to file
phlo metrics export --format prometheus
```

### Programmatic

```python
from phlo_metrics.collector import MetricsCollector

collector = MetricsCollector()
collector.increment("custom_metric", labels={"source": "api"})
```

## Entry Points

- `phlo.plugins.cli` - Provides `metrics` CLI commands
- `phlo.plugins.hooks` - Provides `MetricsHookPlugin` for event handling

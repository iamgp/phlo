# Part 11: Observability and Monitoring—Knowing Your Pipeline

> Prerequisite: Complete [Part 7: Orchestration with Dagster](07-orchestration-dagster.md) to follow the monitoring flows.

## What You'll Learn

- How Phlo collects metrics, logs, and traces
- How to set alerting thresholds for pipeline health
- How to use Dagster and Observatory for incident response
- How observability connects to governance and quality

## Prerequisites

- [Part 7: Orchestration with Dagster](07-orchestration-dagster.md)
- Optional: [Part 10: Metadata and Governance](10-metadata-governance.md) for lineage context.

You've built a data lakehouse with validation and governance. But what happens at 3am when something breaks? This post covers observability: monitoring, alerting, and troubleshooting.
For custom UI extensions in the observability layer, see [Part 15: Observatory Extensions](15-observatory-extensions.md).

## The Observability Problem

Without proper monitoring, failures hide:

```
Tuesday 3am:
  • DLT fails to fetch from Nightscout API
  • Data stops flowing
  • Nobody notices

Wednesday 9am:
  • Users report: "Dashboard shows stale data"
  • Investigation: "Last update was 30 hours ago"
  • Impact: 500+ people using outdated metrics
  • Root cause: API timeout at 3:14am, log buried in Dagster logs
```

Observability solves this with:

```
[Monitoring] → Understand what's happening
[Alerting]   → Get notified of problems
[Tracing]    → Find root causes quickly
[Dashboards] → Visualize pipeline health
```

## Three Pillars of Observability

### 1. Metrics (Numbers)

Track quantitative data:

```
• Pipeline runtime: 5.2 seconds
• Data quality: 99.7% valid rows
• Row throughput: 12,500 rows/minute
• Freshness: 2 hours since last update
• API latency: 150ms average
```

### 2. Logs (Events)

Track what happened and when:

```
[2024-10-15 10:35:42] ✓ dlt_glucose_entries started
[2024-10-15 10:35:45] ✓ Fetched 487 rows from API
[2024-10-15 10:35:47] ✓ Pandera validation: 487/487 rows valid
[2024-10-15 10:35:49] ⚠ 2 rows with invalid device type (logged)
[2024-10-15 10:35:51] ✓ Merged to Iceberg (487 inserts, 2 updates)
[2024-10-15 10:35:53] ✓ dlt_glucose_entries succeeded
```

### 3. Traces (Flows)

Track execution paths:

```
Request: dlt_glucose_entries asset materialization
├─ Fetch from API (45ms)
│  ├─ Auth (5ms)
│  └─ Network (40ms)
├─ Pandera validation (12ms)
│  ├─ Type checking (8ms)
│  └─ Constraint checking (4ms)
├─ Merge to Iceberg (80ms)
│  ├─ Read current snapshot (20ms)
│  ├─ Merge operation (40ms)
│  └─ Write metadata (20ms)
└─ Asset check (15ms)

Total: 152ms
```

## Phlo's Observability Stack

```
┌──────────────────────────────┐
│  Application Layer           │
│  (Dagster, dbt, DLT)         │
└──────────────────────────────┘
            ↓ (emits events)
┌──────────────────────────────┐
│  Phlo CLI & Monitoring       │
│  • phlo logs                 │
│  • phlo metrics              │
│  • phlo lineage              │
│  • phlo alerts               │
└──────────────────────────────┘
            ↓
┌──────────────────────────────┐
│  Storage & Collection        │
│  • Dagster Event Log         │
│  • Metrics Collector         │
│  • Lineage Graph             │
└──────────────────────────────┘
            ↓
┌──────────────────────────────┐
│  Alerting & Notifications    │
│  • Slack Webhooks            │
│  • PagerDuty                 │
│  • Email                     │
└──────────────────────────────┘
```

## Metrics: Tracking Pipeline Health

Phlo provides built-in metrics collection through the `phlo metrics` CLI command and the metrics collector module.

### Viewing Metrics via CLI

The easiest way to check pipeline health:

```bash
# View overall pipeline metrics
$ phlo metrics summary

Platform Metrics Summary

Runs (last 24h)
  Total:     288
  Success:   285 (98.96%)
  Failure:   3 (1.04%)

Data Volume
  Rows:      1.2M
  Bytes:     450 MB

Latency (seconds)
  p50:       0.32s
  p95:       0.85s
  p99:       1.20s

Assets
  Active:    12
  Success:   11
  Warning:   0
  Failure:   1
```


For per-asset details:

```bash
# View metrics for specific asset
$ phlo metrics asset glucose_entries --runs 20

Metrics for glucose_entries
Metric              Value
─────────────────────────────────
Last Run Status     success
Last Run Duration   5.20s
Average Duration    5.10s
Failure Rate        5.0%
Avg Rows/Run        498
Data Size           2.5 MB

Last 20 Runs
Run ID    Status   Duration  Rows
─────────────────────────────────
abc123    success  5.2s      487
def456    success  4.8s      512
ghi789    success  5.1s      495
```


Export metrics for external analysis:

```bash
# Export to JSON
$ phlo metrics export --format json --period 7d --output metrics.json

# Export to CSV
$ phlo metrics export --format csv --period 30d --output metrics.csv
```


## Logs: Structured Logging

Use structured logs for easy searching:

```python
# workflows/ingestion/dlt_assets.py
import structlog

logger = structlog.get_logger()


@asset
def dlt_glucose_entries(context) -> None:
    """Ingest glucose entries with structured logging."""

    logger.info(
        "asset_started",
        asset_name="dlt_glucose_entries",
        timestamp=datetime.utcnow().isoformat(),
    )

    try:
        # Fetch API
        logger.info(
            "api_fetch_started",
            endpoint="https://api.nightscout.info/api/v1/entries",
            timeout_seconds=30,
        )

        response = fetch_from_api()

        logger.info(
            "api_fetch_success",
            rows_returned=len(response),
            response_time_ms=response.elapsed.total_seconds() * 1000,
        )

        # Validate
        logger.info(
            "validation_started",
            validator="pandera",
            schema="glucose_entries_v1",
        )

        validated = validate(response)
        invalid_count = len(response) - len(validated)

        logger.info(
            "validation_complete",
            total_rows=len(response),
            valid_rows=len(validated),
            invalid_rows=invalid_count,
            pass_rate=100.0 * len(validated) / len(response),
        )

        # Merge
        logger.info(
            "merge_started",
            table="raw.glucose_entries",
            rows_to_merge=len(validated),
            unique_key="_id",
        )

        result = merge_to_iceberg(validated)

        logger.info(
            "merge_complete",
            table="raw.glucose_entries",
            inserts=result["inserts"],
            updates=result["updates"],
            merge_time_ms=result["duration_ms"],
        )

        # Success
        logger.info(
            "asset_succeeded",
            asset_name="dlt_glucose_entries",
            total_time_ms=get_total_elapsed(),
        )

    except Exception as e:
        logger.exception(
            "asset_failed",
            asset_name="dlt_glucose_entries",
            error_type=type(e).__name__,
            error_message=str(e),
        )
        raise
```

In Grafana, search logs:

```
{job="dagster"} | json | asset_name="dlt_glucose_entries" | status="success"

Last 24 hours:
├─ 10/15 10:35 ✓ Succeeded in 152ms
├─ 10/15 10:30 ✓ Succeeded in 145ms
├─ 10/15 10:25 ✓ Succeeded in 168ms
├─ 10/15 10:20 ⚠ Succeeded in 1,240ms (slow)
└─ 10/15 10:15 ✓ Succeeded in 156ms
```

## Alerting: Getting Notified When Things Break

Phlo includes a built-in alerting system that can send notifications to Slack, PagerDuty, and email.

### Configuring Alert Destinations

Set up alert destinations via environment variables:

```bash
# Slack Integration
export PHLO_ALERT_SLACK_WEBHOOK="https://hooks.slack.com/services/T.../B.../xxx"
export PHLO_ALERT_SLACK_CHANNEL="#data-alerts"  # Optional

# PagerDuty Integration
export PHLO_ALERT_PAGERDUTY_KEY="your-integration-key"

# Email Integration
export PHLO_ALERT_EMAIL_SMTP_HOST="smtp.gmail.com"
export PHLO_ALERT_EMAIL_SMTP_PORT="587"
export PHLO_ALERT_EMAIL_SMTP_USER="alerts@yourcompany.com"
export PHLO_ALERT_EMAIL_SMTP_PASSWORD="your-password"
export PHLO_ALERT_EMAIL_RECIPIENTS="data-team@yourcompany.com,oncall@yourcompany.com"
```


### Managing Alerts via CLI

Check alert system status:

```bash
$ phlo alerts status

Alert System Status

Configured Destinations: 2
  • slack
  • email

Recent Alerts Sent: 5
Deduplication Window: 60 minutes
```


List configured destinations:

```bash
$ phlo alerts list

Configured Alert Destinations
Name   Type              Status
─────────────────────────────────
slack  SlackDestination  ✓ Ready
email  EmailDestination  ✓ Ready
```


Test your alert configuration:

```bash
# Send test alert to all destinations
$ phlo alerts test

✓ Test alert sent successfully! Check your configured alert destinations.

# Test specific destination
$ phlo alerts test --destination slack --severity critical
```


### What Triggers Alerts

Phlo automatically sends alerts for:

1. **Asset Failures** - When materialization fails
2. **Quality Check Violations** - When data quality checks fail
3. **SLA Breaches** - When freshness or quality thresholds are exceeded

### Alert Severity Levels

| Severity     | Description       | Default Routing                         |
| ------------ | ----------------- | --------------------------------------- |
| **INFO**     | FYI notifications | Slack only                              |
| **WARNING**  | Needs attention   | Slack + Email                           |
| **ERROR**    | Something failed  | Slack + Email + PagerDuty (low urgency) |
| **CRITICAL** | Production impact | All channels + PagerDuty (high urgency) |

## Dashboards: Visualizing Health

### Main Operations Dashboard

```
Phlo Data Pipeline - Operations Dashboard

┌─────────────────┬─────────────────┬─────────────────┐
│ Pipeline Status │  Data Freshness │  Quality Score  │
│      ✓ HEALTHY  │      2.3 hours  │    99.74%       │
└─────────────────┴─────────────────┴─────────────────┘

Asset Execution Times (last 24 hours)
├─ dlt_glucose_entries:    150ms avg ✓
├─ stg_glucose_entries:    45ms avg ✓
├─ fct_glucose_readings:   320ms avg ✓
├─ mrt_glucose_readings:   85ms avg ✓
└─ publish_to_postgres:   1,240ms avg ⚠

Data Quality Checks (pass rate)
├─ glucose_range_check:         100% ✓
├─ glucose_freshness_check:     100% ✓
├─ no_duplicates:               100% ✓
├─ statistical_bounds_check:    99.9% ✓
└─ validation_pass_rate:        99.74% ✓

Active Alerts
├─ ⚠ publish_to_postgres running slow (1240ms vs 500ms avg)
└─ ℹ API latency slightly elevated (180ms vs 150ms avg)

Resource Utilization
├─ Disk: 45% used (180 GB / 400 GB)
├─ Memory: 62% used (10 GB / 16 GB)
└─ MinIO lake bucket: 280 GB
```

### Asset Health Dashboard

```
Asset: fct_glucose_readings

Status:        ✓ HEALTHY
Last Update:   2024-10-15 10:35:42 UTC (2.3 hours ago)
Owner:         data-platform-team
Layer:         Gold (Marts)
Row Count:     487,239

Execution Metrics (24 hours)
├─ Total runs: 288
├─ Success: 285 (98.96%)
├─ Failures: 3 (1.04%)
├─ Avg time: 320ms
├─ P95 time: 580ms
├─ P99 time: 950ms

Quality Checks
├─ glucose_range_check:         ✓ 487,239/487,239 valid
├─ glucose_freshness_check:     ✓ Latest: 2.3h ago
├─ no_duplicates:               ✓ 0 duplicates
└─ statistical_bounds_check:    ⚠ 2 outliers detected

Data Distribution
├─ Mean: 150 mg/dL
├─ Std Dev: 45 mg/dL
├─ Min: 22 mg/dL
├─ Max: 598 mg/dL
└─ Nulls: 0 (0%)

Downstream Usage
├─ mrt_glucose_readings (Gold) → 100K reads/day
├─ Superset Dashboard (Glucose Monitoring) → 450 views/day
└─ Alert: Low Glucose Detection → 12 alerts/day avg
```

## Tracing: Deep Debugging

Use distributed tracing to understand slow operations:

```python
# phlo/monitoring/tracing.py
from jaeger_client import Config
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from contextlib import contextmanager


jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)

tracer = trace.get_tracer(__name__)


@contextmanager
def trace_operation(operation_name: str, attributes: dict = None):
    """Context manager for tracing operations."""
    with tracer.start_as_current_span(operation_name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        yield span


# Usage in code
@asset
def dlt_glucose_entries(context):
    """Ingest with tracing."""

    with trace_operation("dlt_glucose_entries") as span:
        # Fetch
        with trace_operation("fetch_from_api") as fetch_span:
            fetch_span.set_attribute("endpoint", "nightscout_api")
            data = fetch_api()
            fetch_span.set_attribute("rows_fetched", len(data))

        # Validate
        with trace_operation("pandera_validation") as val_span:
            val_span.set_attribute("schema", "glucose_entries_v1")
            valid = validate(data)
            val_span.set_attribute("rows_valid", len(valid))

        # Merge
        with trace_operation("iceberg_merge") as merge_span:
            merge_span.set_attribute("table", "raw.glucose_entries")
            result = merge_to_iceberg(valid)
            merge_span.set_attribute("inserts", result["inserts"])
            merge_span.set_attribute("updates", result["updates"])
```
Expected output:
```text
No output (definitions only).
```

In Jaeger UI, you see:

```
Trace: dlt_glucose_entries
Duration: 152ms

├─ dlt_glucose_entries [0ms - 152ms] (main)
│  ├─ fetch_from_api [0ms - 45ms]
│  │  └─ http.request GET /api/v1/entries [5ms - 40ms]
│  ├─ pandera_validation [50ms - 62ms]
│  │  ├─ type_checking [50ms - 55ms]
│  │  └─ constraint_checking [55ms - 60ms]
│  └─ iceberg_merge [65ms - 152ms]
│     ├─ read_snapshot [65ms - 85ms]
│     ├─ merge_operation [85ms - 125ms]
│     └─ write_metadata [125ms - 152ms]
```
Expected output:
```text
Example rendered as shown.
```

Click on any span to see:

- Start time and duration
- Attributes (table name, row count, etc.)
- Logs within that span
- Errors or exceptions

## Monitoring as Code

```python
# phlo/monitoring/observability_assets.py
from dagster import asset, schedule


@asset(group_name="monitoring")
def freshness_dashboard(context):
    """Generate freshness dashboard."""
    queries = {
        "dlt_glucose_entries": """
            (time() - asset_last_update_timestamp{'asset'='dlt_glucose_entries'}) / 3600
        """,
        "fct_glucose_readings": """
            (time() - asset_last_update_timestamp{'asset'='fct_glucose_readings'}) / 3600
        """,
    }

    dashboard = create_grafana_dashboard(
        name="Data Freshness",
        panels=[
            create_gauge_panel(
                title=f"{asset} Age (hours)",
                query=query,
                thresholds={"warning": 2, "critical": 4},
            )
            for asset, query in queries.items()
        ],
    )

    context.log.info(f"✓ Created freshness dashboard: {dashboard.url}")


@asset(group_name="monitoring")
def sla_tracker(context):
    """Track SLA compliance."""
    slas = {
        "dlt_glucose_entries": {
            "freshness": "2 hours",
            "availability": "99.9%",
        },
        "fct_glucose_readings": {
            "freshness": "1 hour",
            "availability": "99.95%",
        },
    }

    for asset_name, sla in slas.items():
        record_sla_metric(asset_name, sla)
        context.log.info(f"✓ Updated SLA for {asset_name}")


@schedule(
    name="observability_updates",
    cron_schedule="* * * * *",  # Every minute
)
def update_observability():
    """Update monitoring dashboards and alerts."""
    return {}
```
Expected output:
```text
No output (definitions only).
```

## Lineage Visualization: Understanding Your Data Flow

One of the hardest questions in data engineering: "If I change this table, what breaks?"

Without lineage, you're guessing. With lineage, you know exactly what depends on what.

### Why Lineage Matters

```
Scenario: You need to rename a column in glucose_entries

Without lineage:
  1. Grep through code looking for references
  2. Miss the dbt model that uses a different alias
  3. Deploy change
  4. Dashboard breaks in production
  5. 2am phone call

With lineage:
  1. Run: phlo lineage impact glucose_entries
  2. See all 6 downstream dependencies
  3. Update them first
  4. Deploy safely
```
Expected output:
```text
Example rendered as shown.
```

### Viewing Lineage from CLI

The `phlo lineage` commands let you explore dependencies without opening a browser:

```bash
$ phlo lineage show glucose_entries

glucose_entries
├── [upstream]
│   └── (external) Nightscout API
│       └── Fetched via DLT rest_api
└── [downstream]
    └── stg_glucose_entries (dbt model)
        └── fct_glucose_readings (dbt model)
            ├── mrt_glucose_readings (dbt model)
            │   └── publish_glucose_marts (Dagster asset)
            │       └── (external) Superset Dashboard
            └── fct_daily_glucose_metrics (dbt model)
                └── mrt_glucose_hourly_patterns (dbt model)
```


This tree shows your entire data flow: from API source through transformations to dashboards.

### Impact Analysis

Before making changes, check what's affected:

```bash
$ phlo lineage impact glucose_entries

Impact Analysis: glucose_entries

Direct Dependencies (depth 1):
  • stg_glucose_entries (dbt) - 12 columns reference source

Transitive Dependencies (depth 2+):
  • fct_glucose_readings - 8 columns derived
  • fct_daily_glucose_metrics - aggregates from fact table

Publishing Impact:
  ⚠ mrt_glucose_readings → PostgreSQL marts (used by Superset)
  ⚠ publish_glucose_marts → External consumers

Total Impact:
  6 assets affected
  2 publishing endpoints
  1 external dashboard

Recommendation: Coordinate change with dashboard owners before deploying
```


### Exporting Lineage

Generate lineage diagrams for documentation:

```bash
# Graphviz DOT format
$ phlo lineage export --format dot --output lineage.dot
$ dot -Tpng lineage.dot -o lineage.png

# Mermaid format (for Markdown docs)
$ phlo lineage export --format mermaid --output lineage.md
```


The Mermaid output can be embedded directly in GitHub READMEs or Notion docs:

```mermaid
graph LR
    A[Nightscout API] --> B[glucose_entries]
    B --> C[stg_glucose_entries]
    C --> D[fct_glucose_readings]
    D --> E[mrt_glucose_readings]
    D --> F[fct_daily_glucose_metrics]
    E --> G[Superset Dashboard]
```
Expected output:
```text
Diagram renders in Markdown preview.
```

---

## Alerting: Getting Notified When Things Break

Dashboards are great, but you can't watch them 24/7. Alerting ensures you know about problems before your users do.

### Example Alert Format

When alerts are sent, they include context:

```
🔴 Asset Materialization Failed

Asset: glucose_entries
Partition: 2024-01-15
Run ID: abc123-def456

Error: Connection timeout after 30s

Timestamp: 2024-01-15 10:35:42 UTC
```
Expected output:
```text
Example rendered as shown.
```

The AlertManager automatically handles:

- **Deduplication** - Same asset + same error = 1 alert per hour (configurable)
- **Severity Routing** - Routes to appropriate channels based on severity
- **Context** - Includes run ID, asset name, error details

---

## Log Access and Filtering

When something goes wrong, you need logs. The `phlo logs` command gives you fast access without diving into Docker or Dagster UI.

### Why CLI Logs?

```
Scenario: Dashboard is showing stale data

Without CLI logs:
  1. Open browser
  2. Navigate to Dagster UI
  3. Find the run
  4. Scroll through logs
  5. Try to filter
  6. Give up and grep Docker logs

With phlo logs:
  $ phlo logs --asset glucose_entries --level ERROR --since 1h

  [10:35:42] ERROR glucose_entries: Connection refused to nightscout.api
  [10:35:42] ERROR glucose_entries: Retry 3/3 failed, aborting
  [10:35:43] ERROR glucose_entries: Run failed after 45s
```

### Filtering Options

```bash
# By asset
phlo logs --asset glucose_entries

# By time
phlo logs --since 1h          # Last hour
phlo logs --since 30m         # Last 30 minutes
phlo logs --since 7d          # Last week

# By severity
phlo logs --level ERROR       # Errors only
phlo logs --level WARNING     # Warnings and above

# Combined filters
phlo logs --asset glucose_entries --level ERROR --since 2h

# By specific run
phlo logs --run-id abc123-def456

# By job (for scheduled jobs)
phlo logs --job daily_glucose_pipeline
```


### Real-Time Tailing

Watch logs as they happen:

```bash
$ phlo logs --follow

[10:35:40] INFO  glucose_entries: Starting materialization
[10:35:41] INFO  glucose_entries: Fetching from Nightscout API
[10:35:42] INFO  glucose_entries: Retrieved 487 entries
[10:35:43] INFO  glucose_entries: Validating with Pandera schema
[10:35:44] INFO  glucose_entries: Writing to Iceberg table
[10:35:45] INFO  glucose_entries: Materialization complete (5.2s)
^C  # Ctrl+C to stop
```


### JSON Output for Scripting

Pipe logs to other tools:

```bash
# Find all unique error messages in the last day
phlo logs --level ERROR --since 1d --json | \
  jq -r '.[] | .message' | \
  sort | uniq -c | sort -rn

# Export to file for analysis
phlo logs --asset glucose_entries --since 7d --json > glucose_logs.json

# Grep for specific patterns
phlo logs --json | jq 'select(.message | contains("timeout"))'
```


---

## Metrics: Quantifying Pipeline Health

Logs tell you what happened. Metrics tell you how well things are running over time.

### The Metrics Dashboard

```bash
$ phlo metrics

Pipeline Health Dashboard (Last 24 Hours)
══════════════════════════════════════════

Overall Status: ✓ HEALTHY

Runs:
  Total:     288
  Success:   285 (98.96%)
  Failed:    3 (1.04%)

Data Volume:
  Rows Processed:  1.2M
  Bytes Written:   450 MB

Latency:
  P50:   320ms
  P95:   850ms
  P99:   1.2s

Quality:
  Pass Rate:     99.74%
  Checks Run:    1,440
  Failures:      4

Active Alerts: 1
  ⚠ publish_to_postgres running slow (1.2s avg vs 500ms baseline)
```


### Per-Asset Metrics

Drill into specific assets:

```bash
$ phlo metrics asset glucose_entries --runs 20

Asset: glucose_entries
════════════════════════

Last 20 Runs:
  Run ID          Time      Duration  Rows   Status
  ────────────────────────────────────────────────
  abc123          10:35     5.2s      487    ✓
  def456          10:30     4.8s      512    ✓
  ghi789          10:25     5.1s      495    ✓
  ...
  xyz000          09:05     45.2s     0      ✗ (timeout)

Statistics:
  Success Rate:   95% (19/20)
  Avg Duration:   5.1s
  P95 Duration:   8.2s
  Avg Rows:       498

Trend:
  Duration: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ (stable)
  Failures: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ (1 in window)
```


### Exporting for Analysis

Export metrics for external tools (Grafana, spreadsheets, custom analysis):

```bash
# CSV for spreadsheets
$ phlo metrics export --format csv --period 30d --output metrics.csv

# JSON for custom analysis
$ phlo metrics export --format json --period 7d | \
  python analyze_metrics.py
```


---

## Hands-On Exercise: Simulate an Alert

1. Stop one service: `phlo services stop trino`.
2. Confirm the alert condition in Dagster or Observatory logs.
3. Restart the service: `phlo services start trino`.
4. Verify the alert clears and metrics recover.

## Common Issues

- **Observatory UI not loading**

```bash
phlo services logs observatory
curl http://localhost:3001
```


Fix: restart Observatory and confirm port 3001 is reachable.

- **Dashboards show no metrics**

```bash
phlo services logs grafana
phlo services logs prometheus
```


Fix: verify metrics exporters are running and Grafana data sources are configured.

- **Logs not appearing in the UI**

```bash
phlo services logs loki
```


Fix: confirm log shipping configuration and restart Loki if needed.

See [Troubleshooting Guide](../operations/troubleshooting.md) for deeper diagnostics.

## See Also

See also: [Part 7: Orchestration with Dagster](07-orchestration-dagster.md), [Part 10: Metadata and Governance](10-metadata-governance.md), [Part 15: Observatory Extensions](15-observatory-extensions.md). Reference: [Phlo API Reference](../reference/phlo-api.md).


## Summary

Phlo's observability stack provides:

**Metrics**: Track what's happening via `phlo metrics` (execution time, throughput, quality)
**Logs**: Understand why with `phlo logs` (structured logs, searchable, real-time tailing)
**Lineage**: Understand impact with `phlo lineage` (CLI visualization, export, impact analysis)
**Alerts**: Get notified via `phlo alerts` (Slack, PagerDuty, email with deduplication)

Combined, you have:

- **Visibility**: Know your pipeline state at any time via CLI
- **Reliability**: Automated alerts detect failures before users do
- **Speed**: Find root causes in minutes with structured logs and lineage
- **Confidence**: Deploy with safety nets and impact analysis in place

All accessible through simple CLI commands that integrate with your existing workflows.

## Next Steps

- Continue with [Part 12: Production Deployment and Scaling](12-production-deployment.md).
- Explore custom extensions in [Part 15: Observatory Extensions](15-observatory-extensions.md).

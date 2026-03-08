# phlo-otel

OpenTelemetry instrumentation for Phlo. Translates hook events into OTel traces and metrics.

## Install

```bash
uv pip install -e packages/phlo-otel
```

## Configuration

Uses standard OTel environment variables, with Phlo settings as defaults when
the OTel variables are unset:

| Variable | Default | Description |
|---|---|---|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP gRPC endpoint |
| `OTEL_SERVICE_NAME` | `PHLO_LOG_SERVICE_NAME` or `phlo` | Service name in traces/metrics |
| `OTEL_SERVICE_NAMESPACE` | `PHLO_SERVICE_NAMESPACE` or `phlo` | Service namespace |
| `OTEL_SERVICE_VERSION` | `PHLO_SERVICE_VERSION` or `0.1.0` | Service version attached to resources |
| `OTEL_SERVICE_INSTANCE_ID` | `PHLO_SERVICE_INSTANCE_ID` or hostname | Service instance identifier |
| `OTEL_TRACES_EXPORTER` | unset | Set to `otlp` or configure an OTLP endpoint to enable trace export |
| `OTEL_METRICS_EXPORTER` | unset | Set to `otlp` or configure an OTLP endpoint to enable metrics export |
| `OTEL_LOGS_EXPORTER` | `none` | Set to `otlp` to enable OTLP log export |
| `PHLO_PROJECT` | `PHLO_PROJECT` setting or service name | Project identifier attached to resources |

Additional resource metadata comes from Phlo settings and `OTEL_RESOURCE_ATTRIBUTES`,
including `deployment.environment`, `phlo.package`, `phlo.runtime`, and
`phlo.project`.

Phlo settings supported for resource defaults:

- `PHLO_LOG_SERVICE_NAME`
- `PHLO_SERVICE_NAMESPACE`
- `PHLO_SERVICE_VERSION`
- `PHLO_SERVICE_INSTANCE_ID`
- `PHLO_PROJECT`
- `PHLO_ENVIRONMENT`

## What gets instrumented

| Hook Event | Trace Span | Metric |
|---|---|---|
| `IngestionEvent` | `ingestion.<table>` | `phlo.ingestion.runs`, `phlo.ingestion.rows`, `phlo.ingestion.duration` |
| `TransformEvent` | `transform.<tool>.<target>` | `phlo.transform.runs`, `phlo.transform.duration` |
| `QualityResultEvent` | `quality.<check>` | `phlo.quality.checks` |
| `LineageEvent` | `lineage.edges` | `phlo.lineage.events`, `phlo.lineage.edges` |
| `PublishEvent` | `publish.<target_system>` | `phlo.publish.runs`, `phlo.publish.tables`, `phlo.publish.duration` |
| `ServiceLifecycleEvent` | `service.<service>.<phase>` | `phlo.service.lifecycle.events` |
| `SchemaMigrationEvent` | `schema_migration.<table>` | `phlo.schema_migration.runs`, `phlo.schema_migration.changes` |
| `DataMigrationEvent` | `data_migration.<migration>` | `phlo.data_migration.runs`, `phlo.data_migration.rows_read`, `phlo.data_migration.rows_written`, `phlo.data_migration.duration` |
| `TelemetryEvent` | — | `phlo.telemetry.<name>` (`gauge` by default; `counter`, `histogram`, and `up_down_counter` supported via payload) |
| `LogEvent` | — | OTLP log records with Phlo correlation attributes |

Trace and metric export activate when you configure an OTLP endpoint or set the
standard exporter env vars. OTLP log export is supported but stays opt-in.
Failure statuses across workflow events also increment `phlo.errors`.
Spans and OTLP log records carry shared correlation fields when hook producers
provide them, including `run_id`, `asset_key`, `partition_key`, `job_name`,
and trace/span identifiers.

Example:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_TRACES_EXPORTER=otlp
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
```

### Telemetry metric kinds

`TelemetryEvent(event_type="telemetry.metric")` defaults to a gauge. Override the
instrument type with `payload["metric_kind"]` or `payload["otel_metric_kind"]`.

Supported values:

- `gauge`
- `counter`
- `histogram`
- `up_down_counter`

Example:

```python
telemetry.emit_metric(
    name="rows_written",
    value=250,
    unit="rows",
    payload={"metric_kind": "counter", "source": "nightscout"},
)
```

### Metric label policy

Telemetry metric payloads are filtered to low-cardinality labels before export.
Allowed label keys currently include:

- `backend`
- `classification`
- `environment`
- `namespace`
- `operation`
- `phase`
- `result`
- `service`
- `source`
- `source_type`
- `status`
- `target`
- `target_system`
- `tool`

Identifiers such as `run_id`, `partition_key`, and `asset_key` stay in traces
and logs rather than metric labels.

## Architecture

Hooks into the existing `HookBus` as a `HookPlugin` — same pattern as `phlo-metrics`.
Point the OTLP exporters at Alloy (already OTel-compatible) or directly at your
trace/metric/log backends.

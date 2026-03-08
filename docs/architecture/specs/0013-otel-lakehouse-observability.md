# Spec 0013: OTel Lakehouse Observability

## Status

Draft

## Summary

`phlo-otel` should become Phlo's OpenTelemetry emission layer for lakehouse
workloads, not a backend-specific integration. Phlo should emit clean OTLP
traces, metrics, and eventually logs, then rely on Alloy or OpenTelemetry
Collector to route data to Tempo, Prometheus-compatible systems, Grafana, or
ClickHouse-backed ClickStack.

This keeps backend choice outside core workflow packages and makes Phlo's
observability model portable.

## Problem

Current `phlo-otel` covers only a narrow slice of observability:

- one global provider setup
- spans for ingestion, transform, and quality events
- counters for a few workflow events
- gauges for numeric telemetry events

Gaps:

- resource attributes are too thin for multi-service deployments
- metric instruments are created ad hoc inside handlers
- metric type selection is too coarse
- spans are isolated rather than linked into pipeline traces
- logs are not exported through OTel
- label/cardinality policy is not defined
- several hook event types are not instrumented
- correlation between logs, spans, and metrics is incomplete

For a real Phlo-powered lakehouse, this is enough for demos but not enough for
incident response, performance analysis, or backend portability.

## Goals

- Make OTLP the only observability export contract for `phlo-otel`.
- Support end-to-end correlation across traces, metrics, and logs.
- Define stable Phlo-specific semantic attributes for lakehouse events.
- Keep metric labels low-cardinality and trace attributes rich.
- Cover the full workflow path: ingestion, quality, transform, publish,
  maintenance, migrations, and service lifecycle.
- Stay backend-agnostic so Alloy/Collector can route to Tempo, Prometheus,
  Grafana, ClickStack, or future backends.

## Non-Goals

- Do not add backend-specific logic for ClickHouse, Tempo, or Grafana into
  `phlo-otel`.
- Do not redesign all observability UI surfaces in this spec.
- Do not replace `phlo-metrics` or existing Prometheus-oriented APIs in one
  step.
- Do not allow high-cardinality metrics for convenience.

## Design Principles

- OTLP-only boundary: backends are collector concerns.
- Stable event naming: Phlo event semantics must be explicit and documented.
- Low-cardinality metrics: dimensions safe for long-term storage and alerts.
- Rich traces: run identifiers, partition keys, and asset context belong in
  traces and logs more than metrics.
- Shared correlation: every signal should support trace/log/run navigation.
- Incremental rollout: keep existing hook/event model and extend it.

## Current State

Current `phlo-otel` behavior:

- `IngestionEvent` -> one span, run counter, rows counter
- `TransformEvent` -> one span, run counter
- `QualityResultEvent` -> one span, checks counter
- `TelemetryEvent(event_type="telemetry.metric")` -> one gauge

Current provider behavior:

- initializes global tracer + meter providers once
- sets only `service.name`
- uses OTLP gRPC exporters directly

This is a valid first slice, but it does not yet represent Phlo's full
lakehouse runtime.

## Proposed Architecture

### 1. OTLP as the only backend contract

`phlo-otel` should emit OTel signals only. Routing to storage/query systems
should happen through Alloy or OpenTelemetry Collector.

Target flow:

```text
Phlo workflow packages
  -> HookBus events
  -> phlo-otel
  -> OTLP
  -> Alloy / OTel Collector
  -> Tempo / Prometheus-compatible backend / Loki / ClickStack
```

Implication:

- no `phlo-clickhouse-otel` plugin needed for first-class support
- ClickStack support should be collector configuration, not Phlo code

### 2. Resource attributes

Extend provider resource setup beyond `service.name`.

Minimum resource attributes:

- `service.name`
- `service.namespace`
- `service.version`
- `deployment.environment`
- `service.instance.id`
- `phlo.package`
- `phlo.runtime`
- `phlo.project`

These attributes should be configurable from Phlo settings and standard
`OTEL_RESOURCE_ATTRIBUTES`.

### 3. Stable Phlo semantic attributes

Document and standardize Phlo-specific attributes for emitted spans, logs, and
metrics metadata.

Candidate attributes:

- `phlo.event_type`
- `phlo.stage`
- `phlo.system`
- `phlo.tool`
- `phlo.operation`
- `phlo.status`
- `phlo.asset_key`
- `phlo.table_name`
- `phlo.dataset`
- `phlo.check_name`
- `phlo.group_name`
- `phlo.partition_key`
- `phlo.run_id`

Rule:

- high-cardinality fields may appear in traces/logs
- only low-cardinality fields may appear as metric labels

### 4. Instrument registry and lifecycle

Do not create counters, gauges, or histograms on every event handler call.
Create and cache instruments once per process per meter.

Suggested registry:

- `phlo.ingestion.runs` counter
- `phlo.ingestion.rows` counter
- `phlo.ingestion.duration` histogram
- `phlo.transform.runs` counter
- `phlo.transform.duration` histogram
- `phlo.quality.checks` counter
- `phlo.publish.runs` counter
- `phlo.publish.duration` histogram
- `phlo.maintenance.runs` counter
- `phlo.maintenance.duration` histogram
- `phlo.errors` counter

Dynamic telemetry events may still require dynamic instruments, but the system
should prefer a bounded metric vocabulary for common workflow signals.

### 5. Metric type policy

Use metric types intentionally:

- counters:
  - run counts
  - rows read/written
  - files created/deleted
  - retries
  - failures
- histograms:
  - duration
  - bytes scanned/written
  - latency
  - batch sizes
- gauges:
  - point-in-time backlog
  - freshness lag
  - open connections

Rule:

- `telemetry.metric` should not default to gauge forever
- Phlo should support explicit metric kind selection or a documented mapping

### 6. Cardinality policy

Low-cardinality labels allowed in metrics:

- `service`
- `environment`
- `tool`
- `operation`
- `status`
- `result`
- `namespace`

Avoid in metrics:

- `run_id`
- `partition_key`
- `asset_key` if unbounded
- arbitrary telemetry payload keys
- user-provided freeform identifiers

Those fields should stay in traces and logs.

### 7. Trace model

Move from isolated spans to run-oriented traces.

Target shape:

```text
pipeline.run
  -> ingestion.<table>
  -> quality.<check>
  -> transform.<tool>.<target>
  -> publish.<target>
  -> maintenance.<operation>
```

Requirements:

- preserve parent/child relationships where the execution model allows
- bind `run_id`, `asset_key`, and `partition_key` consistently
- capture failure status and exception details on spans

### 8. Log correlation

Phlo already exposes correlation fields in structured logging. `phlo-otel`
should connect those logs with active trace/span context.

Desired end state:

- logs emitted during active spans include `trace_id` and `span_id`
- OTel log export is supported, or a bridge exists from `LogEvent` to OTLP logs
- dashboards can pivot from metric anomaly -> trace -> logs

### 9. Event coverage

Expand instrumentation beyond the current hook subset.

Priority additions:

- `PublishEvent`
- `ServiceLifecycleEvent`
- `SchemaMigrationEvent`
- `DataMigrationEvent`
- `LineageEvent` success/failure metadata
- Iceberg maintenance telemetry

This should align `phlo-otel` with the broader hook surface, not just the
initial workflow events.

## ClickStack / ClickHouse Considerations

ClickStack support should assume ClickHouse is a storage/query backend behind an
OTLP-compatible ingestion path.

Guidance:

- keep OTLP emission backend-neutral
- prefer append-only event semantics
- enforce clear units on all numeric signals
- keep metric dimensions conservative
- preserve correlation fields for trace/log exploration

ClickHouse tolerates high volume well, but poor metric cardinality will still
be expensive and hard to operate. This makes label discipline a hard
requirement, not an optimization.

## Rollout Plan

### Phase 1: Provider and metadata hardening

- enrich resource attributes in `phlo-otel`
- add Phlo settings for environment/service metadata where needed
- document collector-oriented deployment shape

### Phase 2: Instrument model cleanup

- add instrument caching
- define standard workflow metric names
- introduce explicit metric kind policy for telemetry events
- update tests for instrument reuse and type behavior

### Phase 3: Correlation and trace hierarchy

- propagate span context across workflow execution boundaries
- bind logs to active trace/span context
- add parent/child spans for pipeline runs and child stages

### Phase 4: Event coverage expansion

- instrument publish, service lifecycle, schema/data migration, and maintenance
- document semantic attributes for each event family
- add regression coverage for event-to-signal mapping

### Phase 5: Backend guidance

- add docs for Alloy / Collector topologies
- document Tempo + Prometheus + Grafana deployment
- document ClickStack-compatible collector routing

## Acceptance Criteria

- `phlo-otel` emits backend-agnostic OTLP signals.
- Common workflow instruments are cached and reused.
- Metric kinds are intentional and documented.
- Logs, metrics, and traces can be correlated via shared identifiers.
- Full workflow traces can represent parent/child execution stages.
- Additional hook event families are instrumented without backend-specific code.
- ClickStack support requires collector configuration, not Phlo plugin forks.

## Open Questions

- Should `TelemetryEvent` gain an explicit metric kind field?
- Should Phlo export OTLP logs directly or route structured logs through a
  dedicated sink bridge first?
- What is the canonical root span boundary: CLI invocation, Dagster run, asset
  materialization, or Phlo workflow run?
- Which Phlo identifiers are guaranteed low-cardinality enough for metric
  labels across real deployments?

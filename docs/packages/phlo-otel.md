# phlo-otel

`phlo-otel` translates Phlo hook events into OpenTelemetry traces, metrics, and
optionally OTLP log records.

## What It Does

- Creates spans for ingestion, transform, quality, lineage, publish, service lifecycle, and migration events
- Emits standard workflow metrics such as runs, rows, durations, lineage edges, and errors
- Exports routed `LogEvent` records to OTLP logs when log export is enabled
- Reuses shared hook correlation so traces and logs can link by `run_id`, `asset_key`, `partition_key`, `job_name`, and trace/span IDs

## Configuration

`phlo-otel` uses standard `OTEL_*` environment variables and falls back to Phlo
settings when those variables are unset.

Relevant Phlo settings:

- `PHLO_LOG_SERVICE_NAME`
- `PHLO_SERVICE_NAMESPACE`
- `PHLO_SERVICE_VERSION`
- `PHLO_SERVICE_INSTANCE_ID`
- `PHLO_PROJECT`
- `PHLO_ENVIRONMENT`

Resource attributes emitted by default include:

- `service.name`
- `service.namespace`
- `service.version`
- `service.instance.id`
- `deployment.environment`
- `phlo.package`
- `phlo.runtime`
- `phlo.project`

## Metric Labels

Metric labels stay intentionally low-cardinality. Labels such as `status`,
`tool`, `service`, `target_system`, and `source_type` are allowed. High-cardinality
identifiers like `run_id`, `asset_key`, and `partition_key` stay in traces and logs.

## Related Docs

- [Configuration Reference](../reference/configuration-reference.md)
- [Observability Setup](../setup/observability.md)
- [Packages Index](index.md)

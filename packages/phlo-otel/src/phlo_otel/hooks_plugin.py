"""Hook plugin that translates Phlo events into OTel spans and metrics."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from opentelemetry._logs import LogRecord, SeverityNumber
from opentelemetry.trace import Span, StatusCode, get_current_span

from phlo.hooks.events import DataMigrationEvent
from phlo.hooks.events import LogEvent
from phlo.hooks.events import LineageEvent
from phlo.hooks.events import PublishEvent
from phlo.hooks.events import QualityResultEvent
from phlo.hooks.events import SchemaMigrationEvent
from phlo.hooks.events import ServiceLifecycleEvent
from phlo.hooks.events import TelemetryEvent
from phlo.hooks.events import TransformEvent
from phlo.hooks.events import IngestionEvent
from phlo.plugins.base import PluginMetadata
from phlo.plugins.hooks import HookPlugin, HookRegistration

from phlo_otel.provider import get_log_emitter, get_meter, get_tracer


class OtelHookPlugin(HookPlugin):
    """Emit OTel traces and metrics from Phlo hook events."""

    def __init__(self) -> None:
        self._counter_cache: dict[tuple[str, str], Any] = {}
        self._gauge_cache: dict[tuple[str, str], Any] = {}
        self._histogram_cache: dict[tuple[str, str], Any] = {}
        self._up_down_counter_cache: dict[tuple[str, str], Any] = {}

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="otel",
            version="0.1.0",
            description="OpenTelemetry instrumentation for Phlo",
        )

    def get_hooks(self) -> list[HookRegistration]:
        return [
            HookRegistration(
                hook_name="otel_ingestion",
                handler=self._handle_ingestion,
            ),
            HookRegistration(
                hook_name="otel_transform",
                handler=self._handle_transform,
            ),
            HookRegistration(
                hook_name="otel_quality",
                handler=self._handle_quality,
            ),
            HookRegistration(
                hook_name="otel_lineage",
                handler=self._handle_lineage,
            ),
            HookRegistration(
                hook_name="otel_publish",
                handler=self._handle_publish,
            ),
            HookRegistration(
                hook_name="otel_service_lifecycle",
                handler=self._handle_service_lifecycle,
            ),
            HookRegistration(
                hook_name="otel_schema_migration",
                handler=self._handle_schema_migration,
            ),
            HookRegistration(
                hook_name="otel_data_migration",
                handler=self._handle_data_migration,
            ),
            HookRegistration(
                hook_name="otel_telemetry",
                handler=self._handle_telemetry,
            ),
            HookRegistration(
                hook_name="otel_log_record",
                handler=self._handle_log_record,
            ),
        ]

    def _handle_ingestion(self, event: Any) -> None:
        if not isinstance(event, IngestionEvent):
            return

        tracer = get_tracer()
        with tracer.start_as_current_span(
            f"ingestion.{event.table_name}",
            attributes={
                "phlo.asset_key": event.asset_key,
                "phlo.table_name": event.table_name,
                "phlo.group_name": event.group_name,
                "phlo.event_type": event.event_type,
            },
        ) as span:
            if event.partition_key:
                span.set_attribute("phlo.partition_key", event.partition_key)
            if event.run_id:
                span.set_attribute("phlo.run_id", event.run_id)
            if event.status:
                span.set_attribute("phlo.status", event.status)
            if event.error:
                span.set_status(StatusCode.ERROR, event.error)
            if event.metrics:
                for key, value in event.metrics.items():
                    if isinstance(value, (int, float)):
                        span.set_attribute(f"phlo.metrics.{key}", value)
            self._record_failure(event_name="ingestion", status=event.status, error=event.error)

        counter = self._get_counter(
            "phlo.ingestion.runs",
            description="Number of ingestion runs",
        )
        counter.add(1, {"table_name": event.table_name, "status": event.status or "unknown"})

        rows = event.metrics.get("rows_loaded")
        if rows is None:
            rows = event.metrics.get("rows_processed")
        if isinstance(rows, (int, float)):
            rows_counter = self._get_counter(
                "phlo.ingestion.rows",
                description="Rows ingested",
            )
            rows_counter.add(int(rows), {"table_name": event.table_name})

        self._record_duration(
            "phlo.ingestion.duration",
            metrics=event.metrics,
            attributes={"table_name": event.table_name, "status": event.status or "unknown"},
            description="Ingestion duration",
        )

    def _handle_transform(self, event: Any) -> None:
        if not isinstance(event, TransformEvent):
            return

        tracer = get_tracer()
        span_name = f"transform.{event.tool}"
        if event.target:
            span_name = f"transform.{event.tool}.{event.target}"

        with tracer.start_as_current_span(
            span_name,
            attributes={
                "phlo.tool": event.tool,
                "phlo.event_type": event.event_type,
            },
        ) as span:
            if event.target:
                span.set_attribute("phlo.target", event.target)
            if event.model_names:
                span.set_attribute("phlo.model_names", event.model_names)
            if event.status:
                span.set_attribute("phlo.status", event.status)
            if event.error:
                span.set_status(StatusCode.ERROR, event.error)
            if event.asset_key:
                span.set_attribute("phlo.asset_key", event.asset_key)
            if event.partition_key:
                span.set_attribute("phlo.partition_key", event.partition_key)
            self._set_numeric_span_attributes(span, event.metrics)
            self._record_failure(event_name="transform", status=event.status, error=event.error)

        counter = self._get_counter(
            "phlo.transform.runs",
            description="Number of transform runs",
        )
        counter.add(1, {"tool": event.tool, "status": event.status or "unknown"})

        self._record_duration(
            "phlo.transform.duration",
            metrics=event.metrics,
            attributes={"tool": event.tool, "status": event.status or "unknown"},
            description="Transform duration",
        )

    def _handle_quality(self, event: Any) -> None:
        if not isinstance(event, QualityResultEvent):
            return

        tracer = get_tracer()
        with tracer.start_as_current_span(
            f"quality.{event.check_name}",
            attributes={
                "phlo.asset_key": event.asset_key,
                "phlo.check_name": event.check_name,
                "phlo.passed": event.passed,
                "phlo.event_type": event.event_type,
            },
        ) as span:
            if event.severity:
                span.set_attribute("phlo.severity", event.severity)
            if event.partition_key:
                span.set_attribute("phlo.partition_key", event.partition_key)
            for key, value in event.metadata.items():
                if isinstance(value, (bool, int, float, str)):
                    span.set_attribute(f"phlo.metadata.{key}", value)
            if not event.passed:
                span.set_status(StatusCode.ERROR, f"Quality check failed: {event.check_name}")
                self._record_failure(event_name="quality", status="fail")

        counter = self._get_counter(
            "phlo.quality.checks",
            description="Quality check executions",
        )
        result = "pass" if event.passed else "fail"
        counter.add(1, {"check_name": event.check_name, "result": result})

    def _handle_lineage(self, event: Any) -> None:
        if not isinstance(event, LineageEvent):
            return

        tracer = get_tracer()
        with tracer.start_as_current_span(
            "lineage.edges",
            attributes={
                "phlo.event_type": event.event_type,
                "phlo.edge_count": len(event.edges),
                "phlo.asset_count": len(event.asset_keys),
            },
        ) as span:
            if event.asset_keys:
                span.set_attribute("phlo.asset_keys", sorted(event.asset_keys))
            self._set_event_tags(span, event.tags)
            for key, value in event.metadata.items():
                if isinstance(value, (bool, int, float, str)):
                    span.set_attribute(f"phlo.metadata.{key}", value)

        event_counter = self._get_counter(
            "phlo.lineage.events",
            description="Number of lineage events",
        )
        edge_counter = self._get_counter(
            "phlo.lineage.edges",
            description="Number of lineage edges",
        )
        attributes = self._metric_attributes_from_tags(event.tags)
        event_counter.add(1, attributes)
        edge_counter.add(len(event.edges), attributes)

    def _handle_publish(self, event: Any) -> None:
        if not isinstance(event, PublishEvent):
            return

        target_system = event.target_system or "unknown"
        tracer = get_tracer()
        with tracer.start_as_current_span(
            f"publish.{target_system}",
            attributes={
                "phlo.event_type": event.event_type,
                "phlo.target_system": target_system,
            },
        ) as span:
            if event.asset_key:
                span.set_attribute("phlo.asset_key", event.asset_key)
            if event.status:
                span.set_attribute("phlo.status", event.status)
            if event.tables:
                span.set_attribute("phlo.table_count", len(event.tables))
                span.set_attribute("phlo.tables", sorted(event.tables.values()))
            if event.error:
                span.set_status(StatusCode.ERROR, event.error)
            self._set_numeric_span_attributes(span, event.metrics)
            self._set_event_tags(span, event.tags)
            self._record_failure(event_name="publish", status=event.status, error=event.error)

        counter = self._get_counter(
            "phlo.publish.runs",
            description="Number of publish runs",
        )
        counter.add(1, {"target_system": target_system, "status": event.status or "unknown"})

        if event.tables:
            table_counter = self._get_counter(
                "phlo.publish.tables",
                description="Number of published tables",
            )
            table_counter.add(len(event.tables), {"target_system": target_system})

        self._record_duration(
            "phlo.publish.duration",
            metrics=event.metrics,
            attributes={"target_system": target_system, "status": event.status or "unknown"},
            description="Publish duration",
        )

    def _handle_service_lifecycle(self, event: Any) -> None:
        if not isinstance(event, ServiceLifecycleEvent):
            return

        phase = event.phase or "unknown"
        tracer = get_tracer()
        with tracer.start_as_current_span(
            f"service.{event.service_name}.{phase}",
            attributes={
                "phlo.event_type": event.event_type,
                "phlo.service_name": event.service_name,
                "phlo.phase": phase,
            },
        ) as span:
            if event.project_name:
                span.set_attribute("phlo.project_name", event.project_name)
            if event.project_root:
                span.set_attribute("phlo.project_root", event.project_root)
            if event.container_name:
                span.set_attribute("phlo.container_name", event.container_name)
            if event.status:
                span.set_attribute("phlo.status", event.status)
                if self._is_failure_status(event.status):
                    span.set_status(StatusCode.ERROR, f"Service lifecycle failed: {phase}")
            self._set_event_tags(span, event.tags)
            self._record_failure(event_name="service_lifecycle", status=event.status)

        counter = self._get_counter(
            "phlo.service.lifecycle.events",
            description="Number of service lifecycle events",
        )
        counter.add(
            1,
            {
                "service_name": event.service_name,
                "phase": phase,
                "status": event.status or "unknown",
            },
        )

    def _handle_schema_migration(self, event: Any) -> None:
        if not isinstance(event, SchemaMigrationEvent):
            return

        tracer = get_tracer()
        with tracer.start_as_current_span(
            f"schema_migration.{event.table_name}",
            attributes={
                "phlo.event_type": event.event_type,
                "phlo.table_name": event.table_name,
                "phlo.classification": event.classification,
                "phlo.change_count": event.change_count,
                "phlo.status": event.status,
            },
        ) as span:
            if event.changes:
                span.set_attribute("phlo.schema_change_count", len(event.changes))
            self._set_event_tags(span, event.tags)
            if self._is_failure_status(event.status):
                span.set_status(StatusCode.ERROR, f"Schema migration failed: {event.table_name}")
            self._record_failure(event_name="schema_migration", status=event.status)

        labels = {"classification": event.classification, "status": event.status}
        counter = self._get_counter(
            "phlo.schema_migration.runs",
            description="Number of schema migration events",
        )
        counter.add(1, labels)

        changes_counter = self._get_counter(
            "phlo.schema_migration.changes",
            description="Schema change count",
        )
        changes_counter.add(event.change_count, labels)

    def _handle_data_migration(self, event: Any) -> None:
        if not isinstance(event, DataMigrationEvent):
            return

        tracer = get_tracer()
        with tracer.start_as_current_span(
            f"data_migration.{event.migration_name}",
            attributes={
                "phlo.event_type": event.event_type,
                "phlo.migration_name": event.migration_name,
                "phlo.source_type": event.source_type,
                "phlo.destination_table": event.destination_table,
                "phlo.rows_read": event.rows_read,
                "phlo.rows_written": event.rows_written,
                "phlo.status": event.status,
            },
        ) as span:
            if event.chunk_index is not None:
                span.set_attribute("phlo.chunk_index", event.chunk_index)
            self._set_numeric_span_attributes(span, event.metrics)
            self._set_event_tags(span, event.tags)
            if self._is_failure_status(event.status):
                span.set_status(StatusCode.ERROR, f"Data migration failed: {event.migration_name}")
            self._record_failure(event_name="data_migration", status=event.status)

        labels = {"source_type": event.source_type, "status": event.status}
        runs_counter = self._get_counter(
            "phlo.data_migration.runs",
            description="Number of data migration events",
        )
        runs_counter.add(1, labels)

        rows_read_counter = self._get_counter(
            "phlo.data_migration.rows_read",
            description="Rows read during data migration",
        )
        rows_read_counter.add(event.rows_read, labels)

        rows_written_counter = self._get_counter(
            "phlo.data_migration.rows_written",
            description="Rows written during data migration",
        )
        rows_written_counter.add(event.rows_written, labels)

        self._record_duration(
            "phlo.data_migration.duration",
            metrics=event.metrics,
            attributes=labels,
            description="Data migration duration",
        )

    def _handle_telemetry(self, event: Any) -> None:
        if not isinstance(event, TelemetryEvent):
            return
        if event.event_type != "telemetry.metric":
            return
        if not isinstance(event.value, (int, float)):
            return

        metric_name = f"phlo.telemetry.{event.name}"
        attributes = self._normalize_metric_attributes(event.payload)
        metric_kind = self._resolve_metric_kind(attributes)
        unit = event.unit or ""

        if metric_kind == "counter":
            counter = self._get_counter(
                metric_name,
                description=f"Telemetry metric: {event.name}",
                unit=unit,
            )
            counter.add(event.value, attributes)
            return

        if metric_kind == "histogram":
            histogram = self._get_histogram(
                metric_name,
                unit=unit,
                description=f"Telemetry metric: {event.name}",
            )
            histogram.record(event.value, attributes)
            return

        if metric_kind == "up_down_counter":
            counter = self._get_up_down_counter(
                metric_name,
                unit=unit,
                description=f"Telemetry metric: {event.name}",
            )
            counter.add(event.value, attributes)
            return

        gauge = self._get_gauge(
            metric_name,
            unit=unit,
            description=f"Telemetry metric: {event.name}",
        )
        gauge.set(event.value, attributes)

    def _handle_log_record(self, event: Any) -> None:
        if not isinstance(event, LogEvent):
            return

        attributes = self._build_log_attributes(event)
        trace_id, span_id, trace_flags = self._resolve_log_context(event)
        log_record = LogRecord(
            timestamp=self._datetime_to_unix_nanos(event.timestamp),
            observed_timestamp=self._datetime_to_unix_nanos(datetime.now(event.timestamp.tzinfo)),
            trace_id=trace_id,
            span_id=span_id,
            trace_flags=trace_flags,
            severity_text=event.level.upper(),
            severity_number=self._map_severity(event.level),
            body=event.message,
            attributes=attributes,
            event_name=event.event_type,
        )
        emitter = get_log_emitter()
        if emitter is None:
            return
        emitter.emit(log_record)

    def _get_counter(self, name: str, *, description: str, unit: str = "") -> Any:
        cache_key = (name, unit)
        counter = self._counter_cache.get(cache_key)
        if counter is None:
            counter = get_meter().create_counter(name, unit=unit, description=description)
            self._counter_cache[cache_key] = counter
        return counter

    def _get_gauge(self, name: str, *, unit: str, description: str) -> Any:
        cache_key = (name, unit)
        gauge = self._gauge_cache.get(cache_key)
        if gauge is None:
            gauge = get_meter().create_gauge(name, unit=unit, description=description)
            self._gauge_cache[cache_key] = gauge
        return gauge

    def _get_histogram(self, name: str, *, unit: str, description: str) -> Any:
        cache_key = (name, unit)
        histogram = self._histogram_cache.get(cache_key)
        if histogram is None:
            histogram = get_meter().create_histogram(name, unit=unit, description=description)
            self._histogram_cache[cache_key] = histogram
        return histogram

    def _get_up_down_counter(self, name: str, *, unit: str, description: str) -> Any:
        cache_key = (name, unit)
        counter = self._up_down_counter_cache.get(cache_key)
        if counter is None:
            counter = get_meter().create_up_down_counter(name, unit=unit, description=description)
            self._up_down_counter_cache[cache_key] = counter
        return counter

    def _resolve_metric_kind(self, attributes: dict[str, Any]) -> str:
        """Resolve telemetry metric type from reserved payload attributes."""
        raw_kind = attributes.pop("metric_kind", attributes.pop("otel_metric_kind", "gauge"))
        if not isinstance(raw_kind, str):
            return "gauge"

        metric_kind = raw_kind.strip().lower().replace("-", "_")
        valid_kinds = {"counter", "gauge", "histogram", "up_down_counter"}
        if metric_kind not in valid_kinds:
            return "gauge"
        return metric_kind

    def _normalize_metric_attributes(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for key, value in payload.items():
            normalized[key] = self._coerce_metric_attribute_value(value)
        return normalized

    def _set_numeric_span_attributes(self, span: Span, metrics: dict[str, Any]) -> None:
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                span.set_attribute(f"phlo.metrics.{key}", value)

    def _set_event_tags(self, span: Span, tags: dict[str, str]) -> None:
        for key, value in tags.items():
            span.set_attribute(f"phlo.tags.{key}", value)

    def _metric_attributes_from_tags(self, tags: dict[str, str]) -> dict[str, str]:
        allowed = {
            "backend",
            "environment",
            "namespace",
            "operation",
            "service",
            "source",
            "target",
            "tool",
        }
        return {key: value for key, value in tags.items() if key in allowed}

    def _build_log_attributes(self, event: LogEvent) -> dict[str, Any]:
        attributes: dict[str, Any] = {
            "phlo.logger": event.logger,
            "phlo.level": event.level,
        }
        if event.service:
            attributes["phlo.service"] = event.service
        if event.run_id:
            attributes["phlo.run_id"] = event.run_id
        if event.asset_key:
            attributes["phlo.asset_key"] = event.asset_key
        if event.job_name:
            attributes["phlo.job_name"] = event.job_name
        if event.partition_key:
            attributes["phlo.partition_key"] = event.partition_key
        if event.check_name:
            attributes["phlo.check_name"] = event.check_name

        for key, value in event.tags.items():
            attributes[f"phlo.tag.{key}"] = value
        for key, value in event.metadata.items():
            attributes[f"phlo.metadata.{key}"] = self._coerce_attribute_value(value)
        return attributes

    def _coerce_attribute_value(self, value: Any) -> Any:
        if isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, (list, tuple)):
            return [
                item if isinstance(item, (bool, int, float, str)) else str(item) for item in value
            ]
        return str(value)

    def _coerce_metric_attribute_value(self, value: Any) -> Any:
        if isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, (list, tuple)):
            return tuple(
                item if isinstance(item, (bool, int, float, str)) else str(item) for item in value
            )
        return str(value)

    def _map_severity(self, level: str) -> SeverityNumber:
        normalized = level.strip().lower()
        if normalized == "debug":
            return SeverityNumber.DEBUG
        if normalized in {"warning", "warn"}:
            return SeverityNumber.WARN
        if normalized == "error":
            return SeverityNumber.ERROR
        if normalized == "critical":
            return SeverityNumber.FATAL
        return SeverityNumber.INFO

    def _is_failure_status(self, status: str) -> bool:
        return status.lower() in {"error", "failed", "failure", "rejected"}

    def _record_duration(
        self,
        metric_name: str,
        *,
        metrics: dict[str, Any],
        attributes: dict[str, str],
        description: str,
    ) -> None:
        duration = self._extract_duration_seconds(metrics)
        if duration is None:
            return

        histogram = self._get_histogram(metric_name, unit="s", description=description)
        histogram.record(duration, attributes)

    def _extract_duration_seconds(self, metrics: dict[str, Any]) -> float | None:
        for key in ("duration_seconds", "total_elapsed_seconds", "elapsed_seconds"):
            value = metrics.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        return None

    def _record_failure(
        self,
        *,
        event_name: str,
        status: str | None,
        error: str | None = None,
    ) -> None:
        if not (error or (status and self._is_failure_status(status))):
            return

        counter = self._get_counter(
            "phlo.errors",
            description="Number of failed Phlo workflow events",
        )
        counter.add(1, {"event": event_name, "status": status or "error"})

    def _datetime_to_unix_nanos(self, value: datetime) -> int:
        return int(value.timestamp() * 1_000_000_000)

    def _resolve_log_context(self, event: LogEvent) -> tuple[int | None, int | None, Any | None]:
        span_context = get_current_span().get_span_context()
        trace_id = span_id = trace_flags = None
        if span_context.is_valid:
            trace_id = span_context.trace_id
            span_id = span_context.span_id
            trace_flags = span_context.trace_flags

        metadata_trace_id = self._parse_trace_identifier(event.metadata.get("trace_id"))
        metadata_span_id = self._parse_trace_identifier(event.metadata.get("span_id"))
        if metadata_trace_id is not None:
            trace_id = metadata_trace_id
        if metadata_span_id is not None:
            span_id = metadata_span_id
        return trace_id, span_id, trace_flags

    def _parse_trace_identifier(self, value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if not isinstance(value, str):
            return None

        raw = value.strip().lower()
        if not raw:
            return None
        try:
            if raw.startswith("0x"):
                return int(raw, 16)
            return int(raw, 16)
        except ValueError:
            return None

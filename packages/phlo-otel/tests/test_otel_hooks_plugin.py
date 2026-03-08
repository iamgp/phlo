"""Tests for the OTel hook plugin."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from opentelemetry.trace import get_current_span

from phlo.hooks.emitters import TelemetryEventContext, TelemetryEventEmitter
from phlo.hooks.events import (
    DataMigrationEvent,
    HookCorrelation,
    IngestionEvent,
    LineageEvent,
    LogEvent,
    PublishEvent,
    QualityResultEvent,
    SchemaMigrationEvent,
    ServiceLifecycleEvent,
    TelemetryEvent,
    TransformEvent,
)

from phlo_otel.hooks_plugin import OtelHookPlugin


@pytest.fixture()
def plugin() -> OtelHookPlugin:
    return OtelHookPlugin()


@pytest.fixture(autouse=True)
def _mock_otel(monkeypatch):
    """Prevent real OTel provider init; stub tracer and meter."""
    monkeypatch.setattr("phlo_otel.provider._initialized", True)


class TestOtelHookPlugin:
    def test_metadata(self, plugin: OtelHookPlugin):
        assert plugin.metadata.name == "otel"

    def test_registers_otel_hooks(self, plugin: OtelHookPlugin):
        hooks = plugin.get_hooks()
        assert len(hooks) == 10
        names = {h.hook_name for h in hooks}
        assert names == {
            "otel_ingestion",
            "otel_transform",
            "otel_quality",
            "otel_lineage",
            "otel_publish",
            "otel_service_lifecycle",
            "otel_schema_migration",
            "otel_data_migration",
            "otel_telemetry",
            "otel_log_record",
        }

    def test_ignores_wrong_event_type(self, plugin: OtelHookPlugin):
        wrong = TransformEvent(event_type="transform.start", tool="dbt")
        plugin._handle_ingestion(wrong)  # should not raise

    @patch("phlo_otel.hooks_plugin.get_meter")
    @patch("phlo_otel.hooks_plugin.get_tracer")
    def test_ingestion_creates_span(self, mock_tracer_fn, mock_meter_fn, plugin):
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span
        mock_tracer_fn.return_value = mock_tracer

        mock_counter = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_counter.return_value = mock_counter
        mock_meter_fn.return_value = mock_meter

        event = IngestionEvent(
            event_type="ingestion.complete",
            asset_key="dlt_glucose_entries",
            table_name="glucose_entries",
            group_name="nightscout",
            status="success",
            metrics={"rows_loaded": 500},
        )
        plugin._handle_ingestion(event)

        mock_tracer.start_as_current_span.assert_called_once()
        call_args = mock_tracer.start_as_current_span.call_args
        assert "ingestion.glucose_entries" in call_args[0]
        assert call_args.kwargs["attributes"]["phlo.stage"] == "ingestion"

        assert mock_meter.create_counter.call_count == 2
        assert mock_counter.add.call_count == 2

    @patch("phlo_otel.hooks_plugin.get_meter")
    @patch("phlo_otel.hooks_plugin.get_tracer")
    def test_ingestion_uses_correlation_as_parent_context(
        self, mock_tracer_fn, mock_meter_fn, plugin
    ):
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span
        mock_tracer_fn.return_value = mock_tracer

        mock_meter = MagicMock()
        mock_meter.create_counter.return_value = MagicMock()
        mock_meter_fn.return_value = mock_meter

        event = IngestionEvent(
            event_type="ingestion.complete",
            asset_key="dlt_glucose_entries",
            table_name="glucose_entries",
            group_name="nightscout",
            run_id="run-123",
            partition_key="2026-03-08",
            correlation=HookCorrelation(
                trace_id="abc123",
                span_id="def456",
                job_name="daily_ingestion",
            ),
        )

        plugin._handle_ingestion(event)

        _, kwargs = mock_tracer.start_as_current_span.call_args
        assert kwargs["context"] is not None
        mock_span.set_attribute.assert_any_call("phlo.run_id", "run-123")
        mock_span.set_attribute.assert_any_call("phlo.partition_key", "2026-03-08")
        mock_span.set_attribute.assert_any_call("phlo.job_name", "daily_ingestion")

    def test_build_parent_context_derives_stable_trace_from_run_id(self, plugin):
        first = plugin._build_parent_context(HookCorrelation(run_id="run-123"))
        second = plugin._build_parent_context(HookCorrelation(run_id="run-123"))

        assert first is not None
        assert second is not None
        first_context = get_current_span(first).get_span_context()
        second_context = get_current_span(second).get_span_context()
        assert first_context.is_valid
        assert second_context.is_valid
        assert first_context.trace_id == second_context.trace_id
        assert first_context.span_id == second_context.span_id

    def test_build_parent_context_uses_request_id_when_run_id_missing(self, plugin):
        context = plugin._build_parent_context(HookCorrelation(request_id="req-99"))

        assert context is not None
        span_context = get_current_span(context).get_span_context()
        assert span_context.is_valid

    @patch("phlo_otel.hooks_plugin.get_meter")
    @patch("phlo_otel.hooks_plugin.get_tracer")
    def test_ingestion_preserves_zero_rows_loaded(self, mock_tracer_fn, mock_meter_fn, plugin):
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span
        mock_tracer_fn.return_value = mock_tracer

        mock_runs_counter = MagicMock()
        mock_rows_counter = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_counter.side_effect = [mock_runs_counter, mock_rows_counter]
        mock_meter_fn.return_value = mock_meter

        event = IngestionEvent(
            event_type="ingestion.complete",
            asset_key="dlt_glucose_entries",
            table_name="glucose_entries",
            group_name="nightscout",
            status="success",
            metrics={"rows_loaded": 0},
        )

        plugin._handle_ingestion(event)

        mock_rows_counter.add.assert_called_once_with(0, {"table_name": "glucose_entries"})

    @patch("phlo_otel.hooks_plugin.get_meter")
    @patch("phlo_otel.hooks_plugin.get_tracer")
    def test_ingestion_records_duration_histogram(self, mock_tracer_fn, mock_meter_fn, plugin):
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span
        mock_tracer_fn.return_value = mock_tracer

        mock_runs_counter = MagicMock()
        mock_rows_counter = MagicMock()
        mock_histogram = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_counter.side_effect = [mock_runs_counter, mock_rows_counter]
        mock_meter.create_histogram.return_value = mock_histogram
        mock_meter_fn.return_value = mock_meter

        event = IngestionEvent(
            event_type="ingestion.complete",
            asset_key="dlt_glucose_entries",
            table_name="glucose_entries",
            group_name="nightscout",
            status="success",
            metrics={"rows_loaded": 5, "total_elapsed_seconds": 3.25},
        )

        plugin._handle_ingestion(event)

        mock_histogram.record.assert_called_once_with(
            3.25,
            {"table_name": "glucose_entries", "status": "success"},
        )

    @patch("phlo_otel.hooks_plugin.get_meter")
    @patch("phlo_otel.hooks_plugin.get_tracer")
    def test_quality_fail_sets_error_status(self, mock_tracer_fn, mock_meter_fn, plugin):
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span
        mock_tracer_fn.return_value = mock_tracer

        mock_meter = MagicMock()
        mock_meter.create_counter.return_value = MagicMock()
        mock_meter_fn.return_value = mock_meter

        event = QualityResultEvent(
            event_type="quality.result",
            asset_key="dlt_glucose_entries",
            check_name="not_null_glucose",
            passed=False,
            severity="error",
        )
        plugin._handle_quality(event)

        mock_span.set_status.assert_called_once()

    @patch("phlo_otel.hooks_plugin.get_meter")
    @patch("phlo_otel.hooks_plugin.get_tracer")
    def test_lineage_creates_span_and_counters(self, mock_tracer_fn, mock_meter_fn, plugin):
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span
        mock_tracer_fn.return_value = mock_tracer

        mock_events_counter = MagicMock()
        mock_edges_counter = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_counter.side_effect = [mock_events_counter, mock_edges_counter]
        mock_meter_fn.return_value = mock_meter

        event = LineageEvent(
            event_type="lineage.edges",
            edges=[("bronze.orders", "silver.orders"), ("silver.orders", "gold.orders")],
            asset_keys=["silver.orders", "gold.orders"],
            metadata={"pipeline": "orders"},
            tags={"tool": "dbt", "target": "warehouse"},
        )

        plugin._handle_lineage(event)

        mock_tracer.start_as_current_span.assert_called_once_with(
            "lineage.edges",
            attributes={
                "phlo.event_type": "lineage.edges",
                "phlo.stage": "lineage",
                "phlo.operation": "edges",
                "phlo.edge_count": 2,
                "phlo.asset_count": 2,
            },
            context=None,
        )
        mock_events_counter.add.assert_called_once_with(1, {"tool": "dbt", "target": "warehouse"})
        mock_edges_counter.add.assert_called_once_with(2, {"tool": "dbt", "target": "warehouse"})

    @patch("phlo_otel.hooks_plugin.get_meter")
    @patch("phlo_otel.hooks_plugin.get_tracer")
    def test_publish_creates_span_and_counters(self, mock_tracer_fn, mock_meter_fn, plugin):
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span
        mock_tracer_fn.return_value = mock_tracer

        mock_runs_counter = MagicMock()
        mock_tables_counter = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_counter.side_effect = [mock_runs_counter, mock_tables_counter]
        mock_meter_fn.return_value = mock_meter

        event = PublishEvent(
            event_type="publish.end",
            asset_key="gold.orders",
            target_system="clickhouse",
            tables={"gold.orders": "analytics.orders"},
            status="success",
            metrics={"rows_written": 200},
        )

        plugin._handle_publish(event)

        mock_tracer.start_as_current_span.assert_called_once()
        call_args = mock_tracer.start_as_current_span.call_args
        assert call_args.kwargs["attributes"]["phlo.stage"] == "publish"
        assert call_args.kwargs["attributes"]["phlo.system"] == "clickhouse"
        assert call_args.kwargs["attributes"]["phlo.operation"] == "publish"
        mock_runs_counter.add.assert_called_once_with(
            1, {"target_system": "clickhouse", "status": "success"}
        )
        mock_tables_counter.add.assert_called_once_with(1, {"target_system": "clickhouse"})
        mock_span.set_attribute.assert_any_call("phlo.metrics.rows_written", 200)

    @patch("phlo_otel.hooks_plugin.get_meter")
    @patch("phlo_otel.hooks_plugin.get_tracer")
    def test_publish_failure_records_error_and_duration(
        self, mock_tracer_fn, mock_meter_fn, plugin
    ):
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span
        mock_tracer_fn.return_value = mock_tracer

        mock_runs_counter = MagicMock()
        mock_error_counter = MagicMock()
        mock_histogram = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_counter.side_effect = [mock_error_counter, mock_runs_counter]
        mock_meter.create_histogram.return_value = mock_histogram
        mock_meter_fn.return_value = mock_meter

        event = PublishEvent(
            event_type="publish.end",
            asset_key="gold.orders",
            target_system="clickhouse",
            status="failure",
            metrics={"elapsed_seconds": 1.75},
            error="warehouse unavailable",
        )

        plugin._handle_publish(event)

        mock_error_counter.add.assert_called_once_with(1, {"event": "publish", "status": "failure"})
        mock_histogram.record.assert_called_once_with(
            1.75,
            {"target_system": "clickhouse", "status": "failure"},
        )

    @patch("phlo_otel.hooks_plugin.get_meter")
    @patch("phlo_otel.hooks_plugin.get_tracer")
    def test_service_lifecycle_sets_error_status_on_failure(
        self, mock_tracer_fn, mock_meter_fn, plugin
    ):
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span
        mock_tracer_fn.return_value = mock_tracer

        mock_counter = MagicMock()
        mock_error_counter = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_counter.side_effect = [mock_error_counter, mock_counter]
        mock_meter_fn.return_value = mock_meter

        event = ServiceLifecycleEvent(
            event_type="service.post_start",
            service_name="dagster-webserver",
            phase="post_start",
            status="failure",
            tags={"service": "dagster-webserver"},
        )

        plugin._handle_service_lifecycle(event)

        call_args = mock_tracer.start_as_current_span.call_args
        assert call_args.kwargs["attributes"]["phlo.stage"] == "service"
        assert call_args.kwargs["attributes"]["phlo.operation"] == "post_start"
        mock_span.set_status.assert_called_once()
        mock_error_counter.add.assert_called_once_with(
            1,
            {
                "event": "service_lifecycle",
                "status": "failure",
            },
        )
        mock_counter.add.assert_called_once_with(
            1,
            {
                "service_name": "dagster-webserver",
                "phase": "post_start",
                "status": "failure",
            },
        )

    @patch("phlo_otel.hooks_plugin.get_meter")
    @patch("phlo_otel.hooks_plugin.get_tracer")
    def test_schema_and_data_migrations_emit_metrics(self, mock_tracer_fn, mock_meter_fn, plugin):
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span
        mock_tracer_fn.return_value = mock_tracer

        schema_runs = MagicMock()
        schema_changes = MagicMock()
        data_runs = MagicMock()
        data_rows_read = MagicMock()
        data_rows_written = MagicMock()
        data_duration = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_counter.side_effect = [
            schema_runs,
            schema_changes,
            data_runs,
            data_rows_read,
            data_rows_written,
        ]
        mock_meter.create_histogram.return_value = data_duration
        mock_meter_fn.return_value = mock_meter

        schema_event = SchemaMigrationEvent(
            event_type="schema_migration.applied",
            table_name="silver.orders",
            classification="minor",
            change_count=3,
            status="applied",
        )
        data_event = DataMigrationEvent(
            event_type="data_migration.completed",
            migration_name="backfill_orders",
            source_type="postgres",
            destination_table="silver.orders",
            status="completed",
            rows_read=100,
            rows_written=95,
            chunk_index=2,
            metrics={"duration_seconds": 8.5},
        )

        plugin._handle_schema_migration(schema_event)
        plugin._handle_data_migration(data_event)

        schema_call = mock_tracer.start_as_current_span.call_args_list[0]
        data_call = mock_tracer.start_as_current_span.call_args_list[1]
        assert schema_call.kwargs["attributes"]["phlo.stage"] == "migration"
        assert schema_call.kwargs["attributes"]["phlo.system"] == "schema"
        assert data_call.kwargs["attributes"]["phlo.stage"] == "migration"
        assert data_call.kwargs["attributes"]["phlo.system"] == "postgres"
        schema_changes.add.assert_called_once_with(
            3, {"classification": "minor", "status": "applied"}
        )
        data_rows_read.add.assert_called_once_with(
            100, {"source_type": "postgres", "status": "completed"}
        )
        data_rows_written.add.assert_called_once_with(
            95, {"source_type": "postgres", "status": "completed"}
        )
        data_duration.record.assert_called_once_with(
            8.5, {"source_type": "postgres", "status": "completed"}
        )

    @patch("phlo_otel.hooks_plugin.get_meter")
    def test_telemetry_gauge(self, mock_meter_fn, plugin):
        mock_gauge = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_gauge.return_value = mock_gauge
        mock_meter_fn.return_value = mock_meter

        event = TelemetryEvent(
            event_type="telemetry.metric",
            name="ingestion_lag_seconds",
            value=12.5,
            unit="s",
            payload={"source": "nightscout"},
        )
        plugin._handle_telemetry(event)

        mock_meter.create_gauge.assert_called_once()
        mock_gauge.set.assert_called_once_with(12.5, {"source": "nightscout"})

    @patch("phlo_otel.hooks_plugin.get_meter")
    def test_standard_instruments_are_cached(self, mock_meter_fn, plugin):
        mock_meter = MagicMock()
        mock_runs_counter = MagicMock()
        mock_rows_counter = MagicMock()
        mock_meter.create_counter.side_effect = [mock_runs_counter, mock_rows_counter]
        mock_meter_fn.return_value = mock_meter

        first = IngestionEvent(
            event_type="ingestion.complete",
            asset_key="dlt_glucose_entries",
            table_name="glucose_entries",
            group_name="nightscout",
            status="success",
            metrics={"rows_loaded": 5},
        )
        second = IngestionEvent(
            event_type="ingestion.complete",
            asset_key="dlt_glucose_entries",
            table_name="glucose_entries",
            group_name="nightscout",
            status="success",
            metrics={"rows_loaded": 7},
        )

        with patch("phlo_otel.hooks_plugin.get_tracer") as mock_tracer_fn:
            mock_span = MagicMock()
            mock_span.__enter__ = MagicMock(return_value=mock_span)
            mock_span.__exit__ = MagicMock(return_value=False)
            mock_tracer = MagicMock()
            mock_tracer.start_as_current_span.return_value = mock_span
            mock_tracer_fn.return_value = mock_tracer

            plugin._handle_ingestion(first)
            plugin._handle_ingestion(second)

        assert mock_meter.create_counter.call_count == 2
        assert mock_runs_counter.add.call_count == 2
        assert mock_rows_counter.add.call_count == 2

    @patch("phlo_otel.hooks_plugin.get_meter")
    def test_telemetry_counter_metric_kind(self, mock_meter_fn, plugin):
        mock_counter = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_counter.return_value = mock_counter
        mock_meter_fn.return_value = mock_meter

        event = TelemetryEvent(
            event_type="telemetry.metric",
            name="rows_written",
            value=42,
            unit="rows",
            payload={"metric_kind": "counter", "source": "nightscout"},
        )

        plugin._handle_telemetry(event)

        mock_meter.create_counter.assert_called_once()
        mock_counter.add.assert_called_once_with(42, {"source": "nightscout"})

    @patch("phlo_otel.hooks_plugin.get_meter")
    def test_telemetry_histogram_metric_kind(self, mock_meter_fn, plugin):
        mock_histogram = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_histogram.return_value = mock_histogram
        mock_meter_fn.return_value = mock_meter

        event = TelemetryEvent(
            event_type="telemetry.metric",
            name="duration_seconds",
            value=1.5,
            unit="s",
            payload={"otel_metric_kind": "histogram", "source": "nightscout"},
        )

        plugin._handle_telemetry(event)

        mock_meter.create_histogram.assert_called_once()
        mock_histogram.record.assert_called_once_with(1.5, {"source": "nightscout"})

    @patch("phlo_otel.hooks_plugin.get_meter")
    def test_telemetry_normalizes_sequence_attributes(self, mock_meter_fn, plugin):
        mock_gauge = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_gauge.return_value = mock_gauge
        mock_meter_fn.return_value = mock_meter

        event = TelemetryEvent(
            event_type="telemetry.metric",
            name="transform.duration_seconds",
            value=2.5,
            unit="seconds",
            payload={"models": ["orders", "customers"]},
        )

        plugin._handle_telemetry(event)

        mock_gauge.set.assert_called_once_with(2.5, {})

    @patch("phlo_otel.hooks_plugin.get_meter")
    def test_telemetry_filters_high_cardinality_attributes(self, mock_meter_fn, plugin):
        mock_gauge = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_gauge.return_value = mock_gauge
        mock_meter_fn.return_value = mock_meter

        event = TelemetryEvent(
            event_type="telemetry.metric",
            name="ingestion_lag_seconds",
            value=12.5,
            unit="s",
            payload={"source": "nightscout", "run_id": "run-123", "asset_key": "raw.orders"},
        )

        plugin._handle_telemetry(event)

        mock_gauge.set.assert_called_once_with(12.5, {"source": "nightscout"})

    @patch("phlo_otel.hooks_plugin.get_meter")
    def test_telemetry_skips_non_numeric(self, mock_meter_fn, plugin):
        event = TelemetryEvent(
            event_type="telemetry.log",
            name="some_log",
            value="not a number",
        )
        plugin._handle_telemetry(event)
        mock_meter_fn.assert_not_called()

    @patch("phlo_otel.hooks_plugin.get_meter")
    def test_telemetry_skips_numeric_logs(self, mock_meter_fn, plugin):
        event = TelemetryEvent(
            event_type="telemetry.log",
            name="some_log",
            value=1,
            payload={"source": "nightscout"},
        )

        plugin._handle_telemetry(event)

        mock_meter_fn.assert_not_called()

    @patch("phlo_otel.hooks_plugin.get_meter")
    def test_maintenance_telemetry_promotes_standard_metrics(
        self, mock_meter_fn, monkeypatch, plugin
    ):
        mock_runs_counter = MagicMock()
        mock_duration_histogram = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_counter.return_value = mock_runs_counter
        mock_meter.create_histogram.return_value = mock_duration_histogram
        mock_meter_fn.return_value = mock_meter

        class RecordingBus:
            def __init__(self) -> None:
                self.events: list[object] = []

            def emit(self, event: object) -> None:
                self.events.append(event)

        bus = RecordingBus()
        monkeypatch.setattr("phlo.hooks.emitters.get_hook_bus", lambda: bus)
        telemetry = TelemetryEventEmitter(
            TelemetryEventContext(
                tags={
                    "operation": "expire_snapshots",
                    "namespace": "raw",
                    "status": "success",
                }
            )
        )
        telemetry.emit_metric(
            name="iceberg.maintenance.run",
            value=1,
            unit="run",
            payload={"operation": "expire_snapshots", "namespace": "raw", "status": "success"},
        )
        telemetry.emit_metric(
            name="iceberg.maintenance.duration_seconds",
            value=3.5,
            unit="seconds",
            payload={"operation": "expire_snapshots", "namespace": "raw", "status": "success"},
        )

        for event in bus.events:
            plugin._handle_telemetry(event)

        mock_meter.create_counter.assert_called_once_with(
            "phlo.maintenance.runs",
            unit="run",
            description="Maintenance metric derived from iceberg.maintenance.run",
        )
        mock_runs_counter.add.assert_called_once_with(
            1,
            {"operation": "expire_snapshots", "namespace": "raw", "status": "success"},
        )
        mock_meter.create_histogram.assert_called_once_with(
            "phlo.maintenance.duration",
            unit="seconds",
            description="Maintenance metric derived from iceberg.maintenance.duration_seconds",
        )
        mock_duration_histogram.record.assert_called_once_with(
            3.5,
            {"operation": "expire_snapshots", "namespace": "raw", "status": "success"},
        )

    @patch("phlo_otel.hooks_plugin.get_meter")
    def test_unknown_telemetry_keeps_generic_metric_namespace(self, mock_meter_fn, plugin):
        mock_gauge = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_gauge.return_value = mock_gauge
        mock_meter_fn.return_value = mock_meter

        event = TelemetryEvent(
            event_type="telemetry.metric",
            name="custom.backlog",
            value=9,
            unit="items",
            payload={"operation": "sync"},
        )

        plugin._handle_telemetry(event)

        mock_meter.create_gauge.assert_called_once_with(
            "phlo.telemetry.custom.backlog",
            unit="items",
            description="Telemetry metric: custom.backlog",
        )
        mock_gauge.set.assert_called_once_with(9, {"operation": "sync"})

    @patch("phlo_otel.hooks_plugin.get_log_emitter")
    def test_log_record_exports_to_otel_logs(self, mock_get_log_emitter, plugin):
        mock_emitter = MagicMock()
        mock_get_log_emitter.return_value = mock_emitter

        event = LogEvent(
            event_type="log.record",
            logger="phlo.tests.logging",
            level="warning",
            message="lag spike detected",
            service="phlo-worker",
            run_id="run-7",
            metadata={"trace_id": "abc123", "attempt": 2},
            tags={"team": "analytics"},
        )

        plugin._handle_log_record(event)

        mock_get_log_emitter.assert_called_once()
        emitted_record = mock_emitter.emit.call_args.args[0]
        assert emitted_record.body == "lag spike detected"
        assert emitted_record.severity_text == "WARNING"
        assert emitted_record.trace_id == int("abc123", 16)
        assert emitted_record.attributes["phlo.stage"] == "log"
        assert emitted_record.attributes["phlo.service"] == "phlo-worker"
        assert emitted_record.attributes["phlo.system"] == "phlo-worker"
        assert emitted_record.attributes["phlo.run_id"] == "run-7"
        assert emitted_record.attributes["phlo.tag.team"] == "analytics"
        assert emitted_record.attributes["phlo.metadata.trace_id"] == "abc123"

    @patch("phlo_otel.hooks_plugin.get_log_emitter")
    def test_log_record_uses_operation_tag_as_semantic_attribute(
        self, mock_get_log_emitter, plugin
    ):
        mock_emitter = MagicMock()
        mock_get_log_emitter.return_value = mock_emitter

        event = LogEvent(
            event_type="log.record",
            logger="phlo.tests.logging",
            level="info",
            message="maintenance complete",
            tags={"operation": "expire_snapshots"},
        )

        plugin._handle_log_record(event)

        emitted_record = mock_emitter.emit.call_args.args[0]
        assert emitted_record.attributes["phlo.operation"] == "expire_snapshots"

    @patch("phlo_otel.hooks_plugin.get_log_emitter")
    def test_log_record_uses_correlation_for_trace_context(self, mock_get_log_emitter, plugin):
        mock_emitter = MagicMock()
        mock_get_log_emitter.return_value = mock_emitter

        event = LogEvent(
            event_type="log.record",
            logger="phlo.tests.logging",
            level="info",
            message="pipeline started",
            correlation=HookCorrelation(
                trace_id="abc123",
                span_id="def456",
                run_id="run-42",
                asset_key="silver.orders",
            ),
        )

        plugin._handle_log_record(event)

        emitted_record = mock_emitter.emit.call_args.args[0]
        assert emitted_record.trace_id == int("abc123", 16)
        assert emitted_record.span_id == int("def456", 16)
        assert emitted_record.attributes["phlo.run_id"] == "run-42"
        assert emitted_record.attributes["phlo.asset_key"] == "silver.orders"

    @patch("phlo_otel.hooks_plugin.get_log_emitter")
    def test_log_record_derives_trace_context_from_run_id(self, mock_get_log_emitter, plugin):
        mock_emitter = MagicMock()
        mock_get_log_emitter.return_value = mock_emitter

        event = LogEvent(
            event_type="log.record",
            logger="phlo.tests.logging",
            level="info",
            message="pipeline heartbeat",
            run_id="run-777",
        )

        plugin._handle_log_record(event)

        emitted_record = mock_emitter.emit.call_args.args[0]
        assert emitted_record.trace_id is not None
        assert emitted_record.span_id is not None
        assert emitted_record.attributes["phlo.run_id"] == "run-777"

    def test_parse_trace_identifier_treats_all_digit_strings_as_hex(self, plugin):
        assert plugin._parse_trace_identifier("1234567890123456") == int("1234567890123456", 16)

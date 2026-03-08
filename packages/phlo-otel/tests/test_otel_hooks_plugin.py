"""Tests for the OTel hook plugin."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from phlo.hooks.events import (
    DataMigrationEvent,
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

        assert mock_meter.create_counter.call_count == 2
        assert mock_counter.add.call_count == 2

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
                "phlo.edge_count": 2,
                "phlo.asset_count": 2,
            },
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

        mock_gauge.set.assert_called_once_with(2.5, {"models": ("orders", "customers")})

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
        assert emitted_record.attributes["phlo.service"] == "phlo-worker"
        assert emitted_record.attributes["phlo.run_id"] == "run-7"
        assert emitted_record.attributes["phlo.tag.team"] == "analytics"
        assert emitted_record.attributes["phlo.metadata.trace_id"] == "abc123"

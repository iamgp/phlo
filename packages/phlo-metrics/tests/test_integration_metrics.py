"""Integration tests for phlo-metrics."""

from datetime import datetime, timezone

import pytest

pytestmark = pytest.mark.integration


def test_metrics_collector_initializes():
    """Test that MetricsCollector initializes correctly."""
    from phlo_metrics import MetricsCollector, get_metrics_collector

    collector = get_metrics_collector()
    assert isinstance(collector, MetricsCollector)
    assert collector._cache is not None


def test_summary_metrics_defaults():
    """Test SummaryMetrics has correct defaults."""
    from phlo_metrics import SummaryMetrics

    metrics = SummaryMetrics()
    assert metrics.total_runs_24h == 0
    assert metrics.successful_runs_24h == 0
    assert metrics.failed_runs_24h == 0
    assert metrics.assets_by_status == {"success": 0, "warning": 0, "failure": 0}


def test_asset_metrics_defaults():
    """Test AssetMetrics has correct defaults."""
    from phlo_metrics import AssetMetrics

    metrics = AssetMetrics(asset_name="test_asset")
    assert metrics.asset_name == "test_asset"
    assert metrics.last_run is None
    assert metrics.last_10_runs == []
    assert metrics.average_duration == 0.0
    assert metrics.failure_rate == 0.0


def test_run_metrics_creation():
    """Test RunMetrics creation."""
    from datetime import datetime, timezone
    from phlo_metrics import RunMetrics

    now = datetime.now(timezone.utc)
    run = RunMetrics(
        asset_name="test_asset",
        run_id="run123",
        start_time=now,
        status="success",
        rows_processed=1000,
    )

    assert run.asset_name == "test_asset"
    assert run.run_id == "run123"
    assert run.status == "success"
    assert run.rows_processed == 1000


def test_collector_caching():
    """Test that MetricsCollector uses caching."""
    from phlo_metrics import MetricsCollector, SummaryMetrics

    collector = MetricsCollector()

    # Manually inject cache
    cache_key = "summary_24h"
    cached_metrics = SummaryMetrics(total_runs_24h=42)
    collector._cache[cache_key] = cached_metrics

    # Collect should return cached value
    result = collector.collect_summary(period_hours=24)
    assert result.total_runs_24h == 42


def test_telemetry_recorder_exists():
    """Test TelemetryRecorder is exported and can be instantiated."""
    from phlo_metrics import TelemetryRecorder

    recorder = TelemetryRecorder()
    assert recorder is not None


def test_metrics_exports():
    """Test that phlo-metrics exports required classes."""
    import phlo_metrics

    assert hasattr(phlo_metrics, "MetricsCollector")
    assert hasattr(phlo_metrics, "get_metrics_collector")
    assert hasattr(phlo_metrics, "SummaryMetrics")
    assert hasattr(phlo_metrics, "AssetMetrics")
    assert hasattr(phlo_metrics, "RunMetrics")
    assert hasattr(phlo_metrics, "TelemetryRecorder")


def test_hooks_plugin_exists():
    """Test that metrics hooks plugin exists."""
    from phlo_metrics.hooks_plugin import MetricsHookPlugin

    plugin = MetricsHookPlugin()
    assert plugin is not None
    assert hasattr(plugin, "metadata")


def test_get_asset_runs_from_postgres_success(monkeypatch):
    """Collector returns normalized Dagster run rows."""
    from phlo_metrics.collector import MetricsCollector
    import phlo_metrics.collector as collector_module

    class FakeCursor:
        last_params = None

        def execute(self, _query, _params):
            FakeCursor.last_params = _params
            return None

        def fetchall(self):
            return [
                {
                    "run_id": "run-123",
                    "start_time": datetime(2026, 2, 1, 10, 0, tzinfo=timezone.utc),
                    "end_time": datetime(2026, 2, 1, 10, 5, tzinfo=timezone.utc),
                    "status": "SUCCESS",
                }
            ]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeConnection:
        def cursor(self, **_kwargs):
            return FakeCursor()

        def close(self):
            return None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(collector_module.psycopg2, "connect", lambda **_kwargs: FakeConnection())

    collector = MetricsCollector()
    runs = collector._get_asset_runs_from_postgres("dlt_users", limit=5)

    assert len(runs) == 1
    assert runs[0].run_id == "run-123"
    assert runs[0].status == "success"
    assert runs[0].duration_seconds == 300.0
    assert FakeCursor.last_params is not None
    assert FakeCursor.last_params[1] == r"%dlt\_users%"


def test_get_iceberg_table_stats_dependency_unavailable(monkeypatch):
    """Collector raises explicit dependency error when query engine is unavailable."""
    from phlo_metrics.collector import MetricsCollector, MetricsDependencyError

    collector = MetricsCollector()
    monkeypatch.setattr(
        collector,
        "_load_query_engine",
        lambda: (_ for _ in ()).throw(MetricsDependencyError("missing")),
    )
    with pytest.raises(MetricsDependencyError):
        collector._get_iceberg_table_stats("dlt_users")


def test_get_iceberg_table_stats_success(monkeypatch):
    """Collector returns row/byte stats from Trino metadata tables."""
    from phlo_metrics.collector import MetricsCollector

    class FakeQueryEngine:
        def __init__(self, rows):
            self.rows = rows
            self.queries = []

        def execute(self, sql, params=None, schema=None):
            self.queries.append((sql, schema))
            return self.rows.pop(0)

    collector = MetricsCollector()
    collector.settings.metrics_query_catalog = "iceberg"
    monkeypatch.setattr(
        collector,
        "_load_query_engine",
        lambda: FakeQueryEngine([[("bronze",)], [(1024, 42)]]),
    )
    stats = collector._get_iceberg_table_stats("dlt_users")

    assert stats == {"total_bytes": 1024, "row_count": 42}


def test_get_iceberg_table_stats_malformed_response(monkeypatch):
    """Collector raises typed malformed response error for invalid Trino payload."""
    from phlo_metrics.collector import MetricsCollector, MetricsMalformedResponseError

    class FakeQueryEngine:
        def __init__(self, rows):
            self.rows = rows

        def execute(self, _sql, params=None, schema=None):
            return self.rows.pop(0)

    collector = MetricsCollector()
    collector.settings.metrics_query_catalog = "iceberg"
    monkeypatch.setattr(
        collector,
        "_load_query_engine",
        lambda: FakeQueryEngine([[("bronze",)], [("bad-shape",)]]),
    )
    with pytest.raises(MetricsMalformedResponseError):
        collector._get_iceberg_table_stats("dlt_users")

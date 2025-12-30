"""Integration tests for phlo-metrics."""

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
    from datetime import datetime
    from phlo_metrics import RunMetrics

    now = datetime.utcnow()
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

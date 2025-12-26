"""Tests for observability features (metrics, alerting, lineage)."""

import json
import tempfile
from pathlib import Path

import pytest

from phlo_alerting import Alert, AlertSeverity, get_alert_manager
from phlo_alerting.destinations.email import EmailAlertDestination
from phlo_alerting.destinations.pagerduty import PagerDutyAlertDestination
from phlo_alerting.destinations.slack import SlackAlertDestination
from phlo_lineage import LineageGraph
from phlo_metrics import AssetMetrics, SummaryMetrics


class TestMetricsCollector:
    """Tests for metrics collection."""

    def test_summary_metrics_creation(self):
        """Test creating summary metrics."""
        metrics = SummaryMetrics(
            total_runs_24h=100,
            successful_runs_24h=95,
            failed_runs_24h=5,
            total_rows_processed_24h=1000000,
            total_bytes_written_24h=5000000,
            p50_duration_seconds=10.5,
            p95_duration_seconds=25.0,
            p99_duration_seconds=50.0,
            active_assets_count=42,
        )

        assert metrics.total_runs_24h == 100
        assert metrics.successful_runs_24h == 95
        assert metrics.failed_runs_24h == 5
        assert metrics.total_rows_processed_24h == 1000000
        assert metrics.p50_duration_seconds == 10.5

    def test_asset_metrics_creation(self):
        """Test creating asset-level metrics."""
        metrics = AssetMetrics(
            asset_name="glucose_entries",
            average_duration=15.5,
            failure_rate=0.05,
            average_rows_per_run=5000,
            data_growth_bytes=10000000,
        )

        assert metrics.asset_name == "glucose_entries"
        assert metrics.failure_rate == 0.05
        assert metrics.average_rows_per_run == 5000


class TestAlertManager:
    """Tests for alert management."""

    def test_alert_creation(self):
        """Test creating an alert."""
        alert = Alert(
            title="Test Alert",
            message="This is a test",
            severity=AlertSeverity.WARNING,
            asset_name="test_asset",
            run_id="run_123",
        )

        assert alert.title == "Test Alert"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.asset_name == "test_asset"
        assert alert.timestamp is not None

    def test_alert_manager_registration(self):
        """Test registering alert destinations."""
        manager = get_alert_manager()
        initial_count = len(manager.destinations)

        # Register a mock destination
        class MockDestination:
            def send(self, alert):
                return True

        manager.register_destination("mock", MockDestination())
        assert len(manager.destinations) >= initial_count

    def test_alert_severity_values(self):
        """Test alert severity enum."""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.ERROR.value == "error"
        assert AlertSeverity.CRITICAL.value == "critical"

    def test_slack_payload_building(self):
        """Test Slack payload construction."""
        slack = SlackAlertDestination(webhook_url="https://hooks.slack.com/test")

        alert = Alert(
            title="Test Alert",
            message="This is a test",
            severity=AlertSeverity.ERROR,
            asset_name="test_asset",
            run_id="run_123",
        )

        payload = slack._build_payload(alert)
        assert "attachments" in payload
        assert len(payload["attachments"]) == 1
        assert payload["attachments"][0]["title"] == "Test Alert"

    def test_pagerduty_payload_building(self):
        """Test PagerDuty payload construction."""
        pagerduty = PagerDutyAlertDestination(integration_key="test_key")

        alert = Alert(
            title="Critical Alert",
            message="System failure",
            severity=AlertSeverity.CRITICAL,
            asset_name="critical_asset",
        )

        payload = pagerduty._build_payload(alert)
        assert payload["routing_key"] == "test_key"
        assert payload["event_action"] == "trigger"
        assert payload["payload"]["severity"] == "critical"
        assert "dedup_key" in payload

    def test_email_payload_building(self):
        """Test email content construction."""
        email = EmailAlertDestination(
            smtp_host="smtp.example.com",
            recipients=["test@example.com"],
        )

        alert = Alert(
            title="Email Test",
            message="Test email content",
            severity=AlertSeverity.WARNING,
            error_message="Something went wrong",
        )

        text_content = email._build_text(alert)
        assert "Email Test" in text_content
        assert "Test email content" in text_content
        assert "Something went wrong" in text_content

        html_content = email._build_html(alert)
        assert "Email Test" in html_content
        assert "<html>" in html_content
        assert "Test email content" in html_content


class TestLineageGraph:
    """Tests for lineage tracking."""

    def test_lineage_graph_creation(self):
        """Test creating a lineage graph."""
        graph = LineageGraph()
        assert len(graph.assets) == 0
        assert len(graph.edges) == 0

    def test_add_asset(self):
        """Test adding assets to graph."""
        graph = LineageGraph()
        graph.add_asset("glucose_entries", asset_type="ingestion")
        graph.add_asset("stg_glucose", asset_type="transform")

        assert "glucose_entries" in graph.assets
        assert "stg_glucose" in graph.assets
        assert graph.assets["glucose_entries"].asset_type == "ingestion"
        assert graph.assets["stg_glucose"].asset_type == "transform"

    def test_add_edge(self):
        """Test adding dependencies between assets."""
        graph = LineageGraph()
        graph.add_edge("glucose_entries", "stg_glucose")
        graph.add_edge("stg_glucose", "fct_glucose")

        assert "stg_glucose" in graph.edges["glucose_entries"]
        assert "fct_glucose" in graph.edges["stg_glucose"]

    def test_get_upstream(self):
        """Test finding upstream dependencies."""
        graph = LineageGraph()
        graph.add_edge("raw_data", "stage_data")
        graph.add_edge("stage_data", "transform_data")
        graph.add_edge("transform_data", "mart_data")

        upstream = graph.get_upstream("mart_data")
        assert "transform_data" in upstream
        assert "stage_data" in upstream
        assert "raw_data" in upstream

    def test_get_downstream(self):
        """Test finding downstream dependents."""
        graph = LineageGraph()
        graph.add_edge("raw_data", "stage_data")
        graph.add_edge("stage_data", "transform_data")
        graph.add_edge("transform_data", "mart_data")

        downstream = graph.get_downstream("raw_data")
        assert "stage_data" in downstream
        assert "transform_data" in downstream
        assert "mart_data" in downstream

    def test_get_impact(self):
        """Test impact analysis."""
        graph = LineageGraph()
        graph.add_asset("raw_data", asset_type="ingestion")
        graph.add_asset("stage_data", asset_type="transform")
        graph.add_asset("transform_data", asset_type="transform")
        graph.add_asset("mart_data", asset_type="publish")

        graph.add_edge("raw_data", "stage_data")
        graph.add_edge("stage_data", "transform_data")
        graph.add_edge("transform_data", "mart_data")

        impact = graph.get_impact("raw_data")
        assert impact["publishing_affected"] is True
        assert len(impact["affected_assets"]) == 3

    def test_ascii_tree_generation(self):
        """Test ASCII tree representation."""
        graph = LineageGraph()
        graph.add_edge("raw", "stage")
        graph.add_edge("stage", "transform")

        tree = graph.to_ascii_tree("stage", direction="both")
        assert "stage" in tree
        assert "raw" in tree or "transform" in tree

    def test_dot_format_generation(self):
        """Test Graphviz DOT format generation."""
        graph = LineageGraph()
        graph.add_edge("raw", "stage")
        graph.add_edge("stage", "transform")

        dot = graph.to_dot()
        assert "digraph" in dot
        assert "raw" in dot
        assert "stage" in dot
        assert "transform" in dot
        assert "->" in dot

    def test_mermaid_format_generation(self):
        """Test Mermaid diagram format generation."""
        graph = LineageGraph()
        graph.add_edge("raw", "stage")
        graph.add_edge("stage", "transform")

        mermaid = graph.to_mermaid()
        assert "graph TD" in mermaid
        assert "raw" in mermaid
        assert "stage" in mermaid
        assert "-->" in mermaid

    def test_json_format_generation(self):
        """Test JSON format generation."""
        graph = LineageGraph()
        graph.add_asset("raw", asset_type="ingestion")
        graph.add_asset("stage", asset_type="transform")
        graph.add_edge("raw", "stage")

        json_str = graph.to_json()
        data = json.loads(json_str)

        assert "assets" in data
        assert "edges" in data
        assert "raw" in data["assets"]
        assert "stage" in data["assets"]
        assert "stage" in data["edges"]["raw"]


class TestMetricsExport:
    """Tests for metrics export functionality."""

    def test_metrics_export_json(self):
        """Test exporting metrics to JSON."""
        from phlo_metrics.cli import _export_json

        metrics = SummaryMetrics(
            total_runs_24h=100,
            successful_runs_24h=95,
            failed_runs_24h=5,
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = Path(f.name)

        try:
            _export_json(metrics, output_path)
            assert output_path.exists()

            with open(output_path) as f:
                data = json.load(f)

            assert "total_runs_24h" in data
            assert data["total_runs_24h"] == 100
            assert "exported_at" in data
        finally:
            output_path.unlink()

    def test_format_bytes(self):
        """Test byte formatting."""
        from phlo_metrics.cli import _format_bytes

        assert _format_bytes(512) == "512.00 B"
        assert _format_bytes(1024) == "1.00 KB"
        assert _format_bytes(1024 * 1024) == "1.00 MB"
        assert _format_bytes(1024 * 1024 * 1024) == "1.00 GB"

    def test_parse_period(self):
        """Test period parsing."""
        from phlo_metrics.cli import _parse_period

        assert _parse_period("24h") == 24
        assert _parse_period("7d") == 168
        assert _parse_period("1w") == 168
        assert _parse_period("invalid") == 24  # default


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

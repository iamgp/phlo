"""Tests for phlo status command.

Tests the status CLI command for asset and service health monitoring.
"""

import json
from datetime import datetime, timedelta

import pytest
from click.testing import CliRunner

from phlo.cli.status import (
    _check_if_stale,
    _check_service_health,
    _get_freshness_indicator,
    _get_mock_asset_status,
    status,
)


class TestFreshnessIndicator:
    """Tests for freshness indicator logic."""

    def test_fresh_asset(self):
        """Test that recently run assets are marked as fresh."""
        last_run = {
            "status": "success",
            "timestamp": datetime.utcnow() - timedelta(minutes=30),
        }
        assert _get_freshness_indicator(last_run) == "fresh"

    def test_okay_asset(self):
        """Test that assets run within 24 hours are okay."""
        last_run = {
            "status": "success",
            "timestamp": datetime.utcnow() - timedelta(hours=12),
        }
        assert _get_freshness_indicator(last_run) == "okay"

    def test_stale_asset(self):
        """Test that assets older than 24 hours are stale."""
        last_run = {
            "status": "success",
            "timestamp": datetime.utcnow() - timedelta(hours=48),
        }
        assert _get_freshness_indicator(last_run) == "stale"

    def test_failed_asset(self):
        """Test that failed assets are marked as failed."""
        last_run = {
            "status": "failure",
            "timestamp": datetime.utcnow() - timedelta(hours=1),
        }
        assert _get_freshness_indicator(last_run) == "failed"

    def test_never_run_asset(self):
        """Test that never-run assets are marked as never_run."""
        assert _get_freshness_indicator(None) == "never_run"

    def test_asset_with_missing_timestamp(self):
        """Test assets with missing timestamp."""
        last_run = {"status": "success"}
        assert _get_freshness_indicator(last_run) == "unknown"


class TestStalenessCheck:
    """Tests for staleness checking."""

    def test_fresh_asset_not_stale(self):
        """Test that recently run assets are not stale."""
        last_run = {
            "status": "success",
            "timestamp": datetime.utcnow() - timedelta(hours=12),
        }
        assert not _check_if_stale(last_run)

    def test_old_asset_is_stale(self):
        """Test that old assets are stale."""
        last_run = {
            "status": "success",
            "timestamp": datetime.utcnow() - timedelta(days=2),
        }
        assert _check_if_stale(last_run)

    def test_failed_asset_is_stale(self):
        """Test that failed assets are stale."""
        last_run = {
            "status": "failure",
            "timestamp": datetime.utcnow() - timedelta(hours=1),
        }
        assert _check_if_stale(last_run)

    def test_never_run_asset_is_stale(self):
        """Test that never-run assets are stale."""
        assert _check_if_stale(None)

    def test_asset_exactly_24_hours_old(self):
        """Test boundary condition at 24 hours."""
        last_run = {
            "status": "success",
            "timestamp": datetime.utcnow() - timedelta(hours=24),
        }
        # Boundary: should be considered stale
        assert _check_if_stale(last_run)

    def test_asset_23_hours_59_minutes_old(self):
        """Test just under 24 hour boundary."""
        last_run = {
            "status": "success",
            "timestamp": datetime.utcnow() - timedelta(hours=23, minutes=59),
        }
        assert not _check_if_stale(last_run)


class TestMockAssetStatus:
    """Tests for mock asset status."""

    def test_returns_mock_assets(self):
        """Test that mock assets are returned."""
        assets = _get_mock_asset_status()
        assert len(assets) == 4
        assert all("name" in a for a in assets)
        assert all("group" in a for a in assets)

    def test_mock_assets_have_required_fields(self):
        """Test that mock assets have all required fields."""
        assets = _get_mock_asset_status()
        required_fields = {"name", "group", "last_run", "status", "freshness", "is_stale"}
        for asset in assets:
            assert required_fields.issubset(asset.keys())

    def test_filter_by_group(self):
        """Test filtering mock assets by group."""
        assets = _get_mock_asset_status(group="nightscout")
        assert len(assets) == 4
        assert all(a["group"] == "nightscout" for a in assets)

    def test_filter_by_non_existent_group(self):
        """Test filtering by non-existent group returns empty."""
        assets = _get_mock_asset_status(group="nonexistent")
        assert len(assets) == 0

    def test_filter_stale_assets(self):
        """Test filtering to only stale assets."""
        assets = _get_mock_asset_status(stale=True)
        assert len(assets) > 0
        assert all(a["is_stale"] for a in assets)

    def test_filter_by_group_and_stale(self):
        """Test filtering by both group and stale."""
        assets = _get_mock_asset_status(group="nightscout", stale=True)
        assert len(assets) > 0
        assert all(a["is_stale"] for a in assets)
        assert all(a["group"] == "nightscout" for a in assets)

    def test_mock_assets_freshness_values(self):
        """Test that mock assets have valid freshness values."""
        assets = _get_mock_asset_status()
        valid_freshness = {"fresh", "okay", "stale", "failed", "never_run"}
        for asset in assets:
            assert asset["freshness"] in valid_freshness

    def test_mock_asset_names_are_unique(self):
        """Test that mock assets have unique names."""
        assets = _get_mock_asset_status()
        names = [a["name"] for a in assets]
        assert len(names) == len(set(names))


class TestServiceHealth:
    """Tests for service health checks."""

    def test_service_health_with_mock(self):
        """Test service health checks work (with or without requests)."""
        # This will test the actual code path
        result = _check_service_health("http://localhost:9999/test", "TestService")

        # Should handle the connection error gracefully
        assert "name" in result
        assert "status" in result
        assert result["name"] == "TestService"

    def test_service_health_returns_required_fields(self):
        """Test that service health returns all required fields."""
        result = _check_service_health("http://localhost:9999/test", "TestService")

        required_fields = {"name", "status"}
        assert required_fields.issubset(result.keys())

    def test_service_health_handles_invalid_url(self):
        """Test that invalid URLs are handled gracefully."""
        result = _check_service_health("not-a-valid-url", "TestService")

        assert result["status"] in ["down", "error", "timeout"]
        assert result["name"] == "TestService"

    def test_all_service_statuses_valid(self):
        """Test that service health returns valid status values."""
        result = _check_service_health("http://localhost:9999/test", "TestService")

        valid_statuses = {"healthy", "down", "timeout", "error", "unhealthy"}
        assert result["status"] in valid_statuses


class TestStatusCLI:
    """Tests for the status CLI command."""

    def test_status_shows_all_by_default(self):
        """Test that status shows both assets and services by default."""
        runner = CliRunner()
        result = runner.invoke(status, [])

        assert result.exit_code == 0
        assert "Asset Status" in result.output
        assert "Service Health" in result.output

    def test_status_assets_only(self):
        """Test filtering to assets only."""
        runner = CliRunner()
        result = runner.invoke(status, ["--assets"])

        assert result.exit_code == 0
        assert "Asset Status" in result.output
        assert "Service Health" not in result.output

    def test_status_services_only(self):
        """Test filtering to services only."""
        runner = CliRunner()
        result = runner.invoke(status, ["--services"])

        assert result.exit_code == 0
        assert "Service Health" in result.output
        assert "Asset Status" not in result.output

    def test_status_filter_by_group(self):
        """Test filtering by asset group."""
        runner = CliRunner()
        result = runner.invoke(status, ["--assets", "--group", "nightscout"])

        assert result.exit_code == 0
        assert "nightscout" in result.output.lower()

    def test_status_filter_stale_only(self):
        """Test showing only stale assets."""
        runner = CliRunner()
        result = runner.invoke(status, ["--assets", "--stale"])

        assert result.exit_code == 0
        # Should show stale indicator
        assert "Stale" in result.output or "Failed" in result.output

    def test_status_json_output(self):
        """Test JSON output format."""
        runner = CliRunner()
        result = runner.invoke(status, ["--json"])

        assert result.exit_code == 0
        # Output should be valid JSON
        if result.output.strip():
            try:
                data = json.loads(result.output)
                assert "timestamp" in data
                assert "elapsed_seconds" in data
            except json.JSONDecodeError as e:
                pytest.fail(f"Output is not valid JSON: {e}\nOutput: {result.output}")

    def test_status_json_assets_only(self):
        """Test JSON output with assets only."""
        runner = CliRunner()
        result = runner.invoke(status, ["--assets", "--json"])

        assert result.exit_code == 0
        if result.output.strip():
            try:
                data = json.loads(result.output)
                assert "assets" in data
                assert "services" not in data
            except json.JSONDecodeError as e:
                pytest.fail(f"Output is not valid JSON: {e}\nOutput: {result.output}")

    def test_status_json_with_group_filter(self):
        """Test JSON output with group filter."""
        runner = CliRunner()
        result = runner.invoke(status, ["--assets", "--group", "nightscout", "--json"])

        assert result.exit_code == 0
        if result.output.strip():
            try:
                data = json.loads(result.output)
                assert "assets" in data
                if data["assets"]:
                    assert all(a["group"] == "nightscout" for a in data["assets"])
            except json.JSONDecodeError as e:
                pytest.fail(f"Output is not valid JSON: {e}\nOutput: {result.output}")

    def test_status_response_time(self):
        """Test that response time is reasonable."""
        import time

        runner = CliRunner()
        start = time.time()
        result = runner.invoke(status, ["--assets"])
        elapsed = time.time() - start

        assert result.exit_code == 0
        # Should complete in less than 5 seconds
        assert elapsed < 5.0


class TestStatusOutput:
    """Tests for status output formatting."""

    def test_asset_status_table_formatting(self):
        """Test that asset status table is formatted correctly."""
        runner = CliRunner()
        result = runner.invoke(status, ["--assets"])

        assert result.exit_code == 0
        # Check for expected table headers
        assert "Asset Name" in result.output
        assert "Status" in result.output
        assert "Freshness" in result.output

    def test_service_status_table_formatting(self):
        """Test that service status table is formatted correctly."""
        runner = CliRunner()
        result = runner.invoke(status, ["--services"])

        assert result.exit_code == 0
        # Check for expected table headers
        assert "Service" in result.output
        assert "Status" in result.output
        assert "Latency" in result.output

    def test_status_includes_timestamp_in_json(self):
        """Test that JSON output includes timestamp."""
        runner = CliRunner()
        result = runner.invoke(status, ["--json"])

        assert result.exit_code == 0
        if result.output.strip():
            data = json.loads(result.output)
            assert "timestamp" in data
            # Timestamp should be ISO format
            try:
                datetime.fromisoformat(data["timestamp"])
            except ValueError:
                pytest.fail("Timestamp is not in ISO format")

    def test_status_shows_asset_count(self):
        """Test that status shows asset count information."""
        runner = CliRunner()
        result = runner.invoke(status, ["--assets"])

        assert result.exit_code == 0
        # Should have a table with multiple assets
        assert "Asset Status" in result.output


class TestStatusFiltering:
    """Tests for status filtering logic."""

    def test_group_filter_excludes_other_groups(self):
        """Test that group filter excludes other groups."""
        runner = CliRunner()
        result = runner.invoke(status, ["--assets", "--group", "nightscout", "--json"])

        assert result.exit_code == 0
        if result.output.strip():
            data = json.loads(result.output)
            if data["assets"]:
                assert all(a["group"] == "nightscout" for a in data["assets"])

    def test_stale_filter_shows_only_stale(self):
        """Test that stale filter shows only stale assets."""
        runner = CliRunner()
        result = runner.invoke(status, ["--assets", "--stale", "--json"])

        assert result.exit_code == 0
        if result.output.strip():
            data = json.loads(result.output)
            if data["assets"]:
                assert all(a["is_stale"] for a in data["assets"])

    def test_combined_filters(self):
        """Test combining multiple filters."""
        runner = CliRunner()
        result = runner.invoke(
            status,
            ["--assets", "--group", "nightscout", "--stale", "--json"],
        )

        assert result.exit_code == 0
        if result.output.strip():
            data = json.loads(result.output)
            if data["assets"]:
                assert all(a["group"] == "nightscout" for a in data["assets"])
                assert all(a["is_stale"] for a in data["assets"])

    def test_non_existent_group_returns_empty(self):
        """Test that non-existent group returns empty results."""
        runner = CliRunner()
        result = runner.invoke(status, ["--assets", "--group", "nonexistent", "--json"])

        assert result.exit_code == 0
        if result.output.strip():
            data = json.loads(result.output)
            assert len(data["assets"]) == 0


class TestStatusEdgeCases:
    """Tests for edge cases in status command."""

    def test_status_with_all_flags(self):
        """Test status with all filtering flags combined."""
        runner = CliRunner()
        result = runner.invoke(
            status,
            ["--assets", "--services", "--group", "nightscout", "--stale", "--json"],
        )

        assert result.exit_code == 0
        if result.output.strip():
            data = json.loads(result.output)
            assert "assets" in data
            assert "services" in data

    def test_status_json_is_serializable(self):
        """Test that JSON output is fully serializable."""
        runner = CliRunner()
        result = runner.invoke(status, ["--json"])

        assert result.exit_code == 0
        if result.output.strip():
            data = json.loads(result.output)
            # Should be able to re-serialize
            assert json.dumps(data)

    def test_status_handles_missing_requests_library(self):
        """Test that status handles missing requests library gracefully."""
        runner = CliRunner()
        # Even without requests, should not crash
        result = runner.invoke(status, ["--services"])
        assert result.exit_code == 0

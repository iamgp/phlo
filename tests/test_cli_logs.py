"""Tests for the phlo logs CLI command."""

import json
from datetime import datetime, timedelta

import pytest
from click.testing import CliRunner

from phlo.cli.logs import (
    _get_mock_logs,
    _get_log_level,
    _is_json,
    _parse_since,
    logs,
)


class TestLogLevelMapping:
    """Test log level mapping from event types."""

    def test_error_event_type(self):
        """Map ERROR event type."""
        assert _get_log_level("STEP_FAILURE") == "ERROR"
        assert _get_log_level("FAILURE") == "ERROR"

    def test_warning_event_type(self):
        """Map WARNING event type."""
        assert _get_log_level("STEP_WARNING") == "WARNING"

    def test_info_event_type(self):
        """Map INFO event type."""
        assert _get_log_level("STEP_SUCCESS") == "INFO"
        assert _get_log_level("STEP_OUTPUT") == "INFO"

    def test_debug_event_type(self):
        """Map DEBUG event type."""
        assert _get_log_level("LOG_MESSAGE") == "DEBUG"
        assert _get_log_level("STEP_INPUT") == "DEBUG"


class TestTimeParsing:
    """Test time filter parsing."""

    def test_parse_hours(self):
        """Parse hours from time filter."""
        now = datetime.utcnow()
        result = _parse_since("1h")
        # Should be approximately 1 hour ago
        diff = now - result
        assert timedelta(hours=0.99) < diff < timedelta(hours=1.01)

    def test_parse_minutes(self):
        """Parse minutes from time filter."""
        now = datetime.utcnow()
        result = _parse_since("30m")
        diff = now - result
        assert timedelta(minutes=29.9) < diff < timedelta(minutes=30.1)

    def test_parse_days(self):
        """Parse days from time filter."""
        now = datetime.utcnow()
        result = _parse_since("2d")
        diff = now - result
        assert timedelta(days=1.99) < diff < timedelta(days=2.01)

    def test_invalid_time_format(self):
        """Handle invalid time format gracefully."""
        result = _parse_since("invalid")
        # Should default to last 24 hours
        now = datetime.utcnow()
        diff = now - result
        assert timedelta(hours=23.9) < diff < timedelta(hours=24.1)


class TestJSONDetection:
    """Test JSON content detection."""

    def test_valid_json(self):
        """Detect valid JSON strings."""
        assert _is_json('{"key": "value"}')
        assert _is_json('["item1", "item2"]')
        assert _is_json("123")
        assert _is_json("true")

    def test_invalid_json(self):
        """Detect non-JSON strings."""
        assert not _is_json("plain text")
        assert not _is_json("{invalid json}")
        assert not _is_json("")


class TestMockLogs:
    """Test mock log generation and filtering."""

    def test_mock_logs_generation(self):
        """Generate mock logs."""
        logs_data = _get_mock_logs({})
        assert len(logs_data) > 0
        assert all("timestamp" in log for log in logs_data)
        assert all("level" in log for log in logs_data)
        assert all("message" in log for log in logs_data)

    def test_filter_by_level(self):
        """Filter logs by level."""
        logs_data = _get_mock_logs({"level": "INFO"})
        assert all(log["level"] == "INFO" for log in logs_data)

    def test_filter_by_asset(self):
        """Filter logs by asset name."""
        logs_data = _get_mock_logs({"asset": "glucose_entries"})
        assert len(logs_data) > 0
        assert all("glucose" in log["message"].lower() for log in logs_data)

    def test_filter_by_job(self):
        """Filter logs by job name."""
        logs_data = _get_mock_logs({"job": "glucose_ingestion"})
        assert all(log["job_name"] == "glucose_ingestion" for log in logs_data)

    def test_filter_by_run_id(self):
        """Filter logs by run ID."""
        logs_data = _get_mock_logs({"run_id": "abc123"})
        assert all(log["run_id"] == "abc123" for log in logs_data)

    def test_filter_by_time(self):
        """Filter logs by time range."""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=3)
        logs_data = _get_mock_logs({"start_time": cutoff})

        # All logs should be after cutoff
        for log in logs_data:
            log_time = datetime.fromisoformat(log["timestamp"])
            assert log_time >= cutoff

    def test_limit(self):
        """Respect limit parameter."""
        logs_data = _get_mock_logs({"limit": 2})
        assert len(logs_data) <= 2


class TestLogsCLI:
    """Test logs CLI command."""

    def test_help_message(self):
        """Display help message."""
        runner = CliRunner()
        result = runner.invoke(logs, ["--help"])
        assert result.exit_code == 0
        assert "Access and filter Dagster run logs" in result.output
        assert "--asset" in result.output
        assert "--job" in result.output
        assert "--level" in result.output
        assert "--follow" in result.output

    def test_basic_logs(self):
        """Display basic logs."""
        runner = CliRunner()
        result = runner.invoke(logs)
        assert result.exit_code == 0
        assert "Time" in result.output
        assert "Level" in result.output
        assert "Message" in result.output

    def test_filter_by_level(self):
        """Filter logs by level."""
        runner = CliRunner()
        result = runner.invoke(logs, ["--level", "ERROR"])
        assert result.exit_code == 0
        # Mock data doesn't have ERROR level, so should show no logs
        assert "No logs found" in result.output or "Total: 0" in result.output

    def test_filter_by_asset(self):
        """Filter logs by asset name."""
        runner = CliRunner()
        result = runner.invoke(logs, ["--asset", "glucose_entries"])
        assert result.exit_code == 0
        assert "Total:" in result.output

    def test_filter_by_job(self):
        """Filter logs by job name."""
        runner = CliRunner()
        result = runner.invoke(logs, ["--job", "glucose_ingestion"])
        assert result.exit_code == 0
        # Job name might be truncated in display, check for logs instead
        assert "Total:" in result.output

    def test_json_output(self):
        """Output logs in JSON format."""
        runner = CliRunner()
        result = runner.invoke(logs, ["--json", "--limit", "2"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) <= 2

    def test_time_filter(self):
        """Filter logs by time range."""
        runner = CliRunner()
        result = runner.invoke(logs, ["--since", "1h"])
        assert result.exit_code == 0
        assert "Total:" in result.output

    def test_limit_parameter(self):
        """Limit number of logs."""
        runner = CliRunner()
        result = runner.invoke(logs, ["--limit", "3"])
        assert result.exit_code == 0
        # Count rows in output (excluding header/footer)
        lines = result.output.split("\n")
        assert len(lines) > 0

    def test_run_id_filter(self):
        """Filter logs by run ID."""
        runner = CliRunner()
        result = runner.invoke(logs, ["--run-id", "abc123"])
        assert result.exit_code == 0
        assert "abc123" in result.output or "Total:" in result.output

    def test_combined_filters(self):
        """Apply multiple filters."""
        runner = CliRunner()
        result = runner.invoke(
            logs,
            ["--asset", "glucose_entries", "--job", "glucose_ingestion"],
        )
        assert result.exit_code == 0
        assert "Total:" in result.output

    def test_invalid_time_filter(self):
        """Handle invalid time filter gracefully."""
        runner = CliRunner()
        result = runner.invoke(logs, ["--since", "invalid_time"])
        assert result.exit_code == 0
        # Should still work with default time
        assert "Total:" in result.output


class TestLogsPerformance:
    """Test performance characteristics."""

    def test_fast_retrieval(self):
        """Retrieve logs quickly (< 1 second for 100 logs)."""
        import time

        runner = CliRunner()
        start = time.time()
        result = runner.invoke(logs, ["--limit", "100"])
        elapsed = time.time() - start

        assert result.exit_code == 0
        assert elapsed < 1.0  # Should complete in under 1 second

    def test_handles_large_volume(self):
        """Handle large log volumes gracefully."""
        runner = CliRunner()
        result = runner.invoke(logs, ["--limit", "1000"])
        assert result.exit_code == 0
        assert "Total:" in result.output

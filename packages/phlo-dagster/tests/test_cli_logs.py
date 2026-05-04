"""Tests for the phlo logs CLI command."""

from datetime import datetime, timedelta, timezone

from click.testing import CliRunner

from phlo_dagster.cli_logs import (
    _event_log_row_to_entry,
    _get_log_level,
    _parse_since,
    logs,
)
from phlo_dagster.cli_logs_display import _is_json


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


def test_event_log_row_to_entry_parses_dagster_event_payload() -> None:
    row = {
        "run_id": "run-123",
        "dagster_event_type": "ASSET_MATERIALIZATION",
        "timestamp": datetime(2026, 2, 1, 10, 0, tzinfo=timezone.utc),
        "event": (
            '{"level": 20, "user_message": "Materialized value dlt_orders.", '
            '"dagster_event": {"logging_tags": {"job_name": "__ASSET_JOB"}}}'
        ),
    }

    entry = _event_log_row_to_entry(row)

    assert entry == {
        "timestamp": "2026-02-01T10:00:00+00:00",
        "level": "INFO",
        "message": "Materialized value dlt_orders.",
        "event_type": "ASSET_MATERIALIZATION",
        "run_id": "run-123",
        "job_name": "__ASSET_JOB",
        "run_status": "",
    }


class TestTimeParsing:
    """Test time filter parsing."""

    def test_parse_hours(self):
        """Parse hours from time filter."""
        now = datetime.now(timezone.utc)
        result = _parse_since("1h")
        # Should be approximately 1 hour ago
        diff = now - result
        assert timedelta(hours=0.99) < diff < timedelta(hours=1.01)

    def test_parse_minutes(self):
        """Parse minutes from time filter."""
        now = datetime.now(timezone.utc)
        result = _parse_since("30m")
        diff = now - result
        assert timedelta(minutes=29.9) < diff < timedelta(minutes=30.1)

    def test_parse_days(self):
        """Parse days from time filter."""
        now = datetime.now(timezone.utc)
        result = _parse_since("2d")
        diff = now - result
        assert timedelta(days=1.99) < diff < timedelta(days=2.01)

    def test_invalid_time_format(self):
        """Handle invalid time format gracefully."""
        result = _parse_since("invalid")
        # Should default to last 24 hours
        now = datetime.now(timezone.utc)
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
        """Display basic logs (no services connected = no logs)."""
        runner = CliRunner()
        result = runner.invoke(logs)
        assert result.exit_code == 0

    def test_filter_by_level(self):
        """Filter logs by level."""
        runner = CliRunner()
        result = runner.invoke(logs, ["--level", "ERROR"])
        assert result.exit_code == 0

    def test_json_output(self):
        """Output logs in JSON format (empty when services disconnected)."""
        runner = CliRunner()
        result = runner.invoke(logs, ["--json", "--limit", "2"])
        assert result.exit_code == 0
        assert result.output.strip() == "[]"

    def test_limit_parameter(self):
        """Limit number of logs."""
        runner = CliRunner()
        result = runner.invoke(logs, ["--limit", "3"])
        assert result.exit_code == 0

    def test_invalid_time_filter(self):
        """Handle invalid time filter gracefully."""
        runner = CliRunner()
        result = runner.invoke(logs, ["--since", "invalid_time"])
        assert result.exit_code == 0


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

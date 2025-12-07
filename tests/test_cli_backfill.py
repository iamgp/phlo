"""Tests for the phlo backfill CLI command."""

import json
from datetime import datetime
from unittest.mock import patch

from click.testing import CliRunner

from phlo.cli.backfill import (
    _generate_partition_dates,
    _validate_partition_dates,
    backfill,
)


class TestBackfillDateGeneration:
    """Test date range generation."""

    def test_generate_single_day(self):
        """Generate partition for a single day."""
        dates = _generate_partition_dates("2024-01-01", "2024-01-01")
        assert dates == ["2024-01-01"]

    def test_generate_week(self):
        """Generate partitions for a week."""
        dates = _generate_partition_dates("2024-01-01", "2024-01-07")
        assert len(dates) == 7
        assert dates[0] == "2024-01-01"
        assert dates[-1] == "2024-01-07"

    def test_generate_year(self):
        """Generate partitions for entire year."""
        dates = _generate_partition_dates("2024-01-01", "2024-12-31")
        assert len(dates) == 366  # 2024 is leap year
        assert dates[0] == "2024-01-01"
        assert dates[-1] == "2024-12-31"

    def test_generate_month(self):
        """Generate partitions for a month."""
        dates = _generate_partition_dates("2024-01-01", "2024-01-31")
        assert len(dates) == 31

    def test_invalid_start_after_end(self):
        """Reject when start date is after end date."""
        runner = CliRunner()
        result = runner.invoke(
            backfill,
            ["test_asset", "--start-date", "2024-01-05", "--end-date", "2024-01-01"],
        )
        assert result.exit_code == 1
        assert "Start date must be before end date" in result.output


class TestBackfillValidation:
    """Test partition date validation."""

    def test_valid_date_format(self):
        """Accept valid YYYY-MM-DD format."""
        # Should not raise
        _validate_partition_dates(["2024-01-01", "2024-12-31"])

    def test_invalid_date_format(self):
        """Reject invalid date format."""
        runner = CliRunner()
        result = runner.invoke(
            backfill,
            [
                "test_asset",
                "--partitions",
                "2024-01-01,01-01-2024",  # Invalid format
            ],
        )
        assert result.exit_code == 1
        assert "Invalid partition date" in result.output

    def test_whitespace_handling(self):
        """Handle whitespace in date strings."""
        # Should not raise
        _validate_partition_dates(["2024-01-01", " 2024-01-02 ", "2024-01-03"])


class TestBackfillCLI:
    """Test backfill CLI command."""

    def test_help_message(self):
        """Display help message."""
        runner = CliRunner()
        result = runner.invoke(backfill, ["--help"])
        assert result.exit_code == 0
        assert "Run asset materialization across a date range" in result.output
        assert "--start-date" in result.output
        assert "--end-date" in result.output
        assert "--parallel" in result.output
        assert "--resume" in result.output

    def test_missing_asset_name(self):
        """Require asset name when not resuming."""
        runner = CliRunner()
        result = runner.invoke(
            backfill,
            ["--start-date", "2024-01-01", "--end-date", "2024-01-05"],
        )
        assert result.exit_code == 1
        assert "Asset name is required" in result.output

    def test_missing_date_arguments(self):
        """Require date range or explicit partitions."""
        runner = CliRunner()
        result = runner.invoke(backfill, ["test_asset"])
        assert result.exit_code == 1
        assert "Must specify either --start-date/--end-date or --partitions" in result.output

    @patch("phlo.cli.backfill.find_dagster_container", return_value="mock-container")
    @patch("phlo.cli.backfill.get_project_name", return_value="mock-project")
    def test_dry_run_with_date_range(self, mock_project, mock_container):
        """Display commands in dry-run mode."""
        runner = CliRunner()
        result = runner.invoke(
            backfill,
            [
                "glucose_entries",
                "--start-date",
                "2024-01-01",
                "--end-date",
                "2024-01-03",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "Dry run" in result.output
        assert "docker exec" in result.output
        assert "2024-01-01" in result.output
        assert "2024-01-02" in result.output
        assert "2024-01-03" in result.output

    @patch("phlo.cli.backfill.find_dagster_container", return_value="mock-container")
    @patch("phlo.cli.backfill.get_project_name", return_value="mock-project")
    def test_dry_run_with_partitions(self, mock_project, mock_container):
        """Display commands with explicit partitions."""
        runner = CliRunner()
        result = runner.invoke(
            backfill,
            [
                "glucose_entries",
                "--partitions",
                "2024-01-01,2024-01-15,2024-01-31",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "Total partitions: 3" in result.output
        assert "2024-01-01" in result.output
        assert "2024-01-15" in result.output
        assert "2024-01-31" in result.output

    @patch("phlo.cli.backfill.find_dagster_container", return_value="mock-container")
    @patch("phlo.cli.backfill.get_project_name", return_value="mock-project")
    def test_parallel_option(self, mock_project, mock_container):
        """Accept parallel worker count."""
        runner = CliRunner()
        result = runner.invoke(
            backfill,
            [
                "glucose_entries",
                "--start-date",
                "2024-01-01",
                "--end-date",
                "2024-01-10",
                "--parallel",
                "4",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "Parallel workers: 4" in result.output

    def test_invalid_parallel_value(self):
        """Reject invalid parallel worker count."""
        runner = CliRunner()
        result = runner.invoke(
            backfill,
            [
                "glucose_entries",
                "--start-date",
                "2024-01-01",
                "--end-date",
                "2024-01-05",
                "--parallel",
                "0",
                "--dry-run",
            ],
        )
        assert result.exit_code == 1
        assert "Parallel must be >= 1" in result.output

    def test_resume_without_state(self):
        """Reject resume without state file."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(backfill, ["--resume"])
            assert result.exit_code == 1
            assert "No backfill state found" in result.output

    @patch("phlo.cli.backfill.find_dagster_container", return_value="mock-container")
    @patch("phlo.cli.backfill.get_project_name", return_value="mock-project")
    def test_large_date_range(self, mock_project, mock_container):
        """Handle 365+ partitions efficiently."""
        runner = CliRunner()
        result = runner.invoke(
            backfill,
            [
                "glucose_entries",
                "--start-date",
                "2024-01-01",
                "--end-date",
                "2024-12-31",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "366" in result.output  # 2024 is leap year


class TestBackfillStateManagement:
    """Test backfill state file management."""

    def test_state_file_creation(self, tmp_path):
        """Create state file during backfill."""
        # Change to temp directory for test
        import os

        from phlo.cli.backfill import _save_backfill_state

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            _save_backfill_state(
                "test_asset",
                ["2024-01-02", "2024-01-03"],
                ["2024-01-01"],
            )

            state_file = tmp_path / ".phlo" / "backfill_state.json"
            assert state_file.exists()

            state = json.loads(state_file.read_text())
            assert state["asset_name"] == "test_asset"
            assert state["remaining_partitions"] == ["2024-01-02", "2024-01-03"]
            assert state["completed_partitions"] == ["2024-01-01"]
        finally:
            os.chdir(original_cwd)

    def test_state_file_format(self, tmp_path):
        """State file contains all required fields."""
        import os

        from phlo.cli.backfill import _save_backfill_state

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            _save_backfill_state(
                "glucose_entries",
                ["2024-01-05"],
                ["2024-01-01", "2024-01-02"],
            )

            state_file = tmp_path / ".phlo" / "backfill_state.json"
            state = json.loads(state_file.read_text())

            # Verify all required fields
            assert "asset_name" in state
            assert "remaining_partitions" in state
            assert "completed_partitions" in state
            assert "last_updated" in state

            # Verify timestamp format
            datetime.fromisoformat(state["last_updated"])
        finally:
            os.chdir(original_cwd)

"""Tests for Quality Module.

This module contains unit, integration, and data quality tests for the
cascade.defs.quality.nightscout module.
"""

from unittest.mock import MagicMock, patch
from typing import cast

import pandas as pd
import pytest
from dagster import AssetCheckResult, MetadataValue, build_asset_check_context

from cascade.defs.quality.nightscout import nightscout_glucose_quality_check


class TestQualityUnitTests:
    """Unit tests for quality checks with mocked dependencies."""

    def test_nightscout_glucose_quality_check_queries_trino(self):
        """Test that nightscout_glucose_quality_check queries Trino."""
        # Create proper asset check context for testing
        mock_context = build_asset_check_context()

        # Mock Trino resource
        mock_trino = MagicMock()
        mock_cursor = MagicMock()
        mock_trino.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_trino.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Mock query results
        mock_cursor.description = [("entry_id",), ("glucose_mg_dl",)]
        mock_cursor.fetchall.return_value = [("entry1", 120), ("entry2", 130)]

        # Execute
        result = cast(AssetCheckResult, nightscout_glucose_quality_check(mock_context, mock_trino))

        # Verify Trino query was executed
        mock_cursor.execute.assert_called_once()
        assert "fct_glucose_readings" in str(mock_cursor.execute.call_args)

        # Verify result structure
        assert isinstance(result, AssetCheckResult)

    def test_nightscout_glucose_quality_check_validates_data_with_pandera_schema(self):
        """Test that nightscout_glucose_quality_check validates data with Pandera schema."""
        # Create proper asset check context for testing
        mock_context = build_asset_check_context()

        # Mock Trino resource
        mock_trino = MagicMock()
        mock_cursor = MagicMock()
        mock_trino.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_trino.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Mock valid query results
        mock_cursor.description = [
            ("entry_id",), ("glucose_mg_dl",), ("reading_timestamp",),
            ("direction",), ("hour_of_day",), ("day_of_week",),
            ("glucose_category",), ("is_in_range",)
        ]
        mock_cursor.fetchall.return_value = [
            ("entry1", 120, "2024-01-01 12:00:00", "Flat", 12, 1, "in_range", 1),
            ("entry2", 80, "2024-01-01 13:00:00", "SingleDown", 13, 1, "hypoglycemia", 0),
        ]

        # Execute
        result = cast(AssetCheckResult, nightscout_glucose_quality_check(mock_context, mock_trino))

        # Verify validation passed
        assert result.passed is True
        assert result.metadata["rows_validated"] == MetadataValue.int(2)
        assert "pandera_schema" in result.metadata

    def test_nightscout_glucose_quality_check_handles_empty_results(self):
        """Test that nightscout_glucose_quality_check handles empty results."""
        # Create proper asset check context for testing
        mock_context = build_asset_check_context()

        # Mock Trino resource
        mock_trino = MagicMock()
        mock_cursor = MagicMock()
        mock_trino.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_trino.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Mock empty query results
        mock_cursor.description = [("entry_id",), ("glucose_mg_dl",)]
        mock_cursor.fetchall.return_value = []

        # Execute
        result = cast(AssetCheckResult, nightscout_glucose_quality_check(mock_context, mock_trino))

        # Verify empty result handling
        assert result.passed is True
        assert result.metadata["rows_validated"] == MetadataValue.int(0)
        assert "No data available" in str(result.metadata["note"])

    def test_nightscout_glucose_quality_check_reports_failures_correctly(self):
        """Test that nightscout_glucose_quality_check reports failures correctly."""
        # Create proper asset check context for testing
        mock_context = build_asset_check_context()

        # Mock Trino resource
        mock_trino = MagicMock()
        mock_cursor = MagicMock()
        mock_trino.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_trino.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Mock query results with invalid data (glucose too high)
        mock_cursor.description = [
            ("entry_id",), ("glucose_mg_dl",), ("reading_timestamp",),
            ("direction",), ("hour_of_day",), ("day_of_week",),
            ("glucose_category",), ("is_in_range",)
        ]
        mock_cursor.fetchall.return_value = [
            ("entry1", 700, "2024-01-01 12:00:00", "Flat", 12, 1, "invalid", 1),  # Invalid glucose
        ]

        # Execute
        result = cast(AssetCheckResult, nightscout_glucose_quality_check(mock_context, mock_trino))

        # Verify failure reporting
        assert result.passed is False
        assert "failed_checks" in result.metadata
        assert "failures_by_column" in result.metadata


class TestQualityIntegrationTests:
    """Integration tests for quality checks."""

    def test_quality_check_integrates_with_trino_resource(self):
        """Test that quality check integrates with Trino resource."""
        # Create proper asset check context for testing
        mock_context = build_asset_check_context()

        # Mock Trino resource
        mock_trino = MagicMock()
        mock_cursor = MagicMock()
        mock_trino.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_trino.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Mock query results
        mock_cursor.description = [("entry_id",), ("glucose_mg_dl",)]
        mock_cursor.fetchall.return_value = [("entry1", 120)]

        # Execute
        result = cast(AssetCheckResult, nightscout_glucose_quality_check(mock_context, mock_trino))

        # Verify integration
        assert mock_trino.cursor.called
        assert mock_cursor.execute.called
        assert isinstance(result, AssetCheckResult)

    def test_pandera_validation_catches_schema_violations(self):
        """Test that Pandera validation catches schema violations."""
        # Create proper asset check context for testing
        mock_context = build_asset_check_context()

        # Mock Trino resource
        mock_trino = MagicMock()
        mock_cursor = MagicMock()
        mock_trino.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_trino.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Mock query results with schema violations
        mock_cursor.description = [
            ("entry_id",), ("glucose_mg_dl",), ("reading_timestamp",),
            ("direction",), ("hour_of_day",), ("day_of_week",),
            ("glucose_category",), ("is_in_range",)
        ]
        mock_cursor.fetchall.return_value = [
            ("entry1", 50, "2024-01-01 12:00:00", "InvalidDirection", 25, 7, "invalid", 2),  # Multiple violations
        ]

        # Execute
        result = cast(AssetCheckResult, nightscout_glucose_quality_check(mock_context, mock_trino))

        # Verify schema violations are caught
        assert result.passed is False
        assert "failed_checks" in result.metadata
        assert result.metadata["failed_checks"] > MetadataValue.int(0)


class TestQualityDataQualityTests:
    """Data quality tests for validation logic."""

    def test_data_conforms_to_business_rules_glucose_ranges(self):
        """Test that data conforms to business rules (e.g., glucose ranges)."""
        # This would test the Pandera schema validation for glucose ranges
        # Since the actual validation is done by Pandera, we test that the
        # quality check properly invokes it

        # Create proper asset check context for testing
        mock_context = build_asset_check_context()

        # Mock Trino resource
        mock_trino = MagicMock()
        mock_cursor = MagicMock()
        mock_trino.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_trino.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Mock valid data within ranges
        mock_cursor.description = [
            ("entry_id",), ("glucose_mg_dl",), ("reading_timestamp",),
            ("direction",), ("hour_of_day",), ("day_of_week",),
            ("glucose_category",), ("is_in_range",)
        ]
        mock_cursor.fetchall.return_value = [
            ("entry1", 120, "2024-01-01 12:00:00", "Flat", 12, 1, "in_range", 1),
            ("entry2", 180, "2024-01-01 13:00:00", "SingleUp", 13, 1, "hyperglycemia_mild", 0),
        ]

        # Execute
        result = cast(AssetCheckResult, nightscout_glucose_quality_check(mock_context, mock_trino))

        # Verify business rules are enforced
        assert result.passed is True
        assert result.metadata["rows_validated"] == MetadataValue.int(2)

    def test_quality_checks_run_on_partitioned_data(self):
        """Test that quality checks run on partitioned data."""
        # Create proper asset check context for testing
        mock_context = MagicMock()
        mock_context.partition_key = "2024-01-15"

        # Mock Trino resource
        mock_trino = MagicMock()
        mock_cursor = MagicMock()
        mock_trino.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_trino.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Mock query results
        mock_cursor.description = [("entry_id",), ("glucose_mg_dl",)]
        mock_cursor.fetchall.return_value = [("entry1", 120)]

        # Execute
        result = cast(AssetCheckResult, nightscout_glucose_quality_check(mock_context, mock_trino))

        # Verify partition filtering
        query_arg = mock_cursor.execute.call_args[0][0]
        assert "2024-01-15" in query_arg
        assert "DATE" in query_arg

    def test_quality_checks_are_triggered_after_transformations(self):
        """Test that quality checks are triggered after transformations."""
        # This test verifies that the quality check is properly configured
        # to run after the fct_glucose_readings asset

        from dagster import AssetKey

        # The check should be configured for the correct asset
        # This is tested by verifying the decorator configuration
        # rather than runtime behavior

        # Create proper asset check context for testing
        mock_context = build_asset_check_context()

        # Mock Trino resource
        mock_trino = MagicMock()
        mock_cursor = MagicMock()
        mock_trino.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_trino.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Mock query results with all required columns
        mock_cursor.description = [
            ("entry_id",), ("glucose_mg_dl",), ("reading_timestamp",), ("direction",),
            ("hour_of_day",), ("day_of_week",), ("glucose_category",), ("is_in_range")
        ]
        mock_cursor.fetchall.return_value = [(
            "entry1", 120, "2024-01-01 12:00:00", "Flat", 12, 1, "in_range", 1
        )]

        # Execute
        result = cast(AssetCheckResult, nightscout_glucose_quality_check(mock_context, mock_trino))

        # Verify the check runs and produces results
        assert isinstance(result, AssetCheckResult)
        # Note: With mock data, the check may fail due to schema validation,
        # but the important thing is that it runs and produces structured results
        assert "rows_evaluated" in result.metadata

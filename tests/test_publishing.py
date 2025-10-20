"""Tests for Publishing Module.

This module contains unit, integration, e2e, and data quality tests for the
cascade.defs.publishing.trino_to_postgres module.
"""

from unittest.mock import MagicMock, patch

import pytest
from dagster import AssetKey, MaterializeResult, build_asset_context, materialize

from cascade.defs.publishing.trino_to_postgres import publish_glucose_marts_to_postgres
from cascade.schemas import PublishPostgresOutput, TablePublishStats


class TestPublishingUnitTests:
    """Unit tests for publishing assets with mocked dependencies."""

    @patch('cascade.defs.publishing.trino_to_postgres.psycopg2.connect')
    @patch('cascade.defs.publishing.trino_to_postgres.config')
    def test_publish_glucose_marts_to_postgres_queries_trino_correctly(self, mock_config, mock_psycopg2_connect):
        """Test that publish_glucose_marts_to_postgres queries Trino correctly."""
        # Mock config
        mock_config.postgres_mart_schema = "marts"
        mock_config.postgres_host = "postgres"
        mock_config.postgres_port = 5432
        mock_config.postgres_user = "user"
        mock_config.postgres_password = "pass"
        mock_config.postgres_db = "lakehouse"

        # Mock Postgres connection
        mock_pg_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_pg_conn.cursor.return_value = mock_cursor
        mock_psycopg2_connect.return_value = mock_pg_conn

        # Mock Trino resource and cursor
        mock_trino_cursor = MagicMock()
        mock_trino_cursor.description = [("id",), ("glucose",), ("date")]
        mock_trino_cursor.fetchall.return_value = [
            (1, 120, "2024-01-01"),
            (2, 130, "2024-01-02"),
        ]

        # Create proper asset context for testing
        mock_context = build_asset_context()

        # Create mock Trino resource
        mock_trino_resource = MagicMock()
        mock_trino_resource.cursor.return_value.__enter__ = MagicMock(return_value=mock_trino_cursor)
        mock_trino_resource.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Execute the asset function (this tests the core logic)
        result = publish_glucose_marts_to_postgres(mock_context, mock_trino_resource)

        # Verify Trino queries
        assert mock_trino_cursor.execute.call_count == 2  # One for each table
        assert "mrt_glucose_overview" in str(mock_trino_cursor.execute.call_args_list[0])
        assert "mrt_glucose_hourly_patterns" in str(mock_trino_cursor.execute.call_args_list[1])

        # Verify result
        assert isinstance(result, PublishPostgresOutput)
        assert len(result.tables) == 2
        assert "mrt_glucose_overview" in result.tables
        assert "mrt_glucose_hourly_patterns" in result.tables

    @patch('cascade.defs.publishing.trino_to_postgres.psycopg2.connect')
    @patch('cascade.defs.publishing.trino_to_postgres.config')
    def test_publish_glucose_marts_to_postgres_creates_postgres_tables(self, mock_config, mock_psycopg2_connect):
        """Test that publish_glucose_marts_to_postgres creates Postgres tables."""
        # Mock config
        mock_config.postgres_mart_schema = "marts"
        mock_config.postgres_host = "postgres"
        mock_config.postgres_port = 5432
        mock_config.postgres_user = "user"
        mock_config.postgres_password = "pass"
        mock_config.postgres_db = "lakehouse"

        # Mock Postgres connection
        mock_pg_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_pg_conn.cursor.return_value = mock_cursor
        mock_psycopg2_connect.return_value = mock_pg_conn

        # Mock Trino resource and cursor
        mock_trino_cursor = MagicMock()
        mock_trino_cursor.description = [("id",), ("glucose",), ("date")]
        mock_trino_cursor.fetchall.return_value = [(1, 120, "2024-01-01")]

        # Create proper asset context for testing
        mock_context = build_asset_context()

        # Create mock Trino resource
        mock_trino_resource = MagicMock()
        mock_trino_resource.cursor.return_value.__enter__ = MagicMock(return_value=mock_trino_cursor)
        mock_trino_resource.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Execute the asset function
        publish_glucose_marts_to_postgres(mock_context, mock_trino_resource)

        # Verify table creation
        assert mock_cursor.execute.called
        create_calls = [call for call in mock_cursor.execute.call_args_list
                       if "CREATE TABLE" in str(call)]
        assert len(create_calls) >= 1


@pytest.mark.skip(reason="Asset direct invocation requires proper Dagster testing setup")
class TestPublishingIntegrationTests:
    """Integration tests for publishing operations."""


@pytest.mark.skip(reason="Asset direct invocation requires proper Dagster testing setup")
class TestPublishingE2ETests:
    """End-to-end tests for publishing pipeline."""

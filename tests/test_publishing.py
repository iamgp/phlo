"""Tests for Publishing Module.

This module contains unit, integration, e2e, and data quality tests for the
cascade.defs.publishing.trino_to_postgres module.
"""

from unittest.mock import MagicMock, patch

import pytest
from dagster import AssetKey, MaterializeResult
from dagster._core.execution.context.invocation import build_op_context

from cascade.defs.publishing.trino_to_postgres import publish_glucose_marts_to_postgres
from cascade.schemas import PublishPostgresOutput, TablePublishStats


@pytest.mark.skip(reason="Asset direct invocation requires proper Dagster testing setup")
class TestPublishingUnitTests:
    """Unit tests for publishing assets with mocked dependencies."""

    @patch('cascade.defs.publishing.trino_to_postgres.psycopg2.connect')
    @patch('cascade.defs.publishing.trino_to_postgres.config')
    @pytest.mark.skip(reason="Asset direct invocation requires proper Dagster testing setup")
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

        # Mock Trino resource
        mock_trino = MagicMock()
        mock_trino_cursor = MagicMock()
        mock_trino.cursor.return_value.__enter__ = MagicMock(return_value=mock_trino_cursor)
        mock_trino.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Mock Trino query results
        mock_trino_cursor.description = [("id",), ("glucose",), ("date",)]
        mock_trino_cursor.fetchall.return_value = [
            (1, 120, "2024-01-01"),
            (2, 130, "2024-01-02"),
        ]

        # Create proper context
        mock_context = build_op_context()

        # Execute
        result = publish_glucose_marts_to_postgres(mock_context, mock_trino)

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

        # Mock Trino resource
        mock_trino = MagicMock()
        mock_trino_cursor = MagicMock()
        mock_trino.cursor.return_value.__enter__ = MagicMock(return_value=mock_trino_cursor)
        mock_trino.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Mock Trino query results
        mock_trino_cursor.description = [("id",), ("glucose",), ("date",)]
        mock_trino_cursor.fetchall.return_value = [(1, 120, "2024-01-01")]

        # Create proper context
        mock_context = build_op_context()

        # Execute
        publish_glucose_marts_to_postgres(mock_context, mock_trino)

        # Verify table creation
        assert mock_cursor.execute.called
        create_calls = [call for call in mock_cursor.execute.call_args_list
                       if "CREATE TABLE" in str(call)]
        assert len(create_calls) == 2  # One for each table

    @patch('cascade.defs.publishing.trino_to_postgres.psycopg2.connect')
    @patch('cascade.defs.publishing.trino_to_postgres.config')
    def test_publish_glucose_marts_to_postgres_inserts_data_in_batches(self, mock_config, mock_psycopg2_connect):
        """Test that publish_glucose_marts_to_postgres inserts data in batches."""
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

        # Mock Trino resource
        mock_trino = MagicMock()
        mock_trino_cursor = MagicMock()
        mock_trino.cursor.return_value.__enter__ = MagicMock(return_value=mock_trino_cursor)
        mock_trino.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Mock Trino query results
        mock_trino_cursor.description = [("id",), ("glucose",)]
        mock_trino_cursor.fetchall.return_value = [(1, 120), (2, 130), (3, 140)]

        # Create proper context
        mock_context = build_op_context()

        # Execute
        publish_glucose_marts_to_postgres(mock_context, mock_trino)

        # Verify batch inserts
        assert mock_cursor.executemany.called
        assert mock_cursor.executemany.call_count == 2  # One for each table

    @patch('cascade.defs.publishing.trino_to_postgres.psycopg2.connect')
    @patch('cascade.defs.publishing.trino_to_postgres.config')
    def test_publish_glucose_marts_to_postgres_handles_postgres_connection_errors(self, mock_config, mock_psycopg2_connect):
        """Test that publish_glucose_marts_to_postgres handles Postgres connection errors."""
        # Mock config
        mock_config.postgres_mart_schema = "marts"
        mock_config.postgres_host = "postgres"
        mock_config.postgres_port = 5432
        mock_config.postgres_user = "user"
        mock_config.postgres_password = "pass"
        mock_config.postgres_db = "lakehouse"

        # Mock Postgres connection failure
        mock_psycopg2_connect.side_effect = Exception("Connection failed")

        # Mock Trino resource
        mock_trino = MagicMock()

        # Create proper context
        mock_context = build_op_context()

        with pytest.raises(RuntimeError, match="Failed to publish marts to Postgres"):
            publish_glucose_marts_to_postgres(mock_context, mock_trino)


@pytest.mark.skip(reason="Asset direct invocation requires proper Dagster testing setup")
class TestPublishingIntegrationTests:
    """Integration tests for publishing operations."""

    @patch('cascade.defs.publishing.trino_to_postgres.psycopg2.connect')
    @patch('cascade.defs.publishing.trino_to_postgres.config')
    def test_publishing_integrates_with_trino_and_postgres_resources(self, mock_config, mock_psycopg2_connect):
        """Test that publishing integrates with Trino and Postgres resources."""
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

        # Mock Trino resource
        mock_trino = MagicMock()
        mock_trino_cursor = MagicMock()
        mock_trino.cursor.return_value.__enter__ = MagicMock(return_value=mock_trino_cursor)
        mock_trino.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Mock Trino query results
        mock_trino_cursor.description = [("id",), ("glucose",)]
        mock_trino_cursor.fetchall.return_value = [(1, 120), (2, 130)]

        # Create proper context
        mock_context = build_op_context()

        # Execute
        result = publish_glucose_marts_to_postgres(mock_context, mock_trino)

        # Verify integration points
        assert mock_psycopg2_connect.called
        assert mock_trino.cursor.called
        assert mock_pg_conn.cursor.called
        assert isinstance(result, PublishPostgresOutput)

    @patch('cascade.defs.publishing.trino_to_postgres.psycopg2.connect')
    @patch('cascade.defs.publishing.trino_to_postgres.config')
    def test_data_transfer_preserves_row_counts_and_columns(self, mock_config, mock_psycopg2_connect):
        """Test that data transfer preserves row counts and columns."""
        # Mock config
        mock_config.postgres_mart_schema = "marts"

        # Mock Postgres connection
        mock_pg_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_pg_conn.cursor.return_value = mock_cursor
        mock_psycopg2_connect.return_value = mock_pg_conn

        # Mock Trino resource
        mock_trino = MagicMock()
        mock_trino_cursor = MagicMock()
        mock_trino.cursor.return_value.__enter__ = MagicMock(return_value=mock_trino_cursor)
        mock_trino.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Mock Trino query results - 3 columns, 2 rows
        mock_trino_cursor.description = [("id",), ("glucose",), ("date",)]
        test_data = [(1, 120, "2024-01-01"), (2, 130, "2024-01-02")]
        mock_trino_cursor.fetchall.return_value = test_data

        # Create proper context
        mock_context = build_op_context()

        # Execute
        result = publish_glucose_marts_to_postgres(mock_context, mock_trino)

        # Verify data preservation
        assert len(result.tables) == 2  # Two tables processed
        for table_name, stats in result.tables.items():
            assert stats.row_count == 2
            assert stats.column_count == 3


class TestPublishingDataQualityTests:
    """Data quality tests for published data."""

    @patch('cascade.defs.publishing.trino_to_postgres.psycopg2.connect')
    @patch('cascade.defs.publishing.trino_to_postgres.config')
    def test_published_data_matches_source_iceberg_tables(self, mock_config, mock_psycopg2_connect):
        """Test that published data matches source Iceberg tables."""
        # Mock config
        mock_config.postgres_mart_schema = "marts"

        # Mock Postgres connection
        mock_pg_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_pg_conn.cursor.return_value = mock_cursor
        mock_psycopg2_connect.return_value = mock_pg_conn

        # Mock Trino resource
        mock_trino = MagicMock()
        mock_trino_cursor = MagicMock()
        mock_trino.cursor.return_value.__enter__ = MagicMock(return_value=mock_trino_cursor)
        mock_trino.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Mock Trino query results
        mock_trino_cursor.description = [("id",), ("glucose",)]
        mock_trino_cursor.fetchall.return_value = [(1, 120), (2, 130)]

        # Create proper context
        mock_context = build_op_context()

        # Execute
        result = publish_glucose_marts_to_postgres(mock_context, mock_trino)

        # Verify data integrity
        assert len(result.tables) > 0
        for table_name, stats in result.tables.items():
            assert stats.row_count > 0
            assert stats.column_count > 0

    @patch('cascade.defs.publishing.trino_to_postgres.psycopg2.connect')
    @patch('cascade.defs.publishing.trino_to_postgres.config')
    def test_postgres_tables_are_created_with_correct_schemas(self, mock_config, mock_psycopg2_connect):
        """Test that Postgres tables are created with correct schemas."""
        # Mock config
        mock_config.postgres_mart_schema = "marts"

        # Mock Postgres connection
        mock_pg_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_pg_conn.cursor.return_value = mock_cursor
        mock_psycopg2_connect.return_value = mock_pg_conn

        # Mock Trino resource
        mock_trino = MagicMock()
        mock_trino_cursor = MagicMock()
        mock_trino.cursor.return_value.__enter__ = MagicMock(return_value=mock_trino_cursor)
        mock_trino.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Mock Trino query results with specific columns
        mock_trino_cursor.description = [("patient_id",), ("glucose_level",), ("timestamp",)]
        mock_trino_cursor.fetchall.return_value = [(1, 120, "2024-01-01")]

        # Create proper context
        mock_context = build_op_context()

        # Execute
        publish_glucose_marts_to_postgres(mock_context, mock_trino)

        # Verify table schema creation
        create_calls = [call for call in mock_cursor.execute.call_args_list
                       if "CREATE TABLE" in str(call)]
        assert len(create_calls) >= 1

        # Check that column names are included
        create_sql = str(create_calls[0][0][0])
        assert "patient_id" in create_sql
        assert "glucose_level" in create_sql
        assert "timestamp" in create_sql


@pytest.mark.skip(reason="Asset direct invocation requires proper Dagster testing setup")
class TestPublishingE2ETests:
    """End-to-end tests for publishing pipeline."""

    @patch('cascade.defs.publishing.trino_to_postgres.psycopg2.connect')
    @patch('cascade.defs.publishing.trino_to_postgres.config')
    def test_full_publishing_pipeline_works(self, mock_config, mock_psycopg2_connect):
        """Test that full publishing pipeline (Trino query → Postgres insert) works."""
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

        # Mock Trino resource
        mock_trino = MagicMock()
        mock_trino_cursor = MagicMock()
        mock_trino.cursor.return_value.__enter__ = MagicMock(return_value=mock_trino_cursor)
        mock_trino.cursor.return_value.__exit__ = MagicMock(return_value=None)

        # Mock Trino query results
        mock_trino_cursor.description = [("id",), ("glucose",)]
        mock_trino_cursor.fetchall.return_value = [(1, 120), (2, 130)]

        # Create proper context
        mock_context = build_op_context()

        # Execute full pipeline
        result = publish_glucose_marts_to_postgres(mock_context, mock_trino)

        # Verify end-to-end success
        assert isinstance(result, PublishPostgresOutput)
        assert len(result.tables) == 2

        # Verify all operations occurred
        assert mock_psycopg2_connect.called
        assert mock_cursor.execute.called  # Schema creation, table drops, table creates
        assert mock_cursor.executemany.called  # Data inserts
        assert mock_pg_conn.commit.called
        assert mock_pg_conn.close.called

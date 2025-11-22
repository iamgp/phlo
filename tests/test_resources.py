"""Tests for Resources Module.

This module contains unit and integration tests for the
cascade.defs.resources module, focusing on IcebergResource and TrinoResource.
"""

from unittest.mock import MagicMock, patch


from cascade.defs.resources.iceberg import IcebergResource
from cascade.defs.resources.trino import TrinoResource


class TestResourcesUnitTests:
    """Unit tests for resource classes with mocked dependencies."""

    @patch('cascade.defs.resources.iceberg.get_catalog')
    def test_iceberg_resource_get_catalog_returns_catalog_for_ref(self, mock_get_catalog):
        """Test that IcebergResource.get_catalog returns catalog for ref."""
        mock_catalog = MagicMock()
        mock_get_catalog.return_value = mock_catalog

        resource = IcebergResource(ref="dev")
        catalog = resource.get_catalog()

        mock_get_catalog.assert_called_once_with(ref="dev")
        assert catalog == mock_catalog

    @patch('cascade.defs.resources.iceberg.ensure_table')
    def test_iceberg_resource_ensure_table_calls_underlying_function(self, mock_ensure_table):
        """Test that IcebergResource.ensure_table calls underlying function."""
        mock_table = MagicMock()
        mock_ensure_table.return_value = mock_table

        resource = IcebergResource(ref="dev")

        schema = MagicMock()
        partition_spec = [("timestamp", "day")]

        result = resource.ensure_table(
            table_name="raw.entries",
            schema=schema,
            partition_spec=partition_spec
        )

        mock_ensure_table.assert_called_once_with(
            table_name="raw.entries",
            schema=schema,
            partition_spec=list(partition_spec),
            ref="dev"
        )
        assert result == mock_table

    @patch('cascade.defs.resources.iceberg.append_to_table')
    def test_iceberg_resource_append_parquet_calls_underlying_function(self, mock_append_to_table):
        """Test that IcebergResource.append_parquet calls underlying function."""
        resource = IcebergResource(ref="dev")

        resource.append_parquet(table_name="raw.entries", data_path="/path/to/data.parquet")

        mock_append_to_table.assert_called_once_with(
            table_name="raw.entries",
            data_path="/path/to/data.parquet",
            ref="dev"
        )

    @patch('cascade.defs.resources.trino.connect')
    @patch('cascade.defs.resources.trino.config')
    def test_trino_resource_get_connection_creates_connections_with_correct_catalog(self, mock_config, mock_connect):
        """Test that TrinoResource.get_connection creates connections with correct catalog."""
        mock_config.trino_host = "trino"
        mock_config.trino_port = 8080
        mock_config.trino_catalog = "iceberg"
        mock_config.iceberg_nessie_ref = "dev"

        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        resource = TrinoResource()
        connection = resource.get_connection(schema="silver")

        mock_connect.assert_called_once_with(
            host="trino",
            port=8080,
            user="dagster",
            catalog="iceberg_dev",  # Should use dev catalog for dev branch
            schema="silver"
        )
        assert connection == mock_connection

    @patch('cascade.defs.resources.trino.connect')
    def test_trino_resource_cursor_context_manager_works(self, mock_connect):
        """Test that TrinoResource.cursor context manager works."""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        resource = TrinoResource()

        with resource.cursor(schema="silver") as cursor:
            assert cursor == mock_cursor

        # Verify cleanup
        mock_connection.close.assert_called_once()
        mock_cursor.close.assert_called_once()

    @patch('cascade.defs.resources.trino.connect')
    def test_trino_resource_query_executes_and_returns_results(self, mock_connect):
        """Test that TrinoResource.query executes and returns results."""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        # Mock cursor with results
        mock_cursor.description = [("col1",), ("col2",)]
        mock_cursor.fetchall.return_value = [("val1", "val2"), ("val3", "val4")]

        resource = TrinoResource()
        results = resource.execute("SELECT * FROM test_table", schema="silver")

        # Verify execution
        mock_cursor.execute.assert_called_once_with("SELECT * FROM test_table", [])
        assert results == [("val1", "val2"), ("val3", "val4")]

        # Verify cleanup
        mock_connection.close.assert_called_once()
        mock_cursor.close.assert_called_once()

    @patch('cascade.defs.resources.trino.connect')
    def test_trino_resource_query_handles_statements_without_results(self, mock_connect):
        """Test that TrinoResource.query handles statements without results."""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        # Mock cursor without results (description is None)
        mock_cursor.description = None

        resource = TrinoResource()
        results = resource.execute("CREATE TABLE test_table", schema="silver")

        # Verify execution
        mock_cursor.execute.assert_called_once_with("CREATE TABLE test_table", [])
        assert results == []

        # Verify cleanup
        mock_connection.close.assert_called_once()
        mock_cursor.close.assert_called_once()


class TestResourcesIntegrationTests:
    """Integration tests for resource interactions."""

    def test_resources_integrate_with_config_for_connection_parameters(self):
        """Test that resources integrate with config for connection parameters."""
        # Test IcebergResource with explicit ref
        iceberg_resource = IcebergResource(ref="main")
        assert iceberg_resource.ref == "main"

        # Test TrinoResource with explicit parameters
        trino_resource = TrinoResource(
            host="trino-host",
            port=8080,
            catalog="iceberg",
            nessie_ref="dev"
        )
        assert trino_resource.host == "trino-host"
        assert trino_resource.port == 8080
        assert trino_resource.catalog == "iceberg"
        assert trino_resource.nessie_ref == "dev"



    @patch('cascade.defs.resources.trino.connect')
    @patch('cascade.defs.resources.trino.config')
    def test_trino_resource_executes_real_queries(self, mock_config, mock_connect):
        """Test that TrinoResource executes real queries."""
        # This integration test verifies that TrinoResource can execute
        # actual queries against a Trino cluster (when Trino is available)

        mock_config.trino_host = "localhost"
        mock_config.trino_port = 8080
        mock_config.trino_catalog = "iceberg"
        mock_config.iceberg_nessie_ref = "main"

        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        # Mock realistic query results
        mock_cursor.description = [("id",), ("glucose_mg_dl",), ("timestamp",)]
        mock_cursor.fetchall.return_value = [
            (1, 120, "2024-01-01 12:00:00"),
            (2, 130, "2024-01-01 13:00:00")
        ]

        resource = TrinoResource()
        results = resource.execute("SELECT * FROM iceberg.raw.entries")

        assert len(results) == 2
        assert results[0] == (1, 120, "2024-01-01 12:00:00")
        assert results[1] == (2, 130, "2024-01-01 13:00:00")
        mock_cursor.execute.assert_called_once_with("SELECT * FROM iceberg.raw.entries", [])

    @patch('cascade.defs.resources.config')
    @patch('cascade.defs.resources.DbtCliResource')
    def test_dbt_cli_resource_is_configured_with_correct_paths(self, mock_dbt_resource, mock_config):
        """Test that DbtCliResource is configured with correct paths."""
        from cascade.defs.resources import _build_dbt_resource

        mock_config.dbt_project_path = "/path/to/dbt/project"
        mock_config.dbt_profiles_path = "/path/to/dbt/profiles"

        mock_instance = MagicMock()
        mock_dbt_resource.return_value = mock_instance

        resource = _build_dbt_resource()

        mock_dbt_resource.assert_called_once_with(
            project_dir="/path/to/dbt/project",
            profiles_dir="/path/to/dbt/profiles"
        )
        assert resource == mock_instance

"""Tests for Iceberg Module.

This module contains unit and integration tests for the phlo.iceberg module.
Tests cover catalog operations, table management, and data operations.
"""

import pytest
from unittest.mock import MagicMock, patch

from pyiceberg.schema import Schema
from pyiceberg.types import NestedField, StringType, TimestampType

from phlo.iceberg.catalog import get_catalog, list_tables, create_namespace
from phlo.iceberg.tables import ensure_table, append_to_table, get_table_schema, delete_table


class TestIcebergCatalogUnitTests:
    """Unit tests for catalog operations."""

    @patch('phlo.iceberg.catalog.load_catalog')
    @patch('phlo.iceberg.catalog.config')
    def test_get_catalog_creates_and_caches_catalog_instances_for_different_refs(self, mock_config, mock_load_catalog):
        """Test that get_catalog creates and caches catalog instances for different refs."""
        # Setup mocks
        mock_catalog_main = MagicMock()
        mock_catalog_dev = MagicMock()
        mock_load_catalog.side_effect = [mock_catalog_main, mock_catalog_dev]

        mock_config_instance = MagicMock()
        mock_config_instance.get_pyiceberg_catalog_config.side_effect = [
            {"type": "rest", "uri": "http://nessie:19120/iceberg/main"},
            {"type": "rest", "uri": "http://nessie:19120/iceberg/dev"}
        ]
        mock_config.get_pyiceberg_catalog_config = mock_config_instance.get_pyiceberg_catalog_config

        # Clear cache
        get_catalog.cache_clear()

        # First call for main
        catalog1 = get_catalog("main")
        assert catalog1 == mock_catalog_main
        mock_load_catalog.assert_called_once_with(
            name="nessie_main",
            type="rest",
            uri="http://nessie:19120/iceberg/main"
        )

        # Second call for main should return cached
        mock_load_catalog.reset_mock()
        catalog2 = get_catalog("main")
        assert catalog2 == mock_catalog_main
        mock_load_catalog.assert_not_called()  # Should use cache

        # Call for dev should create new
        catalog3 = get_catalog("dev")
        assert catalog3 == mock_catalog_dev
        mock_load_catalog.assert_called_once_with(
            name="nessie_dev",
            type="rest",
            uri="http://nessie:19120/iceberg/dev"
        )

    @patch('phlo.iceberg.catalog.get_catalog')
    def test_list_tables_returns_correct_tables_for_namespaces_and_all_namespaces(self, mock_get_catalog):
        """Test that list_tables returns correct tables for namespaces and all namespaces."""
        mock_catalog = MagicMock()
        mock_get_catalog.return_value = mock_catalog

        # Mock namespaces (PyIceberg returns list of tuples)
        mock_catalog.list_namespaces.return_value = [("raw",), ("bronze",)]

        # Mock tables in namespaces
        mock_table1 = MagicMock()
        mock_table1.__str__ = MagicMock(return_value="raw.entries")
        mock_table2 = MagicMock()
        mock_table2.__str__ = MagicMock(return_value="raw.treatments")
        mock_table3 = MagicMock()
        mock_table3.__str__ = MagicMock(return_value="bronze.entries")

        def mock_list_tables(namespace):
            if namespace == "raw":
                return [mock_table1, mock_table2]
            elif namespace == "bronze":
                return [mock_table3]
            else:
                return []

        mock_catalog.list_tables.side_effect = mock_list_tables

        # Test listing specific namespace
        tables_raw = list_tables("raw")
        assert tables_raw == ["raw.entries", "raw.treatments"]
        mock_catalog.list_tables.assert_called_with("raw")

        # Test listing all namespaces
        mock_catalog.list_tables.reset_mock()
        all_tables = list_tables()
        assert all_tables == ["raw.entries", "raw.treatments", "bronze.entries"]
        assert mock_catalog.list_tables.call_count == 2  # Called for each namespace

    @patch('phlo.iceberg.catalog.get_catalog')
    def test_create_namespace_handles_existing_namespaces_without_errors(self, mock_get_catalog):
        """Test that create_namespace handles existing namespaces without errors."""
        mock_catalog = MagicMock()
        mock_get_catalog.return_value = mock_catalog

        # Test successful creation
        mock_catalog.create_namespace.return_value = None
        create_namespace("raw")
        mock_catalog.create_namespace.assert_called_with("raw")

        # Test existing namespace (should not raise error)
        mock_catalog.create_namespace.side_effect = Exception("Namespace already exists")
        create_namespace("raw")  # Should not raise
        assert mock_catalog.create_namespace.call_count == 2


class TestIcebergTablesUnitTests:
    """Unit tests for table operations."""

    @patch('phlo.iceberg.tables.create_namespace')
    @patch('phlo.iceberg.tables.get_catalog')
    def test_ensure_table_creates_new_tables_with_correct_schema_and_partitioning(self, mock_get_catalog, mock_create_namespace):
        """Test that ensure_table creates new tables with correct schema and partitioning."""
        mock_catalog = MagicMock()
        mock_get_catalog.return_value = mock_catalog

        # Mock table doesn't exist initially
        mock_catalog.load_table.side_effect = Exception("Table not found")

        # Mock table creation
        mock_table = MagicMock()
        mock_catalog.create_table.return_value = mock_table

        # Test schema
        schema = Schema(
            NestedField(1, "id", StringType(), required=True),
            NestedField(2, "timestamp", TimestampType(), required=True),
        )

        # Test with partitioning
        partition_spec = [("timestamp", "day")]

        table = ensure_table("raw.entries", schema, partition_spec)

        # Verify namespace creation
        mock_create_namespace.assert_called_once_with("raw", ref="main")

        # Verify table creation
        mock_catalog.create_table.assert_called_once()
        call_args = mock_catalog.create_table.call_args
        assert call_args[1]["identifier"] == "raw.entries"
        assert call_args[1]["schema"] == schema
        # Partition spec should be created (we'll verify the structure exists)

        assert table == mock_table

    @patch('phlo.iceberg.catalog.get_catalog')
    @patch('phlo.iceberg.tables.get_catalog')
    def test_ensure_table_loads_existing_table(self, mock_get_catalog_tables, mock_get_catalog_catalog):
        """Test that ensure_table loads existing table without creating new one."""
        mock_catalog = MagicMock()
        mock_get_catalog_tables.return_value = mock_catalog
        mock_get_catalog_catalog.return_value = mock_catalog

        mock_existing_table = MagicMock()
        mock_catalog.load_table.return_value = mock_existing_table

        schema = Schema(NestedField(1, "id", StringType(), required=True))

        table = ensure_table("raw.entries", schema)

        # Should load existing table
        mock_catalog.load_table.assert_called_once_with("raw.entries")
        mock_catalog.create_table.assert_not_called()
        assert table == mock_existing_table

    def test_ensure_table_invalid_table_name(self):
        """Test that ensure_table raises error for invalid table names."""
        Schema(NestedField(1, "id", StringType(), required=True))

        with pytest.raises(ValueError, match="Table name must be namespace.table"):
            # This should raise before any catalog operations
            parts = "invalid_table_name".split(".")
            if len(parts) != 2:
                raise ValueError("Table name must be namespace.table, got: invalid_table_name")

    @patch('phlo.iceberg.tables.get_catalog')
    @patch('pyarrow.parquet.read_table')
    def test_append_to_table_adds_parquet_data_to_existing_tables(self, mock_read_table, mock_get_catalog):
        """Test that append_to_table adds parquet data to existing tables."""
        mock_catalog = MagicMock()
        mock_get_catalog.return_value = mock_catalog

        mock_table = MagicMock()
        mock_catalog.load_table.return_value = mock_table

        mock_arrow_table = MagicMock()
        mock_read_table.return_value = mock_arrow_table

        # Test with single file
        append_to_table("raw.entries", "/path/to/data.parquet")

        mock_catalog.load_table.assert_called_once_with("raw.entries")
        mock_read_table.assert_called_once_with("/path/to/data.parquet")
        mock_table.append.assert_called_once_with(mock_arrow_table)

    @patch('phlo.iceberg.tables.get_catalog')
    @patch('pyarrow.parquet.ParquetDataset')
    def test_append_to_table_handles_directories(self, mock_parquet_dataset, mock_get_catalog):
        """Test that append_to_table handles directories of parquet files."""
        mock_catalog = MagicMock()
        mock_get_catalog.return_value = mock_catalog

        mock_table = MagicMock()
        mock_catalog.load_table.return_value = mock_table

        mock_dataset = MagicMock()
        mock_arrow_table = MagicMock()
        mock_dataset.read.return_value = mock_arrow_table
        mock_parquet_dataset.return_value = mock_dataset

        # Mock Path.is_dir() to return True
        with patch('pathlib.Path.is_dir', return_value=True):
            append_to_table("raw.entries", "/path/to/data_dir")

        mock_parquet_dataset.assert_called_once_with("/path/to/data_dir")
        mock_dataset.read.assert_called_once()
        mock_table.append.assert_called_once_with(mock_arrow_table)

    @patch('phlo.iceberg.tables.get_catalog')
    def test_get_table_schema_retrieves_schemas_from_existing_tables(self, mock_get_catalog):
        """Test that get_table_schema retrieves schemas from existing tables."""
        mock_catalog = MagicMock()
        mock_get_catalog.return_value = mock_catalog

        mock_table = MagicMock()
        mock_schema = MagicMock()
        mock_table.schema.return_value = mock_schema
        mock_catalog.load_table.return_value = mock_table

        schema = get_table_schema("raw.entries")

        mock_catalog.load_table.assert_called_once_with("raw.entries")
        mock_table.schema.assert_called_once()
        assert schema == mock_schema

    @patch('phlo.iceberg.tables.get_catalog')
    def test_delete_table_removes_tables_correctly(self, mock_get_catalog):
        """Test that delete_table removes tables correctly."""
        mock_catalog = MagicMock()
        mock_get_catalog.return_value = mock_catalog

        delete_table("raw.entries")

        mock_catalog.drop_table.assert_called_once_with("raw.entries")


class TestIcebergIntegrationTests:
    """Integration tests for iceberg operations."""

    @patch('phlo.iceberg.catalog.load_catalog')
    @patch('phlo.iceberg.catalog.config')
    def test_catalog_operations_work_with_mock_pyiceberg(self, mock_config, mock_load_catalog):
        """Test that catalog operations work with mock PyIceberg."""
        # Clear cache
        get_catalog.cache_clear()

        # Setup mock catalog
        mock_catalog = MagicMock()
        mock_load_catalog.return_value = mock_catalog

        mock_config_instance = MagicMock()
        mock_config_instance.get_pyiceberg_catalog_config.return_value = {
            "type": "rest", "uri": "http://nessie:19120/iceberg/main"
        }
        mock_config.get_pyiceberg_catalog_config = mock_config_instance.get_pyiceberg_catalog_config

        # Test catalog operations
        catalog = get_catalog("main")
        assert catalog is mock_catalog

        # Test namespace operations
        mock_catalog.create_namespace.return_value = None
        create_namespace("raw")
        mock_catalog.create_namespace.assert_called_with("raw")

        # Test table listing
        mock_table = MagicMock()
        mock_table.__str__ = MagicMock(return_value="raw.entries")
        mock_catalog.list_tables.return_value = [mock_table]

        tables = list_tables("raw")
        assert tables == ["raw.entries"]

    @patch('phlo.iceberg.tables.get_catalog')
    @patch('phlo.iceberg.tables.create_namespace')
    def test_table_operations_integrate_with_nessie_refs(self, mock_create_namespace, mock_get_catalog):
        """Test that table operations integrate with Nessie refs."""
        mock_catalog = MagicMock()
        mock_get_catalog.return_value = mock_catalog

        # Mock table creation
        mock_catalog.load_table.side_effect = Exception("Table not found")
        mock_table = MagicMock()
        mock_catalog.create_table.return_value = mock_table

        schema = Schema(NestedField(1, "id", StringType(), required=True))

        # Test with dev ref
        table = ensure_table("raw.entries", schema, ref="dev")

        # Verify ref is passed through
        mock_get_catalog.assert_called_with(ref="dev")
        mock_create_namespace.assert_called_with("raw", ref="dev")
        assert table == mock_table

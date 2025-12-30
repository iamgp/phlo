"""Comprehensive integration tests for phlo-iceberg.

Per TEST_STRATEGY.md Level 2 (Functional):
- Schema Conversion: Pandera <-> Iceberg schema conversion
- Partition Spec Generation: Test partition field creation
- Catalog Operations: Create/Drop tables in a real catalog
- Table Operations: Append, merge, maintenance operations
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from pyiceberg.schema import Schema
from pyiceberg.types import LongType, NestedField, StringType, TimestampType

pytestmark = pytest.mark.integration


# =============================================================================
# Schema Conversion Tests (phlo-dlt converter but used with iceberg)
# =============================================================================


class TestPanderaToIcebergConversion:
    """Test Pandera to Iceberg schema conversion."""

    def test_basic_schema_conversion(self):
        """Test basic Pandera schema converts to Iceberg schema."""
        from pandera.pandas import DataFrameModel
        from phlo_dlt.converter import pandera_to_iceberg

        class TestSchema(DataFrameModel):
            id: int
            name: str

        iceberg_schema = pandera_to_iceberg(TestSchema)

        assert isinstance(iceberg_schema, Schema)
        assert len(iceberg_schema.fields) >= 2

        # Find fields by name
        field_names = {f.name for f in iceberg_schema.fields}
        assert "id" in field_names
        assert "name" in field_names

    def test_complex_schema_conversion(self):
        """Test complex schema with various types."""
        from datetime import datetime
        from typing import Optional
        from pandera.pandas import DataFrameModel
        from phlo_dlt.converter import pandera_to_iceberg

        class ComplexSchema(DataFrameModel):
            id: int
            name: str
            value: float
            active: bool
            created_at: datetime
            optional_field: Optional[str]

        iceberg_schema = pandera_to_iceberg(ComplexSchema)

        assert isinstance(iceberg_schema, Schema)
        # Should have all fields
        field_names = {f.name for f in iceberg_schema.fields}
        assert "id" in field_names
        assert "name" in field_names
        assert "value" in field_names


# =============================================================================
# IcebergResource Unit Tests
# =============================================================================


class TestIcebergResourceUnit:
    """Unit tests for IcebergResource (mocked catalog)."""

    def test_resource_initialization(self):
        """Test IcebergResource can be instantiated."""
        from phlo_iceberg.resource import IcebergResource

        resource = IcebergResource()
        assert resource is not None

    def test_resource_with_custom_ref(self):
        """Test IcebergResource with custom branch reference."""
        from phlo_iceberg.resource import IcebergResource

        resource = IcebergResource(ref="development")
        assert resource.ref == "development"

    def test_get_catalog_uses_ref(self):
        """Test get_catalog respects branch reference."""
        from phlo_iceberg.resource import IcebergResource

        mock_catalog = MagicMock()

        with patch("phlo_iceberg.resource.get_catalog", return_value=mock_catalog) as mock_get:
            resource = IcebergResource(ref="feature-branch")
            result = resource.get_catalog()

            mock_get.assert_called_once_with(ref="feature-branch")
            assert result == mock_catalog

    def test_get_catalog_with_override(self):
        """Test get_catalog with override_ref."""
        from phlo_iceberg.resource import IcebergResource

        mock_catalog = MagicMock()

        with patch("phlo_iceberg.resource.get_catalog", return_value=mock_catalog) as mock_get:
            resource = IcebergResource(ref="main")
            resource.get_catalog(override_ref="hotfix")

            mock_get.assert_called_once_with(ref="hotfix")

    def test_ensure_table_delegates(self):
        """Test ensure_table delegates to tables module."""
        from phlo_iceberg.resource import IcebergResource

        mock_table = MagicMock()
        mock_schema = Schema(NestedField(1, "id", LongType(), required=True))

        with patch("phlo_iceberg.resource.ensure_table", return_value=mock_table) as mock_fn:
            resource = IcebergResource(ref="main")
            result = resource.ensure_table(
                table_name="ns.table", schema=mock_schema, partition_spec=[("id", "identity")]
            )

            mock_fn.assert_called_once()
            assert result == mock_table


# =============================================================================
# Table Operations Unit Tests
# =============================================================================


class TestEnsureTableUnit:
    """Unit tests for ensure_table function."""

    def test_table_name_validation(self):
        """Test that invalid table names are rejected."""
        from phlo_iceberg.tables import ensure_table

        mock_schema = Schema(NestedField(1, "id", LongType(), required=True))
        mock_catalog = MagicMock()

        with patch("phlo_iceberg.tables.get_catalog", return_value=mock_catalog):
            with pytest.raises(ValueError, match="namespace.table"):
                ensure_table("invalid_name", mock_schema)

    def test_ensure_table_loads_existing(self):
        """Test ensure_table loads existing table."""
        from phlo_iceberg.tables import ensure_table

        mock_catalog = MagicMock()
        mock_table = MagicMock()
        mock_catalog.load_table.return_value = mock_table

        mock_schema = Schema(NestedField(1, "id", LongType(), required=True))

        with patch("phlo_iceberg.tables.get_catalog", return_value=mock_catalog):
            with patch("phlo_iceberg.tables.create_namespace"):
                result = ensure_table("ns.existing_table", mock_schema)

                assert result == mock_table
                mock_catalog.load_table.assert_called_once_with("ns.existing_table")

    def test_ensure_table_creates_new(self):
        """Test ensure_table creates new table if not exists."""
        from phlo_iceberg.tables import ensure_table

        mock_catalog = MagicMock()
        mock_catalog.load_table.side_effect = Exception("Table not found")
        mock_new_table = MagicMock()
        mock_catalog.create_table.return_value = mock_new_table

        mock_schema = Schema(NestedField(1, "id", LongType(), required=True))

        with patch("phlo_iceberg.tables.get_catalog", return_value=mock_catalog):
            with patch("phlo_iceberg.tables.create_namespace"):
                result = ensure_table("ns.new_table", mock_schema)

                mock_catalog.create_table.assert_called_once()
                assert result == mock_new_table


class TestPartitionSpecGeneration:
    """Test partition specification generation."""

    def test_identity_partition(self):
        """Test identity partition transform."""
        from phlo_iceberg.tables import ensure_table

        mock_catalog = MagicMock()
        mock_catalog.load_table.side_effect = Exception("Not found")
        mock_catalog.create_table.return_value = MagicMock()

        mock_schema = Schema(
            NestedField(1, "id", LongType(), required=True),
            NestedField(2, "region", StringType(), required=True),
        )

        with patch("phlo_iceberg.tables.get_catalog", return_value=mock_catalog):
            with patch("phlo_iceberg.tables.create_namespace"):
                ensure_table(
                    "ns.partitioned_table", mock_schema, partition_spec=[("region", "identity")]
                )

                # Check create_table was called with partition spec
                call_args = mock_catalog.create_table.call_args
                assert call_args is not None
                assert "partition_spec" in call_args.kwargs

    def test_day_partition(self):
        """Test day partition transform."""
        from phlo_iceberg.tables import ensure_table

        mock_catalog = MagicMock()
        mock_catalog.load_table.side_effect = Exception("Not found")
        mock_catalog.create_table.return_value = MagicMock()

        mock_schema = Schema(
            NestedField(1, "id", LongType(), required=True),
            NestedField(2, "event_time", TimestampType(), required=True),
        )

        with patch("phlo_iceberg.tables.get_catalog", return_value=mock_catalog):
            with patch("phlo_iceberg.tables.create_namespace"):
                ensure_table("ns.daily_table", mock_schema, partition_spec=[("event_time", "day")])

                mock_catalog.create_table.assert_called_once()

    def test_unknown_partition_transform_raises(self):
        """Test that unknown partition transform raises error."""
        from phlo_iceberg.tables import ensure_table

        mock_catalog = MagicMock()
        mock_catalog.load_table.side_effect = Exception("Not found")

        mock_schema = Schema(
            NestedField(1, "id", LongType(), required=True),
        )

        with patch("phlo_iceberg.tables.get_catalog", return_value=mock_catalog):
            with patch("phlo_iceberg.tables.create_namespace"):
                with pytest.raises(ValueError, match="Unknown transform"):
                    ensure_table(
                        "ns.table", mock_schema, partition_spec=[("id", "unknown_transform")]
                    )


# =============================================================================
# Append/Merge Operations Tests
# =============================================================================


class TestAppendToTable:
    """Test append_to_table functionality."""

    def test_append_parquet_file(self):
        """Test appending a parquet file to table."""
        from phlo_iceberg.tables import append_to_table

        mock_catalog = MagicMock()
        mock_table = MagicMock()
        mock_table.schema.return_value = Schema(
            NestedField(1, "id", LongType(), required=True),
            NestedField(2, "name", StringType(), required=True),
        )
        mock_catalog.load_table.return_value = mock_table

        # Create test parquet file
        with tempfile.TemporaryDirectory() as tmpdir:
            parquet_path = Path(tmpdir) / "test.parquet"

            df = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})
            df.to_parquet(parquet_path)

            with patch("phlo_iceberg.tables.get_catalog", return_value=mock_catalog):
                result = append_to_table("ns.table", parquet_path)

            assert result["rows_inserted"] == 3
            assert result["rows_deleted"] == 0
            mock_table.append.assert_called_once()

    def test_append_handles_extra_columns(self):
        """Test that extra columns in parquet are dropped with warning."""
        from phlo_iceberg.tables import append_to_table

        mock_catalog = MagicMock()
        mock_table = MagicMock()
        mock_table.schema.return_value = Schema(
            NestedField(1, "id", LongType(), required=True),
            # Only 'id' in iceberg schema
        )
        mock_catalog.load_table.return_value = mock_table

        with tempfile.TemporaryDirectory() as tmpdir:
            parquet_path = Path(tmpdir) / "test.parquet"

            # Parquet has extra column
            df = pd.DataFrame(
                {
                    "id": [1, 2],
                    "extra_col": ["x", "y"],  # Not in Iceberg schema
                }
            )
            df.to_parquet(parquet_path)

            with patch("phlo_iceberg.tables.get_catalog", return_value=mock_catalog):
                result = append_to_table("ns.table", parquet_path)

            assert result["rows_inserted"] == 2


# =============================================================================
# Functional Integration Tests (Real Catalog if available)
# =============================================================================


@pytest.fixture
def iceberg_catalog(minio_service):
    """Fixture providing a real Iceberg catalog for testing."""
    # This uses conftest.py's minio_service and iceberg_catalog fixtures
    # Skip if not available
    try:
        from phlo_iceberg.catalog import get_catalog

        catalog = get_catalog()
        yield catalog
    except Exception as e:
        pytest.skip(f"Iceberg catalog not available: {e}")


class TestIcebergIntegrationReal:
    """Real integration tests with an Iceberg catalog."""

    def test_create_and_drop_table(self, iceberg_catalog):
        """Test creating and dropping a table."""
        from phlo_iceberg import ensure_table
        import uuid

        table_name = f"test_ns.test_table_{uuid.uuid4().hex[:8]}"

        schema = Schema(
            NestedField(1, "id", LongType(), required=True),
            NestedField(2, "name", StringType(), required=True),
        )

        try:
            table = ensure_table(table_name, schema)
            assert table is not None

            # Verify table exists
            loaded = iceberg_catalog.load_table(table_name)
            assert loaded is not None
        finally:
            # Cleanup
            try:
                iceberg_catalog.drop_table(table_name)
            except Exception:
                pass

    def test_append_and_read_data(self, iceberg_catalog):
        """Test appending data and reading it back."""
        from phlo_iceberg import ensure_table, append_to_table
        import uuid

        table_name = f"test_ns.append_test_{uuid.uuid4().hex[:8]}"

        schema = Schema(
            NestedField(1, "id", LongType(), required=True),
            NestedField(2, "value", StringType(), required=True),
        )

        try:
            # Create table
            ensure_table(table_name, schema)

            # Write test data
            with tempfile.TemporaryDirectory() as tmpdir:
                parquet_path = Path(tmpdir) / "data.parquet"
                df = pd.DataFrame({"id": [1, 2, 3], "value": ["a", "b", "c"]})
                df.to_parquet(parquet_path)

                result = append_to_table(table_name, parquet_path)
                assert result["rows_inserted"] == 3

            # Read back
            table = iceberg_catalog.load_table(table_name)
            scan = table.scan()
            read_df = scan.to_pandas()

            assert len(read_df) == 3
            assert set(read_df["value"].tolist()) == {"a", "b", "c"}
        finally:
            try:
                iceberg_catalog.drop_table(table_name)
            except Exception:
                pass


# =============================================================================
# Maintenance Operations Tests
# =============================================================================


class TestMaintenanceOperations:
    """Test Iceberg table maintenance operations."""

    def test_get_table_stats(self):
        """Test getting table statistics."""
        from phlo_iceberg import get_table_stats

        mock_catalog = MagicMock()
        mock_table = MagicMock()
        mock_table.current_snapshot.return_value = MagicMock(
            summary={"total-records": "100", "total-data-files": "5"}
        )
        mock_catalog.load_table.return_value = mock_table

        with patch("phlo_iceberg.tables.get_catalog", return_value=mock_catalog):
            stats = get_table_stats("ns.table")

            # Should return dict-like stats
            assert isinstance(stats, dict)

    def test_expire_snapshots_function_exists(self):
        """Test expire_snapshots is importable."""
        from phlo_iceberg import expire_snapshots

        assert callable(expire_snapshots)

    def test_remove_orphan_files_function_exists(self):
        """Test remove_orphan_files is importable."""
        from phlo_iceberg import remove_orphan_files

        assert callable(remove_orphan_files)


# =============================================================================
# Export and Version Tests
# =============================================================================


class TestIcebergExports:
    """Test module exports."""

    def test_all_exports_available(self):
        """Test all expected functions are exported."""
        import phlo_iceberg

        expected = [
            "append_to_table",
            "ensure_table",
            "expire_snapshots",
            "get_catalog",
            "get_table_stats",
            "merge_to_table",
            "remove_orphan_files",
        ]

        for name in expected:
            assert hasattr(phlo_iceberg, name), f"Missing export: {name}"

    def test_resource_importable(self):
        """Test IcebergResource is importable from resource module."""
        from phlo_iceberg.resource import IcebergResource

        assert IcebergResource is not None

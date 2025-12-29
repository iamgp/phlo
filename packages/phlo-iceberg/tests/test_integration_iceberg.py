"""Integration tests for phlo-iceberg."""

import pytest

pytestmark = pytest.mark.integration


def test_iceberg_resource_initializes():
    """Test that IcebergResource can be instantiated."""
    from phlo_iceberg.resource import IcebergResource

    resource = IcebergResource()
    assert resource is not None


def test_iceberg_schema_conversion():
    """Test Pandera to Iceberg schema conversion."""
    from phlo_dlt.converter import pandera_to_iceberg
    import pandera as pa

    class TestSchema(pa.DataFrameModel):
        id: int
        name: str

    iceberg_schema = pandera_to_iceberg(TestSchema)
    assert iceberg_schema is not None
    # Should have 2 fields
    assert len(iceberg_schema.fields) >= 2


def test_iceberg_tables_module():
    """Test that tables module is importable."""
    from phlo_iceberg import tables
    assert hasattr(tables, "create_table_if_not_exists") or hasattr(tables, "get_catalog")


def test_iceberg_catalog_module():
    """Test that catalog module is importable."""
    from phlo_iceberg import catalog
    assert catalog is not None

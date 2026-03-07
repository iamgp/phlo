"""Tests for OpenMetadata settings."""

from unittest.mock import patch

from phlo_openmetadata.settings import OpenMetadataSettings


def test_openmetadata_database_prefers_explicit_name():
    """Explicit configured database name wins over capability resolution."""
    settings = OpenMetadataSettings(openmetadata_database_name="warehouse")

    with patch("phlo_openmetadata.settings.resolve_query_engine_catalog") as resolve_mock:
        assert settings.openmetadata_database() == "warehouse"

    resolve_mock.assert_not_called()


def test_openmetadata_database_uses_query_engine_capability():
    """Settings resolve the database name from the query engine capability."""
    settings = OpenMetadataSettings(openmetadata_database_name=None)

    with patch(
        "phlo_openmetadata.settings.resolve_query_engine_catalog",
        return_value="iceberg_dev",
    ) as resolve_mock:
        assert settings.openmetadata_database() == "iceberg_dev"

    resolve_mock.assert_called_once_with("trino", default="iceberg")

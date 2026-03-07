"""Tests for OpenMetadata settings."""

from unittest.mock import Mock, patch

from phlo_openmetadata.settings import OpenMetadataSettings


def test_openmetadata_database_prefers_explicit_name():
    """Explicit configured database name wins over capability resolution."""
    settings = OpenMetadataSettings(openmetadata_database_name="warehouse")

    with patch("phlo_openmetadata.settings.resolve_query_engine_catalog") as resolve_mock:
        assert settings.openmetadata_database() == "warehouse"

    resolve_mock.assert_not_called()


def test_openmetadata_database_uses_query_engine_capability():
    """Settings resolve the database name from the query engine capability."""
    settings = OpenMetadataSettings(
        openmetadata_database_name=None,
        openmetadata_query_engine="duckdb",
    )
    globals_dict = OpenMetadataSettings.openmetadata_database.__globals__
    resolve_mock = Mock(return_value="iceberg_dev")

    with patch.dict(
        globals_dict,
        {"resolve_query_engine_catalog": resolve_mock},
    ):
        assert settings.openmetadata_database() == "iceberg_dev"

    resolve_mock.assert_called_once_with("duckdb")


def test_openmetadata_service_type_prefers_explicit_value():
    """Explicit configured service type wins over capability resolution."""
    settings = OpenMetadataSettings(openmetadata_service_type="Postgres")

    with patch("phlo_openmetadata.settings.resolve_query_engine_service_type") as resolve_mock:
        assert settings.openmetadata_database_service_type() == "Postgres"

    resolve_mock.assert_not_called()


def test_openmetadata_service_type_uses_query_engine_capability():
    """Settings resolve the service type from the query engine capability."""
    settings = OpenMetadataSettings(
        openmetadata_service_type=None,
        openmetadata_query_engine="duckdb",
    )
    globals_dict = OpenMetadataSettings.openmetadata_database_service_type.__globals__
    resolve_mock = Mock(return_value="Trino")

    with patch.dict(
        globals_dict,
        {"resolve_query_engine_service_type": resolve_mock},
    ):
        assert settings.openmetadata_database_service_type() == "Trino"

    resolve_mock.assert_called_once_with("duckdb")

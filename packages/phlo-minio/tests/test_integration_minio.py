"""Integration tests for phlo-minio."""

import pytest

pytestmark = pytest.mark.integration


def test_minio_plugin_initializes():
    """Test that MinIO plugin can be instantiated."""
    from phlo_minio.plugin import MinioServicePlugin

    plugin = MinioServicePlugin()
    assert plugin is not None
    assert plugin.metadata.name == "minio"


def test_minio_service_definition():
    """Test that service definition can be loaded."""
    from phlo_minio.plugin import MinioServicePlugin

    plugin = MinioServicePlugin()
    service_def = plugin.service_definition

    assert isinstance(service_def, dict)


def test_minio_config_accessible():
    """Test MinIO configuration is accessible."""
    from phlo.config import get_settings

    settings = get_settings()
    assert hasattr(settings, "minio_endpoint") or hasattr(settings, "s3_endpoint")

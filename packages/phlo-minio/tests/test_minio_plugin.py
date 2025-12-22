"""Tests for MinIO service plugin."""

from phlo_minio.plugin import MinioServicePlugin


def test_minio_service_definition():
    plugin = MinioServicePlugin()
    service_definition = plugin.service_definition

    assert service_definition["name"] == "minio"
    assert service_definition["category"] == "core"

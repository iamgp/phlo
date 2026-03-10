"""Tests for MinIO service plugin."""

from phlo_minio.plugin import MinioResourceProvider, MinioServicePlugin


def test_minio_service_definition():
    """Validate MinIO service definition fields."""

    plugin = MinioServicePlugin()
    service_definition = plugin.service_definition

    assert service_definition["name"] == "minio"
    assert service_definition["category"] == "core"


def test_minio_resource_provider_exposes_object_store(monkeypatch) -> None:
    """MinIO should expose an object_store capability."""
    monkeypatch.setattr(
        "phlo_minio.plugin.MinioObjectStoreProvider.to_sling_connection",
        lambda _self: {
            "type": "s3",
            "endpoint": "http://minio:9000",
            "access_key_id": "minio",
            "secret_access_key": "secret",
            "region": "us-east-1",
        },
    )

    provider = MinioResourceProvider()

    object_stores = provider.get_object_stores()

    assert len(object_stores) == 1
    assert object_stores[0].name == "minio"
    assert object_stores[0].metadata["endpoint"] == "http://minio:9000"

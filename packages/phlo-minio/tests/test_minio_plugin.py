"""Tests for MinIO service plugin."""

from importlib import resources

from phlo_minio.plugin import MinioResourceProvider, MinioServicePlugin, MinioSetupServicePlugin


def test_minio_service_definition():
    """Validate MinIO service definition fields."""

    plugin = MinioServicePlugin()
    service_definition = plugin.service_definition

    assert service_definition["name"] == "minio"
    assert service_definition["category"] == "core"


def test_minio_service_uses_named_volume():
    """MinIO should not bind-mount a local data directory."""

    plugin = MinioServicePlugin()
    volumes = plugin.service_definition["compose"]["volumes"]

    assert "minio-data:/data" in volumes
    assert all("./volumes/minio" not in volume for volume in volumes)


def test_minio_services_build_pinned_phlo_images() -> None:
    """Server and client should build hardened Phlo-owned images from pinned source."""
    server = MinioServicePlugin().service_definition
    setup = MinioSetupServicePlugin().service_definition

    assert server["image"] == "ghcr.io/phlohouse/phlo-minio:7aac2a2c5b7c-xtext0.39.0"
    assert server["build"]["dockerfile"] == "minio/Dockerfile"
    assert setup["image"] == "ghcr.io/phlohouse/phlo-minio-mc:77f82e18b540-xtext0.39.0"
    assert setup["build"]["dockerfile"] == "minio-mc/Dockerfile"


def test_minio_server_image_includes_the_public_cli_runtime_client() -> None:
    """Release maintenance commands execute `mc` inside the MinIO server container."""
    dockerfile = resources.files("phlo_minio").joinpath("Dockerfile").read_text()

    assert "COPY --from=mc-build /out/mc /usr/bin/mc" in dockerfile


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

"""MinIO service plugin."""

from __future__ import annotations

from importlib import resources
from time import perf_counter
from typing import Any

import yaml

from phlo.capabilities import ObjectStoreSpec, ResourceSpec
from phlo.logging import get_logger
from phlo.plugins import PluginMetadata, ResourceProviderPlugin, ServicePlugin

logger = get_logger(__name__)


def _load_service_definition(resource_name: str, service_name: str) -> dict[str, Any]:
    start = perf_counter()
    logger.info(
        "minio_service_definition_load_started",
        service_name=service_name,
        resource_name=resource_name,
    )
    service_path = resources.files("phlo_minio").joinpath(resource_name)
    try:
        data = yaml.safe_load(service_path.read_text(encoding="utf-8"))
    except Exception:
        logger.error(
            "minio_service_definition_load_failed",
            service_name=service_name,
            resource_name=resource_name,
            elapsed_ms=round((perf_counter() - start) * 1000, 2),
            exc_info=True,
        )
        raise

    service_count = len(data.get("services", {})) if isinstance(data, dict) else None
    logger.info(
        "minio_service_definition_load_completed",
        service_name=service_name,
        resource_name=resource_name,
        elapsed_ms=round((perf_counter() - start) * 1000, 2),
        service_count=service_count,
    )
    return data


class MinioServicePlugin(ServicePlugin):
    """Service plugin for MinIO."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return metadata describing the MinIO service plugin.

        Returns:
            PluginMetadata: Plugin identity and display metadata.
        """
        return PluginMetadata(
            name="minio",
            version="0.1.0",
            description="S3-compatible object storage for data lake",
            author="Phlo Team",
            tags=["core", "storage", "s3"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load the MinIO service definition.

        Returns:
            dict[str, Any]: Parsed service configuration from YAML.
        """
        return _load_service_definition("service.yaml", "minio")


class MinioSetupServicePlugin(ServicePlugin):
    """Service plugin for MinIO bucket initialization."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return metadata describing the MinIO setup plugin.

        Returns:
            PluginMetadata: Plugin identity and display metadata.
        """
        return PluginMetadata(
            name="minio-setup",
            version="0.1.0",
            description="Initialize MinIO buckets for data lake",
            author="Phlo Team",
            tags=["core", "storage", "bootstrap"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load the MinIO setup service definition.

        Returns:
            dict[str, Any]: Parsed service configuration from YAML.
        """
        return _load_service_definition("minio-setup.yaml", "minio-setup")


class MinioObjectStoreProvider:
    """Capability provider for MinIO-backed object storage."""

    def to_sling_connection(self) -> dict[str, Any]:
        """Return a Sling-compatible S3 connection definition."""
        from phlo_minio.settings import get_settings

        settings = get_settings()
        return {
            "type": "s3",
            "endpoint": f"http://{settings.minio_endpoint()}",
            "access_key_id": settings.minio_root_user,
            "secret_access_key": settings.minio_root_password,
            "region": settings.s3_region,
        }


class MinioResourceProvider(ResourceProviderPlugin):
    """Resource provider plugin for MinIO capabilities."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the MinIO resource provider."""
        return PluginMetadata(
            name="minio",
            version="0.1.0",
            description="MinIO object-store capability for Phlo",
            tags=["core", "storage", "s3"],
        )

    def get_resources(self) -> list[ResourceSpec]:
        """Return resource specs exposed by this provider."""
        return []

    def get_object_stores(self) -> list[ObjectStoreSpec]:
        """Return object-store capability specs exposed by this provider."""
        provider = MinioObjectStoreProvider()
        return [
            ObjectStoreSpec(
                name="minio",
                provider=provider,
            metadata={"storage_system": "s3", "type": "s3", "endpoint": provider.to_sling_connection()["endpoint"]},
            )
        ]

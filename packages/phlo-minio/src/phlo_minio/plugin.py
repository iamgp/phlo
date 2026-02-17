"""MinIO service plugin."""

from __future__ import annotations

from importlib import resources
from time import perf_counter
from typing import Any

import yaml

from phlo.logging import get_logger
from phlo.plugins import PluginMetadata, ServicePlugin

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

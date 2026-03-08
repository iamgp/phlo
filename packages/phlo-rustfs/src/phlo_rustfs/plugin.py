"""RustFS service plugin."""

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
        "rustfs_service_definition_load_started",
        service_name=service_name,
        resource_name=resource_name,
    )
    service_path = resources.files("phlo_rustfs").joinpath(resource_name)
    try:
        data = yaml.safe_load(service_path.read_text(encoding="utf-8"))
    except Exception:
        logger.error(
            "rustfs_service_definition_load_failed",
            service_name=service_name,
            resource_name=resource_name,
            elapsed_ms=round((perf_counter() - start) * 1000, 2),
            exc_info=True,
        )
        raise

    service_count = len(data.get("services", {})) if isinstance(data, dict) else None
    logger.info(
        "rustfs_service_definition_load_completed",
        service_name=service_name,
        resource_name=resource_name,
        elapsed_ms=round((perf_counter() - start) * 1000, 2),
        service_count=service_count,
    )
    return data


class RustfsServicePlugin(ServicePlugin):
    """Service plugin for RustFS."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return metadata describing the RustFS service plugin."""
        return PluginMetadata(
            name="rustfs",
            version="0.1.0",
            description="S3-compatible object storage for data lake (RustFS)",
            author="Phlo Team",
            tags=["core", "storage", "s3"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load the RustFS service definition."""
        return _load_service_definition("service.yaml", "rustfs")


class RustfsSetupServicePlugin(ServicePlugin):
    """Service plugin for RustFS bucket initialization."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return metadata describing the RustFS setup plugin."""
        return PluginMetadata(
            name="rustfs-setup",
            version="0.1.0",
            description="Initialize RustFS buckets for data lake",
            author="Phlo Team",
            tags=["core", "storage", "bootstrap"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load the RustFS setup service definition."""
        return _load_service_definition("rustfs-setup.yaml", "rustfs-setup")

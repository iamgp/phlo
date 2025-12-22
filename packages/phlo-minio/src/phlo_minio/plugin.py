"""MinIO service plugin."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class MinioServicePlugin(ServicePlugin):
    """Service plugin for MinIO."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="minio",
            version="0.1.0",
            description="S3-compatible object storage for data lake",
            author="Phlo Team",
            tags=["core", "storage", "s3"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_minio").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))


class MinioSetupServicePlugin(ServicePlugin):
    """Service plugin for MinIO bucket initialization."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="minio-setup",
            version="0.1.0",
            description="Initialize MinIO buckets for data lake",
            author="Phlo Team",
            tags=["core", "storage", "bootstrap"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_minio").joinpath("minio-setup.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))

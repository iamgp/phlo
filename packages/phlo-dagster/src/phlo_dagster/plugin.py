"""Dagster service plugin."""

from __future__ import annotations

import yaml
from importlib import resources
from typing import Any

from phlo.plugins import PluginMetadata, ServicePlugin


class DagsterServicePlugin(ServicePlugin):
    """Service plugin for Dagster."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dagster",
            version="0.1.0",
            description="Data orchestration platform for workflows and pipelines",
            author="Phlo Team",
            tags=["orchestration", "core"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_dagster").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))


class DagsterDaemonServicePlugin(ServicePlugin):
    """Service plugin for Dagster daemon."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dagster-daemon",
            version="0.1.0",
            description="Dagster daemon for background scheduling and sensors",
            author="Phlo Team",
            tags=["orchestration", "core"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_dagster").joinpath("dagster-daemon.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))

"""Dagster service plugin."""

from __future__ import annotations

import yaml
from importlib import resources
from typing import Any

from phlo.logging import get_logger
from phlo.plugins import PluginMetadata, ServicePlugin

logger = get_logger(__name__)


def _load_service_definition(plugin_name: str, filename: str) -> dict[str, Any]:
    """Load a service definition YAML file from the phlo_dagster package.

    Args:
        plugin_name: Logical name for logging (e.g. "dagster", "dagster_daemon").
        filename: YAML filename inside the phlo_dagster package.

    Returns:
        Parsed service configuration dict.
    """
    service_path = resources.files("phlo_dagster").joinpath(filename)
    logger.info(
        "dagster_service_definition_load_started",
        plugin_name=plugin_name,
        service_definition_path=str(service_path),
    )
    try:
        definition = yaml.safe_load(service_path.read_text(encoding="utf-8"))
        logger.info(
            "dagster_service_definition_load_completed",
            plugin_name=plugin_name,
            service_definition_path=str(service_path),
        )
        return definition
    except Exception as exc:
        logger.error(
            "dagster_service_definition_load_failed",
            plugin_name=plugin_name,
            service_definition_path=str(service_path),
            error=str(exc),
            exc_info=True,
        )
        raise


class DagsterServicePlugin(ServicePlugin):
    """Service plugin for Dagster."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return metadata describing the Dagster service plugin.

        Returns:
            PluginMetadata: Plugin identity and display metadata.
        """
        return PluginMetadata(
            name="dagster",
            version="0.1.0",
            description="Data orchestration platform for workflows and pipelines",
            author="Phlo Team",
            tags=["orchestration", "core"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load the Dagster service definition.

        Returns:
            dict[str, Any]: Parsed service configuration from YAML.
        """
        return _load_service_definition("dagster", "service.yaml")


class DagsterDaemonServicePlugin(ServicePlugin):
    """Service plugin for Dagster daemon."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return metadata describing the Dagster daemon plugin.

        Returns:
            PluginMetadata: Plugin identity and display metadata.
        """
        return PluginMetadata(
            name="dagster-daemon",
            version="0.1.0",
            description="Dagster daemon for background scheduling and sensors",
            author="Phlo Team",
            tags=["orchestration", "core"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load the Dagster daemon service definition.

        Returns:
            dict[str, Any]: Parsed service configuration from YAML.
        """
        return _load_service_definition("dagster_daemon", "dagster-daemon.yaml")

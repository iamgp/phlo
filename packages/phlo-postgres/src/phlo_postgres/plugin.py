"""Postgres service plugin."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml
from phlo.capabilities import PublishTargetSpec, ResourceSpec
from phlo.plugins import PluginMetadata, ResourceProviderPlugin, ServicePlugin

from phlo_postgres.publish_target import PostgresPublishTarget
from phlo_postgres.resource import PostgresResource


class PostgresServicePlugin(ServicePlugin):
    """Service plugin for Postgres."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the Postgres service.

        Returns:
            PluginMetadata: Metadata describing the service plugin.
        """
        return PluginMetadata(
            name="postgres",
            version="0.1.0",
            description="PostgreSQL database for metadata and operational storage",
            author="Phlo Team",
            tags=["core", "database", "postgres"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load the Postgres service definition from package data.

        Returns:
            dict[str, Any]: Parsed Docker Compose service definition.
        """
        service_path = resources.files("phlo_postgres").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))


class PostgresExporterServicePlugin(ServicePlugin):
    """Service plugin for Postgres Prometheus exporter."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the Postgres exporter service.

        Returns:
            PluginMetadata: Metadata describing the exporter plugin.
        """
        return PluginMetadata(
            name="postgres-exporter",
            version="0.1.0",
            description="Prometheus exporter for PostgreSQL metrics",
            author="Phlo Team",
            tags=["observability", "metrics", "postgres"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load the Postgres exporter service definition from package data.

        Returns:
            dict[str, Any]: Parsed Docker Compose service definition.
        """
        service_path = resources.files("phlo_postgres").joinpath("exporter_service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))


class PostgresResourceProvider(ResourceProviderPlugin):
    """Resource provider plugin that exposes the Postgres resource."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the Postgres resource provider.

        Returns:
            PluginMetadata: Metadata describing the resource provider plugin.
        """
        return PluginMetadata(
            name="postgres",
            version="0.1.0",
            description="Postgres resource for Phlo",
        )

    def get_resources(self) -> list[ResourceSpec]:
        """Return resource specifications exposed by this provider.

        Returns:
            list[ResourceSpec]: Registered resource specifications.
        """
        return [ResourceSpec(name="postgres", resource=PostgresResource())]

    def get_publish_targets(self) -> list[PublishTargetSpec]:
        """Return publish target capability specs exposed by this provider."""
        return [
            PublishTargetSpec(
                name="postgres",
                provider=PostgresPublishTarget(),
                metadata={"target_system": "postgres", "role": "serving"},
            )
        ]

"""PostgreSQL service plugin implementations.

This module provides plugin implementations that integrate PostgreSQL with the
phlo plugin system. It includes service plugins for the PostgreSQL database,
Prometheus exporter, and volume setup, as well as a resource provider plugin
that exposes PostgreSQL capabilities to the rest of the system.

Example:
    >>> from phlo_postgres.plugin import PostgresServicePlugin
    >>> plugin = PostgresServicePlugin()
    >>> print(plugin.metadata.name)
    postgres
    >>> definition = plugin.service_definition

"""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml
from phlo.capabilities import PublishTargetSpec, ResourceSpec
from phlo.plugins import PluginMetadata, ResourceProviderPlugin, ServicePlugin

from phlo_postgres.publish_target import PostgresPublishTarget
from phlo_postgres.resource import PostgresResource


class PostgresServicePlugin(ServicePlugin):
    """Service plugin for managing PostgreSQL as a phlo service.

    This plugin provides the core PostgreSQL database service definition for
    docker-compose integration. It loads service configuration from package
    data (service.yaml) and exposes metadata for plugin discovery.

    Example:
        >>> plugin = PostgresServicePlugin()
        >>> metadata = plugin.metadata
        >>> print(f"Service: {metadata.name} v{metadata.version}")
        Service: postgres v0.1.0
        >>> definition = plugin.service_definition

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the PostgreSQL service.

        Returns:
            PluginMetadata: Metadata describing the service plugin including
                name, version, description, author, and tags for categorization.

        Example:
            >>> plugin = PostgresServicePlugin()
            >>> meta = plugin.metadata
            >>> print(meta.name)
            postgres
            >>> print(meta.tags)
            ['core', 'database', 'postgres']

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
        """Load the PostgreSQL service definition from package data.

        Reads and parses the service.yaml file from the package resources,
        returning a dictionary suitable for docker-compose configuration.

        Returns:
            dict[str, Any]: Parsed Docker Compose service definition as a
                dictionary with service configuration options.

        Raises:
            FileNotFoundError: If service.yaml is not found in package data.
            yaml.YAMLError: If the YAML file is malformed.

        Example:
            >>> plugin = PostgresServicePlugin()
            >>> definition = plugin.service_definition
            >>> print(definition.keys())
            dict_keys(['services', ...])

        """
        service_path = resources.files("phlo_postgres").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))


class PostgresExporterServicePlugin(ServicePlugin):
    """Service plugin for PostgreSQL Prometheus metrics exporter.

    This plugin provides a Prometheus exporter service that exposes PostgreSQL
    metrics for monitoring and alerting. It runs as a sidecar service alongside
    the main PostgreSQL container.

    Example:
        >>> plugin = PostgresExporterServicePlugin()
        >>> print(plugin.metadata.name)
        postgres-exporter

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the PostgreSQL exporter service.

        Returns:
            PluginMetadata: Metadata describing the exporter plugin.

        Example:
            >>> plugin = PostgresExporterServicePlugin()
            >>> meta = plugin.metadata
            >>> print(meta.description)
            Prometheus exporter for PostgreSQL metrics

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
        """Load the PostgreSQL exporter service definition from package data.

        Returns:
            dict[str, Any]: Parsed Docker Compose service definition for the
                Prometheus exporter sidecar container.

        Example:
            >>> plugin = PostgresExporterServicePlugin()
            >>> definition = plugin.service_definition

        """
        service_path = resources.files("phlo_postgres").joinpath("exporter_service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))


class PostgresVolumeSetupServicePlugin(ServicePlugin):
    """Service plugin for PostgreSQL data volume permission setup.

    This plugin provides an initialization service that ensures proper
    ownership and permissions on PostgreSQL data volumes before the main
    database container starts. This is particularly important for bind mounts
    on systems with strict permission requirements.

    Example:
        >>> plugin = PostgresVolumeSetupServicePlugin()
        >>> print(plugin.metadata.name)
        postgres-volume-setup

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the PostgreSQL volume setup service.

        Returns:
            PluginMetadata: Metadata describing the volume setup plugin.

        """
        return PluginMetadata(
            name="postgres-volume-setup",
            version="0.1.0",
            description="Initialize PostgreSQL data volume permissions",
            author="Phlo Team",
            tags=["core", "database", "postgres"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load the PostgreSQL volume setup service definition from package data.

        Returns:
            dict[str, Any]: Parsed Docker Compose service definition for the
                volume setup initialization container.

        """
        service_path = resources.files("phlo_postgres").joinpath("volume_setup.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))


class PostgresResourceProvider(ResourceProviderPlugin):
    """Resource provider plugin that exposes PostgreSQL capabilities.

    This plugin registers the PostgresResource and PostgresPublishTarget with
    the phlo resource system, making them available to other components for
    database operations and data publishing.

    Example:
        >>> provider = PostgresResourceProvider()
        >>> resources = provider.get_resources()
        >>> targets = provider.get_publish_targets()

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the PostgreSQL resource provider.

        Returns:
            PluginMetadata: Metadata describing the resource provider plugin.

        Example:
            >>> provider = PostgresResourceProvider()
            >>> meta = provider.metadata
            >>> print(meta.name)
            postgres

        """
        return PluginMetadata(
            name="postgres",
            version="0.1.0",
            description="Postgres resource for Phlo",
        )

    def get_resources(self) -> list[ResourceSpec]:
        """Return resource specifications exposed by this provider.

        Returns:
            list[ResourceSpec]: List of registered resource specifications
                that can be accessed by other phlo components.

        Example:
            >>> provider = PostgresResourceProvider()
            >>> specs = provider.get_resources()
            >>> print(specs[0].name)
            postgres

        """
        return [ResourceSpec(name="postgres", resource=PostgresResource())]

    def get_publish_targets(self) -> list[PublishTargetSpec]:
        """Return publish target capability specs exposed by this provider.

        Returns:
            list[PublishTargetSpec]: List of publish target specifications
                that define where data can be published to PostgreSQL.

        Example:
            >>> provider = PostgresResourceProvider()
            >>> targets = provider.get_publish_targets()
            >>> print(targets[0].name)
            postgres
            >>> print(targets[0].metadata)
            {'target_system': 'postgres', 'role': 'serving'}

        """
        return [
            PublishTargetSpec(
                name="postgres",
                provider=PostgresPublishTarget(),
                metadata={"target_system": "postgres", "role": "serving"},
            )
        ]

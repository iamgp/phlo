"""Grafana service plugin implementation.

This module provides the GrafanaServicePlugin class, which integrates Grafana
as a managed service within the Phlo platform. The plugin handles service
metadata registration, service definition loading, and lifecycle management.

The plugin loads its Docker Compose service configuration from a local YAML
file, allowing for consistent deployment across environments.

Example:
    >>> from phlo_grafana.plugin import GrafanaServicePlugin
    >>> plugin = GrafanaServicePlugin()
    >>> print(plugin.metadata.name)
    'grafana'
    >>> print(plugin.metadata.tags)
    ['observability', 'metrics', 'dashboards']

"""

from __future__ import annotations

from phlo.plugins import PackageYamlServicePlugin, PluginMetadata


class GrafanaServicePlugin(PackageYamlServicePlugin):
    """Service plugin for Grafana visualization and dashboards.

    This plugin registers Grafana as a managed service within the Phlo
    ecosystem, providing metrics visualization capabilities. It loads service
    configuration from a local YAML file and exposes metadata for service
    discovery and management.

    Attributes:
        None - This class uses property decorators for metadata and service
            definition access.

    Example:
        >>> plugin = GrafanaServicePlugin()
        >>> metadata = plugin.metadata
        >>> print(f"{metadata.name} v{metadata.version}")
        'grafana v0.1.0'
        >>> service_def = plugin.service_definition
        >>> print(service_def.get('services', {}).keys())

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for Grafana service registration.

        Provides essential metadata about the Grafana plugin including its
        name, version, description, author, and categorization tags for
        service discovery and management interfaces.

        Returns:
            PluginMetadata: A dataclass containing plugin metadata fields:
                - name (str): Plugin identifier ('grafana')
                - version (str): Semantic version ('0.1.0')
                - description (str): Human-readable description
                - author (str): Plugin maintainer ('Phlo Team')
                - tags (list[str]): Category tags for filtering

        Example:
            >>> plugin = GrafanaServicePlugin()
            >>> meta = plugin.metadata
            >>> assert "observability" in meta.tags
            >>> assert meta.name == "grafana"

        """
        return PluginMetadata(
            name="grafana",
            version="0.1.0",
            description="Metrics visualization and dashboards",
            author="Phlo Team",
            tags=["observability", "metrics", "dashboards"],
        )

"""Prometheus service plugin for Phlo.

This module provides a service plugin that integrates Prometheus monitoring
into the Phlo platform. It loads service definitions from YAML configuration
and exposes them through the standard Phlo plugin interface.

Example:
    Typical usage through the Phlo plugin registry::

        from phlo.plugins import get_plugin
        prometheus = get_plugin("prometheus")
        services = prometheus.service_definition

Attributes:
    logger: Module-level logger instance for structured logging.

"""

from __future__ import annotations

from phlo.plugins import PackageYamlServicePlugin, PluginMetadata


class PrometheusServicePlugin(PackageYamlServicePlugin):
    """Service plugin for Prometheus metrics collection and monitoring.

    This plugin provides Prometheus service configuration for Docker Compose
    deployment within the Phlo platform. It loads service definitions from
    embedded YAML resources and exposes them through the standard ServicePlugin
    interface.

    Attributes:
        _metadata: Cached plugin metadata instance.
        _service_definition: Cached service definition dictionary.

    Example:
        Load and inspect the Prometheus service configuration::

            plugin = PrometheusServicePlugin()
            meta = plugin.metadata
            print(f"{meta.name}: {meta.description}")
            definition = plugin.service_definition
            print(f"Services: {list(definition.get('services', {}).keys())}")

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the Prometheus service.

        Returns:
            PluginMetadata: Structured metadata including name, version,
                description, author, and tags for the Prometheus plugin.

        Example:
            >>> plugin = PrometheusServicePlugin()
            >>> meta = plugin.metadata
            >>> meta.name
            'prometheus'
            >>> 'observability' in meta.tags
            True

        """
        return PluginMetadata(
            name="prometheus",
            version="0.1.0",
            description="Metrics collection and monitoring",
            author="Phlo Team",
            tags=["observability", "metrics"],
        )

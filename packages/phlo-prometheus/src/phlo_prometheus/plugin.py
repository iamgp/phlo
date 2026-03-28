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

from importlib import resources
from time import perf_counter
from typing import Any

import yaml

from phlo.logging import get_logger
from phlo.plugins import PluginMetadata, ServicePlugin

logger = get_logger(__name__)


class PrometheusServicePlugin(ServicePlugin):
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

    @property
    def service_definition(self) -> dict[str, Any]:
        """Return the Docker service definition for Prometheus.

        Loads the service definition from the embedded service.yaml resource
        file. This includes container configuration, ports, volumes, and
        networking for the Prometheus metrics server.

        Performance metrics are logged for observability, including load time
        and service count.

        Returns:
            dict[str, Any]: Docker Compose service definition dictionary
                containing 'services', 'networks', 'volumes' as appropriate.

        Raises:
            FileNotFoundError: If the service.yaml resource is missing.
            yaml.YAMLError: If the service.yaml contains invalid YAML syntax.
            Exception: Any other error during resource loading or parsing.

        Example:
            >>> plugin = PrometheusServicePlugin()
            >>> definition = plugin.service_definition
            >>> 'services' in definition
            True
            >>> isinstance(definition.get('services'), dict)
            True

        """
        start = perf_counter()
        logger.info(
            "prometheus_service_definition_load_started",
            plugin_name="prometheus",
            resource_name="service.yaml",
        )
        service_path = resources.files("phlo_prometheus").joinpath("service.yaml")
        try:
            data = yaml.safe_load(service_path.read_text(encoding="utf-8"))
        except Exception:
            logger.error(
                "prometheus_service_definition_load_failed",
                plugin_name="prometheus",
                resource_name="service.yaml",
                elapsed_ms=round((perf_counter() - start) * 1000, 2),
                exc_info=True,
            )
            raise

        service_count = len(data.get("services", {})) if isinstance(data, dict) else None
        logger.info(
            "prometheus_service_definition_load_completed",
            plugin_name="prometheus",
            resource_name="service.yaml",
            elapsed_ms=round((perf_counter() - start) * 1000, 2),
            service_count=service_count,
        )
        return data

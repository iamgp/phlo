"""Prometheus service plugin."""

from __future__ import annotations

from importlib import resources
from time import perf_counter
from typing import Any

import yaml

from phlo.logging import get_logger
from phlo.plugins import PluginMetadata, ServicePlugin

logger = get_logger(__name__)


class PrometheusServicePlugin(ServicePlugin):
    """Service plugin for prometheus."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the Prometheus service."""
        return PluginMetadata(
            name="prometheus",
            version="0.1.0",
            description="Metrics collection and monitoring",
            author="Phlo Team",
            tags=["observability", "metrics"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Return the Docker service definition for Prometheus."""
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

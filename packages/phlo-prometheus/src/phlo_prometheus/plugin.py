"""Prometheus service plugin registration.

Builds the prometheus service plugin (observability and metrics tags) from
the shared service_plugin_class factory; no plugin-specific behavior is
defined here.
"""

from __future__ import annotations

from phlo.plugins import service_plugin_class


PrometheusServicePlugin = service_plugin_class(
    "PrometheusServicePlugin",
    name="prometheus",
    version="0.1.0",
    description="Metrics collection and monitoring",
    author="Phlo Team",
    tags=["observability", "metrics"],
)

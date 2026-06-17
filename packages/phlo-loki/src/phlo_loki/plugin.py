"""Loki service plugin registration."""

from __future__ import annotations

from phlo.plugins import service_plugin_class


LokiServicePlugin = service_plugin_class(
    "LokiServicePlugin",
    name="loki",
    version="0.1.0",
    description="Log aggregation and querying",
    author="Phlo Team",
    tags=["observability", "logs"],
)

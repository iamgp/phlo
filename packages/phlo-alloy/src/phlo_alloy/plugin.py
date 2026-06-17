"""Alloy service plugin registration."""

from __future__ import annotations

from phlo.plugins import service_plugin_class


AlloyServicePlugin = service_plugin_class(
    "AlloyServicePlugin",
    name="alloy",
    version="0.1.0",
    description="Grafana Alloy for log collection and shipping to Loki",
    author="Phlo Team",
    tags=["observability", "logs", "agent"],
)

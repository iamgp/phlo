"""Registers the Alloy service plugin.

Built declaratively via service_plugin_class(): the module declares plugin
metadata only, with no behaviour of its own.
"""

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

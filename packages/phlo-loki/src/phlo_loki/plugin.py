"""Registers the Loki service plugin.

Built declaratively via service_plugin_class(): the module declares plugin
metadata only, with no behaviour of its own.
"""

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

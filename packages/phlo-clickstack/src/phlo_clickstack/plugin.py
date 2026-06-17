"""Clickstack service plugin registration."""

from __future__ import annotations

from phlo.plugins import service_plugin_class


ClickStackServicePlugin = service_plugin_class(
    "ClickStackServicePlugin",
    name="clickstack",
    version="0.1.0",
    description="ClickStack all-in-one observability backend",
    author="Phlo Team",
    tags=["observability", "logs", "metrics", "traces"],
)

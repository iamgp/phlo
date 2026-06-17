"""Nessie service plugin registration."""

from __future__ import annotations

from phlo.plugins import service_plugin_class


NessieServicePlugin = service_plugin_class(
    "NessieServicePlugin",
    name="nessie",
    version="0.1.0",
    description="Git-like catalog for Iceberg tables with branch/merge support",
    author="Phlo Team",
    tags=["core", "catalog", "iceberg"],
)

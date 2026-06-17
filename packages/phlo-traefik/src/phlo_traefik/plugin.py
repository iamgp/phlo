"""Traefik service plugin registration."""

from __future__ import annotations

from phlo.plugins import service_plugin_class


TraefikServicePlugin = service_plugin_class(
    "TraefikServicePlugin",
    name="traefik",
    version="0.1.0",
    description="Local reverse proxy for named service URLs",
    author="Phlo Team",
    tags=["networking", "proxy", "traefik"],
)

"""Api service plugin registration."""

from __future__ import annotations

from phlo.plugins import service_plugin_class


PhloApiServicePlugin = service_plugin_class(
    "PhloApiServicePlugin",
    name="phlo-api",
    version="0.1.0",
    description="Backend API exposing Phlo internals to Observatory",
    author="Phlo Team",
    tags=["api", "observability"],
)

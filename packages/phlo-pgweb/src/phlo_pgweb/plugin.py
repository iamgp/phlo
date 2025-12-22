"""Pgweb service plugin."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class PgwebServicePlugin(ServicePlugin):
    """Service plugin for pgweb."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="pgweb",
            version="0.1.0",
            description="Web-based PostgreSQL database browser",
            author="Phlo Team",
            tags=['admin', 'postgres', 'ui'],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_pgweb").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))

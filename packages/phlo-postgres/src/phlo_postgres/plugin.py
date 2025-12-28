"""Postgres service plugin."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml
from phlo.plugins import PluginMetadata, ServicePlugin


class PostgresServicePlugin(ServicePlugin):
    """Service plugin for Postgres."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="postgres",
            version="0.1.0",
            description="PostgreSQL database for metadata and operational storage",
            author="Phlo Team",
            tags=["core", "database", "postgres"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_postgres").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))


class PostgresExporterServicePlugin(ServicePlugin):
    """Service plugin for Postgres Prometheus exporter."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="postgres-exporter",
            version="0.1.0",
            description="Prometheus exporter for PostgreSQL metrics",
            author="Phlo Team",
            tags=["observability", "metrics", "postgres"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        service_path = resources.files("phlo_postgres").joinpath("exporter_service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))

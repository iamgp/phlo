"""Postgrest service plugin registration."""

from __future__ import annotations

from phlo.plugins import service_plugin_class


PostgrestServicePlugin = service_plugin_class(
    "PostgrestServicePlugin",
    name="postgrest",
    version="0.1.0",
    description="RESTful API automatically generated from PostgreSQL schema",
    author="Phlo Team",
    tags=["api", "rest"],
)

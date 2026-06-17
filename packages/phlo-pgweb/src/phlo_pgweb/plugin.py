"""Pgweb service plugin registration."""

from __future__ import annotations

from phlo.plugins import service_plugin_class


PgwebServicePlugin = service_plugin_class(
    "PgwebServicePlugin",
    name="pgweb",
    version="0.1.0",
    description="Web-based PostgreSQL database browser",
    author="Phlo Team",
    tags=["admin", "postgres", "ui"],
)

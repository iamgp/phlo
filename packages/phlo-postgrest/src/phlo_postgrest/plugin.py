"""Postgrest service plugin registration.

Declares the schema-generated REST API as a service plugin. The class
object is created at import time via service_plugin_class so plugin
discovery can pick it up without instantiation.
"""

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

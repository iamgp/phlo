"""Dagster extension plugin for Trino resources."""

from __future__ import annotations

import dagster as dg

from phlo.plugins.base import DagsterExtensionPlugin, PluginMetadata
from phlo_trino.resource import TrinoResource


class TrinoDagsterPlugin(DagsterExtensionPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="trino",
            version="0.1.0",
            description="Trino resource for Dagster",
        )

    def get_definitions(self) -> dg.Definitions:
        return dg.Definitions(resources={"trino": TrinoResource()})

from __future__ import annotations

import dagster as dg
from phlo.plugins.base import DagsterExtensionPlugin, PluginMetadata

from phlo_dbt.assets import build_dbt_definitions


class DbtDagsterPlugin(DagsterExtensionPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dbt",
            version="0.1.0",
            description="dbt models as Dagster assets",
        )

    def get_definitions(self) -> dg.Definitions:
        return build_dbt_definitions()

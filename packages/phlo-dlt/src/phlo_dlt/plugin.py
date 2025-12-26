from __future__ import annotations

import dagster as dg
from phlo.plugins.base import DagsterExtensionPlugin, PluginMetadata

from phlo_dlt.decorator import (
    clear_ingestion_assets,
    get_ingestion_assets,
    phlo_ingestion,
)


class DltDagsterPlugin(DagsterExtensionPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dlt",
            version="0.1.0",
            description="DLT-based ingestion engine for Phlo",
        )

    def get_definitions(self) -> dg.Definitions:
        return dg.Definitions(assets=get_ingestion_assets())

    def get_exports(self) -> dict[str, object]:
        return {"ingestion": phlo_ingestion}

    def clear_registries(self) -> None:
        clear_ingestion_assets()

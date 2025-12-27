from __future__ import annotations

from typing import Any, Callable

from phlo.plugins.base import IngestionEnginePlugin, PluginMetadata

from phlo_dlt.decorator import (
    clear_ingestion_assets,
    get_ingestion_assets,
    phlo_ingestion,
)


class DltDagsterPlugin(IngestionEnginePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dlt",
            version="0.1.0",
            description="DLT-based ingestion engine for Phlo",
        )

    def get_ingestion_assets(self) -> list[Any]:
        return get_ingestion_assets()

    def get_ingestion_decorator(self) -> Callable[..., Any]:
        return phlo_ingestion

    def clear_registries(self) -> None:
        clear_ingestion_assets()

"""Observatory extension for Trino data explorer UI."""

from __future__ import annotations

from importlib import resources
from importlib.abc import Traversable

from phlo.plugins import PluginMetadata
from phlo.plugins.base import ObservatoryExtensionPlugin
from phlo.plugins.observatory import ObservatoryExtensionManifest


class TrinoObservatoryExtension(ObservatoryExtensionPlugin):
    """Observatory extension metadata for Trino data explorer UI."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="trino",
            version="0.1.0",
            description="Observatory UI extension for Trino data explorer",
        )

    @property
    def manifest(self) -> ObservatoryExtensionManifest:
        return ObservatoryExtensionManifest(
            name="trino",
            version="0.1.0",
            compat={"observatory_min": "0.1.0"},
            ui={
                "nav": [
                    {
                        "title": "Data Explorer",
                        "to": "/data",
                    }
                ]
            },
        )

    @property
    def asset_root(self) -> Traversable:
        return resources.files("phlo_trino").joinpath("observatory_assets")

"""Observatory extension for Loki logs UI."""

from __future__ import annotations

from importlib import resources
from importlib.abc import Traversable

from phlo.plugins import PluginMetadata
from phlo.plugins.base import ObservatoryExtensionPlugin
from phlo.plugins.observatory import ObservatoryExtensionManifest


class LokiObservatoryExtension(ObservatoryExtensionPlugin):
    """Observatory extension metadata for Loki logs UI."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="loki",
            version="0.1.0",
            description="Observatory UI extension for logs",
        )

    @property
    def manifest(self) -> ObservatoryExtensionManifest:
        return ObservatoryExtensionManifest(
            name="loki",
            version="0.1.0",
            compat={"observatory_min": "0.1.0"},
            ui={
                "nav": [
                    {
                        "title": "Logs",
                        "to": "/logs",
                    }
                ]
            },
        )

    @property
    def asset_root(self) -> Traversable:
        return resources.files("phlo_loki").joinpath("observatory_assets")

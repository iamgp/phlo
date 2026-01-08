"""Observatory extension for lineage graph UI."""

from __future__ import annotations

from importlib import resources

from phlo.plugins import PluginMetadata
from phlo.plugins.base import ObservatoryExtensionPlugin
from phlo.plugins.observatory import ObservatoryExtensionManifest


class LineageObservatoryExtension(ObservatoryExtensionPlugin):
    """Observatory extension metadata for lineage graph UI."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="lineage",
            version="0.1.0",
            description="Observatory UI extension for lineage graph",
        )

    @property
    def manifest(self) -> ObservatoryExtensionManifest:
        return ObservatoryExtensionManifest(
            name="lineage",
            version="0.1.0",
            compat={"observatory_min": "0.1.0"},
            ui={
                "nav": [
                    {
                        "title": "Lineage Graph",
                        "to": "/graph",
                    }
                ]
            },
        )

    @property
    def asset_root(self):
        return resources.files("phlo_lineage").joinpath("observatory_assets")

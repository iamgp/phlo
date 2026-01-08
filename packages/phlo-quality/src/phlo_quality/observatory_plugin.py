"""Observatory extension for quality UI."""

from __future__ import annotations

from importlib import resources

from phlo.plugins import PluginMetadata
from phlo.plugins.base import ObservatoryExtensionPlugin
from phlo.plugins.observatory import ObservatoryExtensionManifest


class QualityObservatoryExtension(ObservatoryExtensionPlugin):
    """Observatory extension metadata for Quality UI pages."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="quality",
            version="0.1.0",
            description="Observatory UI extension for data quality",
        )

    @property
    def manifest(self) -> ObservatoryExtensionManifest:
        return ObservatoryExtensionManifest(
            name="quality",
            version="0.1.0",
            compat={"observatory_min": "0.1.0"},
            ui={
                "nav": [
                    {
                        "title": "Quality",
                        "to": "/quality",
                    }
                ]
            },
        )

    @property
    def asset_root(self):
        return resources.files("phlo_quality").joinpath("observatory_assets")

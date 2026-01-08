"""Observatory extension for Dagster assets UI."""

from __future__ import annotations

from importlib import resources

from phlo.plugins import PluginMetadata
from phlo.plugins.base import ObservatoryExtensionPlugin
from phlo.plugins.observatory import ObservatoryExtensionManifest


class DagsterObservatoryExtension(ObservatoryExtensionPlugin):
    """Observatory extension metadata for Dagster assets UI."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dagster",
            version="0.1.0",
            description="Observatory UI extension for Dagster assets",
        )

    @property
    def manifest(self) -> ObservatoryExtensionManifest:
        return ObservatoryExtensionManifest(
            name="dagster",
            version="0.1.0",
            compat={"observatory_min": "0.1.0"},
            ui={
                "nav": [
                    {
                        "title": "Assets",
                        "to": "/assets",
                    }
                ]
            },
        )

    @property
    def asset_root(self):
        return resources.files("phlo_dagster").joinpath("observatory_assets")

"""Observatory extension for Nessie branches UI."""

from __future__ import annotations

from importlib import resources

from phlo.plugins import PluginMetadata
from phlo.plugins.base import ObservatoryExtensionPlugin
from phlo.plugins.observatory import ObservatoryExtensionManifest


class NessieObservatoryExtension(ObservatoryExtensionPlugin):
    """Observatory extension metadata for Nessie branches UI."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="nessie",
            version="0.1.0",
            description="Observatory UI extension for Nessie branches",
        )

    @property
    def manifest(self) -> ObservatoryExtensionManifest:
        return ObservatoryExtensionManifest(
            name="nessie",
            version="0.1.0",
            compat={"observatory_min": "0.1.0"},
            ui={
                "nav": [
                    {
                        "title": "Branches",
                        "to": "/branches",
                    }
                ]
            },
        )

    @property
    def asset_root(self):
        return resources.files("phlo_nessie").joinpath("observatory_assets")

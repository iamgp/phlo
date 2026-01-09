"""Observatory extension for Nessie branches UI."""

from __future__ import annotations

from importlib import resources
from importlib.abc import Traversable

from phlo.plugins import PluginMetadata
from phlo.plugins.base import ObservatoryExtensionPlugin
from phlo.plugins.observatory import (
    ObservatoryExtensionCompatibility,
    ObservatoryExtensionManifest,
    ObservatoryExtensionNavItem,
    ObservatoryExtensionUI,
)


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
            compat=ObservatoryExtensionCompatibility(observatory_min="0.1.0"),
            ui=ObservatoryExtensionUI(
                nav=[ObservatoryExtensionNavItem(title="Branches", to="/branches")]
            ),
        )

    @property
    def asset_root(self) -> Traversable:
        return resources.files("phlo_nessie").joinpath("observatory_assets")

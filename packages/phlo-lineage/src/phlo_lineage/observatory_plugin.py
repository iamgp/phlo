"""Observatory extension for lineage graph UI."""

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
            compat=ObservatoryExtensionCompatibility(observatory_min="0.1.0"),
            ui=ObservatoryExtensionUI(
                nav=[ObservatoryExtensionNavItem(title="Lineage Graph", to="/graph")]
            ),
        )

    @property
    def asset_root(self) -> Traversable:
        return resources.files("phlo_lineage").joinpath("observatory_assets")

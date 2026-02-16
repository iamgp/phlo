"""Observatory extension for lineage graph UI."""

from __future__ import annotations

from importlib import resources
from importlib.abc import Traversable

from phlo.plugins import PluginMetadata
from phlo_observatory import ObservatoryExtensionPlugin
from phlo_observatory.manifest import (
    ObservatoryExtensionCompatibility,
    ObservatoryExtensionManifest,
    ObservatoryExtensionNavItem,
    ObservatoryExtensionUI,
)


class LineageObservatoryExtension(ObservatoryExtensionPlugin):
    """Observatory extension metadata for lineage graph UI."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for extension discovery.

        Returns:
            PluginMetadata: Extension identity and description.
        """
        return PluginMetadata(
            name="lineage",
            version="0.1.0",
            description="Observatory UI extension for lineage graph",
        )

    @property
    def manifest(self) -> ObservatoryExtensionManifest:
        """Return Observatory extension manifest configuration.

        Returns:
            ObservatoryExtensionManifest: UI navigation and compatibility settings.
        """
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
        """Return the static asset directory for the extension.

        Returns:
            Traversable: Package path to bundled Observatory assets.
        """
        return resources.files("phlo_lineage").joinpath("observatory_assets")

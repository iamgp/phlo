"""Observatory extension for Loki logs UI."""

from __future__ import annotations

from importlib import resources
from importlib.abc import Traversable

from phlo.plugins import PluginMetadata
from phlo.plugins.observatory import (
    ObservatoryExtensionCompatibility,
    ObservatoryExtensionManifest,
    ObservatoryExtensionNavItem,
    ObservatoryExtensionPlugin,
    ObservatoryExtensionUI,
)


class LokiObservatoryExtension(ObservatoryExtensionPlugin):
    """Observatory extension metadata for Loki logs UI."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin identity metadata for discovery.

        Returns:
            Plugin metadata for the Loki observatory extension.
        """
        return PluginMetadata(
            name="loki",
            version="0.1.0",
            description="Observatory UI extension for logs",
        )

    @property
    def manifest(self) -> ObservatoryExtensionManifest:
        """Return extension manifest for Observatory navigation and compatibility.

        Returns:
            Extension manifest for the Loki logs UI.
        """
        return ObservatoryExtensionManifest(
            name="loki",
            version="0.1.0",
            compat=ObservatoryExtensionCompatibility(observatory_min="0.1.0"),
            ui=ObservatoryExtensionUI(nav=[ObservatoryExtensionNavItem(title="Logs", to="/logs")]),
        )

    @property
    def asset_root(self) -> Traversable:
        """Return package path to static observatory extension assets.

        Returns:
            Traversable root containing bundled UI assets.
        """
        return resources.files("phlo_loki").joinpath("observatory_assets")

"""Observatory extension for quality UI."""

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


class PanderaObservatoryExtension(ObservatoryExtensionPlugin):
    """Observatory extension metadata for Quality UI pages."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the quality observatory extension.

        Returns:
            PluginMetadata: Metadata used during plugin registration.
        """
        return PluginMetadata(
            name="quality",
            version="0.1.0",
            description="Observatory UI extension for data quality",
        )

    @property
    def manifest(self) -> ObservatoryExtensionManifest:
        """Build the observatory extension manifest for quality navigation.

        Returns:
            ObservatoryExtensionManifest: Extension manifest consumed by observatory.
        """
        return ObservatoryExtensionManifest(
            name="quality",
            version="0.1.0",
            compat=ObservatoryExtensionCompatibility(observatory_min="0.1.0"),
            ui=ObservatoryExtensionUI(
                nav=[ObservatoryExtensionNavItem(title="Quality", to="/extensions/quality")]
            ),
        )

    @property
    def asset_root(self) -> Traversable:
        """Return the packaged root directory for extension static assets.

        Returns:
            Traversable: Filesystem-like handle to the observatory asset directory.
        """
        return resources.files("phlo_pandera").joinpath("observatory_assets")

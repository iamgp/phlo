"""Observatory extension for Trino data explorer UI.

This module provides an Observatory extension plugin for integrating
Trino data exploration capabilities into the Phlo Observatory web UI.

Classes:
    TrinoObservatoryExtension: Extension for Trino data explorer.

Constants:
    VERSION: Extension version string.

Example:
    The plugin is automatically discovered and loaded by Observatory:
    >>> from phlo_trino.observatory_plugin import TrinoObservatoryExtension
    >>> ext = TrinoObservatoryExtension()
    >>> print(ext.manifest.name)
    trino


Loaded through the Observatory extension entry points at UI startup rather
than imported directly by other phlo modules.
"""

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

VERSION = "0.1.0"


class TrinoObservatoryExtension(ObservatoryExtensionPlugin):
    """Observatory extension metadata for Trino data explorer UI."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for Trino observatory integration.

        Returns:
            PluginMetadata: Plugin identity, version, and description.

        """
        return PluginMetadata(
            name="trino",
            version=VERSION,
            description="Observatory UI extension for Trino data explorer",
        )

    @property
    def manifest(self) -> ObservatoryExtensionManifest:
        """Return the observatory extension manifest for Trino.

        Returns:
            ObservatoryExtensionManifest: Manifest defining UI navigation and compatibility.

        """
        return ObservatoryExtensionManifest(
            name="trino",
            version=VERSION,
            compat=ObservatoryExtensionCompatibility(observatory_min="0.1.0"),
            ui=ObservatoryExtensionUI(
                nav=[ObservatoryExtensionNavItem(title="Data Explorer", to="/extensions/trino")]
            ),
        )

    @property
    def asset_root(self) -> Traversable:
        """Return the root directory containing extension frontend assets.

        Returns:
            Traversable: Package resource path for observatory static assets.

        """
        return resources.files("phlo_trino").joinpath("observatory_assets")

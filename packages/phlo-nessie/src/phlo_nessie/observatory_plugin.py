"""Observatory extension for Nessie branches UI.

This module provides an Observatory UI extension that adds a "Branches" view
to the Phlo observatory interface, allowing users to browse and manage Nessie
branches through a web UI.

The extension serves static assets from the package and registers navigation
items for the branches management page.

Example:
    >>> from phlo_nessie.observatory_plugin import NessieObservatoryExtension
    >>> plugin = NessieObservatoryExtension()
    >>> manifest = plugin.manifest

Classes:
    NessieObservatoryExtension: Observatory extension for Nessie branches UI.

Attributes:
    VERSION: Extension version string.

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


class NessieObservatoryExtension(ObservatoryExtensionPlugin):
    """Observatory extension metadata for Nessie branches UI."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for Nessie observatory integration.

        Returns:
            PluginMetadata: Plugin identity, version, and description.

        """
        return PluginMetadata(
            name="nessie",
            version=VERSION,
            description="Observatory UI extension for Nessie branches",
        )

    @property
    def manifest(self) -> ObservatoryExtensionManifest:
        """Return the observatory extension manifest for Nessie.

        Returns:
            ObservatoryExtensionManifest: Manifest defining UI navigation and compatibility.

        """
        return ObservatoryExtensionManifest(
            name="nessie",
            version=VERSION,
            compat=ObservatoryExtensionCompatibility(observatory_min="0.1.0"),
            ui=ObservatoryExtensionUI(
                nav=[ObservatoryExtensionNavItem(title="Branches", to="/branches")]
            ),
        )

    @property
    def asset_root(self) -> Traversable:
        """Return the root directory containing extension frontend assets.

        Returns:
            Traversable: Package resource path for observatory static assets.

        """
        return resources.files("phlo_nessie").joinpath("observatory_assets")

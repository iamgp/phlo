"""Observatory extension for Dagster assets UI.

This module provides an ObservatoryExtensionPlugin that exposes Dagster
asset information to Phlo's Observatory web UI. It registers the extension
with the Observatory plugin system and provides static assets for the
Dagster assets view.

Observatory Integration:
    The DagsterObservatoryExtension implements the ObservatoryExtensionPlugin
    interface to contribute:
    - Extension metadata (name, version, compatibility)
    - Navigation items for the Observatory UI
    - Static assets (HTML, JS, CSS) for the assets view

Extension Points:
    - metadata: Plugin identity for discovery
    - manifest: Extension manifest with navigation and compatibility
    - asset_root: Package path to bundled UI assets

UI Assets:
    Static assets are bundled in the package under observatory_assets/ and
    served through the Observatory's static file handling.

Navigation:
    The extension adds an "Assets" navigation item linking to /assets view
    that renders the Dagster assets UI.

Example:
    Extension registration via entry_points::

        [phlo.plugins.observatory]
        dagster = phlo_dagster.observatory_plugin:DagsterObservatoryExtension

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


class DagsterObservatoryExtension(ObservatoryExtensionPlugin):
    """Observatory extension metadata for Dagster assets UI."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin identity metadata for discovery.

        Returns:
            Plugin metadata for the Dagster observatory extension.

        """
        return PluginMetadata(
            name="dagster",
            version="0.1.0",
            description="Observatory UI extension for Dagster assets",
        )

    @property
    def manifest(self) -> ObservatoryExtensionManifest:
        """Return extension manifest for Observatory navigation and compatibility.

        Returns:
            Extension manifest for the Dagster assets UI.

        """
        return ObservatoryExtensionManifest(
            name="dagster",
            version="0.1.0",
            compat=ObservatoryExtensionCompatibility(observatory_min="0.1.0"),
            ui=ObservatoryExtensionUI(
                nav=[ObservatoryExtensionNavItem(title="Assets", to="/assets")]
            ),
        )

    @property
    def asset_root(self) -> Traversable:
        """Return package path to static observatory extension assets.

        Returns:
            Traversable root containing bundled UI assets.

        """
        return resources.files("phlo_dagster").joinpath("observatory_assets")

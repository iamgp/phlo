"""Observatory extension plugin for lineage graph UI.

This module provides the LineageObservatoryExtension class, which integrates
the phlo-lineage visualization features into the Observatory web UI. It registers
the lineage graph view as a navigation item and serves static assets.

Extension Features:
    - Lineage Graph navigation item in Observatory UI
    - Static assets for lineage visualization (JS, CSS, images)
    - Compatibility checking with Observatory core version

Plugin Registration:
    This extension is auto-discovered via entry points. The Observatory framework
    loads and initializes it automatically.

Asset Structure:
    Static assets are bundled in the package at:
        phlo_lineage/observatory_assets/

Example:
    Once loaded, users can navigate to /graph in Observatory to view:
    - Interactive lineage graph visualization
    - Asset dependency relationships
    - Column-level lineage details

See Also:
    phlo.plugins.observatory for the extension plugin interface.
    phlo_lineage.graph for graph construction logic.

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


class LineageObservatoryExtension(ObservatoryExtensionPlugin):
    """Observatory extension metadata for lineage graph UI."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for extension discovery.

                Provides identifying information for the Observatory plugin system
        to recognize and load this extension.

        Returns:
                    PluginMetadata with extension identity:
                        - name: "lineage"
                        - version: "0.1.0"
                        - description: Brief description of the extension

                Discovery:
                    This metadata is used by the Observatory plugin loader to:
                    - Identify the extension uniquely
                    - Display extension information in the UI
                    - Check for duplicate or conflicting extensions

        Example:
                    >>> ext = LineageObservatoryExtension()
                    >>> meta = ext.metadata
                    >>> print(f"Extension: {meta.name} v{meta.version}")
                    Extension: lineage v0.1.0

        """
        return PluginMetadata(
            name="lineage",
            version="0.1.0",
            description="Observatory UI extension for lineage graph",
        )

    @property
    def manifest(self) -> ObservatoryExtensionManifest:
        """Return Observatory extension manifest configuration.

                Defines the extension's UI integration points, version compatibility
        requirements, and navigation structure within Observatory.

        Returns:
                    ObservatoryExtensionManifest containing:
                        - name: Extension identifier
                        - version: Extension version
                        - compat: Compatibility requirements (observatory_min version)
                        - ui: UI configuration including navigation items

                Manifest Contents:
                    - name: "lineage" (must match metadata.name)
                    - version: "0.1.0"
                    - compat.observatory_min: "0.1.0" (minimum Observatory version)
                    - ui.nav: [NavItem(title="Lineage Graph", to="/graph")]

                Compatibility:
                    The extension requires Observatory core version >= 0.1.0.
                    Loading in incompatible versions will raise a warning.

        Example:
                    >>> ext = LineageObservatoryExtension()
                    >>> manifest = ext.manifest
                    >>> print(f"Requires Observatory >= {manifest.compat.observatory_min}")
                    >>> for item in manifest.ui.nav:
                    ...     print(f"Nav: {item.title} -> {item.to}")

        See Also:
                    ObservatoryExtensionManifest for full manifest schema.

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

                Provides access to bundled static assets (JavaScript, CSS, images)
        that are served by the Observatory web server for the lineage UI.

        Returns:
                    Traversable pointing to the package directory containing
                    static assets at: phlo_lineage/observatory_assets/

                Asset Types:
                    The directory typically contains:
                    - JavaScript files for interactive lineage graph visualization
                    - CSS stylesheets for lineage-specific styling
                    - Image assets for icons and visual elements
                    - HTML templates for the lineage graph view

                Serving:
                    Observatory serves these assets at a URL path derived from
                    the extension name (e.g., /extensions/lineage/assets/).

        Example:
                    >>> ext = LineageObservatoryExtension()
                    >>> assets = ext.asset_root
                    >>> # List asset files
                    >>> for path in assets.iterdir():
                    ...     print(f"Asset: {path.name}")

        Note:
                    Uses importlib.resources for safe package resource access.
                    Works correctly in both development and installed (wheel) contexts.

        """
        return resources.files("phlo_lineage").joinpath("observatory_assets")

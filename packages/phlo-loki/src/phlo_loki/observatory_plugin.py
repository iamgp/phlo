"""Observatory extension for Loki logs UI.

This module provides the LokiObservatoryExtension class which integrates
Loki log viewing capabilities into the Phlo Observatory web interface. It
registers a navigation item for accessing logs and serves static UI assets.

Example:
    The extension is auto-discovered by the Observatory::

        from phlo.plugins import load_plugin
        extension = load_plugin("phlo_loki.observatory")

Attributes:
    LokiObservatoryExtension: Observatory extension class for log visualization.

Loaded through the phlo plugin entry-point mechanism at startup rather than imported directly;
the Observatory auto-discovers this extension via phlo.plugins.
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


class LokiObservatoryExtension(ObservatoryExtensionPlugin):
    """Observatory extension for Loki log aggregation UI.

    This extension integrates Loki log viewing capabilities into the Phlo
    Observatory web interface. It provides navigation to the logs view and
    serves bundled static assets for the log UI components.

    Attributes:
        None - Properties are computed dynamically.

    Example:
        Extension is instantiated by the discovery system::

            extension = LokiObservatoryExtension()
            manifest = extension.manifest
            nav_items = manifest.ui.nav

    """

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

"""Observatory extension for Dagster assets UI."""

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

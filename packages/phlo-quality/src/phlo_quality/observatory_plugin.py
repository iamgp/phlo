"""Observatory extension for quality UI."""

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


class QualityObservatoryExtension(ObservatoryExtensionPlugin):
    """Observatory extension metadata for Quality UI pages."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="quality",
            version="0.1.0",
            description="Observatory UI extension for data quality",
        )

    @property
    def manifest(self) -> ObservatoryExtensionManifest:
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
        return resources.files("phlo_quality").joinpath("observatory_assets")

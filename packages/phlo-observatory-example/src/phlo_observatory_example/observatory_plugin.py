"""Example Observatory extension plugin."""

from __future__ import annotations

from importlib import resources
from importlib.abc import Traversable

from phlo.plugins import PluginMetadata
from phlo.plugins.base import ObservatoryExtensionPlugin
from phlo.plugins.observatory import (
    ObservatoryExtensionCompatibility,
    ObservatoryExtensionManifest,
    ObservatoryExtensionNavItem,
    ObservatoryExtensionRoute,
    ObservatoryExtensionSettings,
    ObservatoryExtensionSettingsPanel,
    ObservatoryExtensionSlot,
    ObservatoryExtensionUI,
)


class ExampleObservatoryExtension(ObservatoryExtensionPlugin):
    """Example Observatory extension showing routes, slots, and settings panels."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="example",
            version="0.1.0",
            description="Example Observatory UI extension",
        )

    @property
    def manifest(self) -> ObservatoryExtensionManifest:
        return ObservatoryExtensionManifest(
            name="example",
            version="0.1.0",
            compat=ObservatoryExtensionCompatibility(observatory_min="0.1.0"),
            settings=ObservatoryExtensionSettings(
                schema={
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "message": {"type": "string"},
                    },
                },
                defaults={"enabled": True, "message": "Hello from extension settings."},
                scope="extension",
            ),
            ui=ObservatoryExtensionUI(
                routes=[
                    ObservatoryExtensionRoute(
                        path="/extensions/example",
                        module="/example.js",
                        export="registerRoutes",
                    )
                ],
                nav=[ObservatoryExtensionNavItem(title="Example", to="/extensions/example")],
                slots=[
                    ObservatoryExtensionSlot(
                        slot_id="dashboard.after-cards",
                        module="/example.js",
                        export="registerDashboardSlot",
                    ),
                    ObservatoryExtensionSlot(
                        slot_id="hub.after-stats",
                        module="/example.js",
                        export="registerHubSlot",
                    ),
                ],
                settings=[
                    ObservatoryExtensionSettingsPanel(
                        module="/example.js", export="registerSettings"
                    )
                ],
            ),
        )

    @property
    def asset_root(self) -> Traversable:
        return resources.files("phlo_observatory_example").joinpath("observatory_assets")

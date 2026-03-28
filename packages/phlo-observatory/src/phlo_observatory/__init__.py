"""Observatory UI plugin package."""

from phlo.plugins.observatory import (
    ObservatoryExtensionCompatibility,
    ObservatoryExtensionManifest,
    ObservatoryExtensionNavItem,
    ObservatoryExtensionPlugin,
    ObservatoryExtensionRoute,
    ObservatoryExtensionSettings,
    ObservatoryExtensionSettingsPanel,
    ObservatoryExtensionSlot,
    ObservatoryExtensionUI,
    discover_observatory_extensions,
    get_observatory_extension,
)
from phlo.plugins.observatory_settings import (
    SettingsRecord,
    SettingsScope,
    SettingsService,
    get_settings_service,
)
from phlo_observatory.plugin import ObservatoryServicePlugin
from phlo_observatory.settings import ObservatorySettings, get_settings

__all__ = [
    "ObservatoryExtensionCompatibility",
    "ObservatoryExtensionManifest",
    "ObservatoryExtensionNavItem",
    "ObservatoryExtensionPlugin",
    "ObservatoryExtensionRoute",
    "ObservatoryExtensionSettings",
    "ObservatoryExtensionSettingsPanel",
    "ObservatoryExtensionSlot",
    "ObservatoryExtensionUI",
    "ObservatoryServicePlugin",
    "ObservatorySettings",
    "SettingsRecord",
    "SettingsScope",
    "SettingsService",
    "discover_observatory_extensions",
    "get_observatory_extension",
    "get_settings",
    "get_settings_service",
]
__version__ = "0.2.4"

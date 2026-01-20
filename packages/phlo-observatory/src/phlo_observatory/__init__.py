"""Observatory UI plugin package."""

from phlo_observatory.manifest import ObservatoryExtensionManifest
from phlo_observatory.observatory_ext import ObservatoryExtensionPlugin
from phlo_observatory.plugin import ObservatoryServicePlugin
from phlo_observatory.settings import ObservatorySettings, get_settings
from phlo_observatory.settings_service import (
    SettingsRecord,
    SettingsScope,
    SettingsService,
    get_settings_service,
)

__all__ = [
    "ObservatoryExtensionManifest",
    "ObservatoryExtensionPlugin",
    "ObservatoryServicePlugin",
    "ObservatorySettings",
    "SettingsRecord",
    "SettingsScope",
    "SettingsService",
    "get_settings",
    "get_settings_service",
]
__version__ = "0.1.0"

"""Backward-compatible re-exports for Observatory settings storage."""

from phlo.plugins.observatory_settings import (
    InMemorySettingsService,
    SettingsRecord,
    SettingsScope,
    SettingsService,
    get_settings_service,
)

__all__ = [
    "InMemorySettingsService",
    "SettingsRecord",
    "SettingsScope",
    "SettingsService",
    "get_settings_service",
]

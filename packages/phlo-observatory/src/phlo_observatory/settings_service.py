"""Observatory settings storage backend (backward-compatible re-exports).

This module provides backward-compatible access to the settings storage
infrastructure used by the Observatory UI for persisting user preferences,
configuration, and extension settings.

The settings system supports:
    - In-memory storage for development and testing
    - PostgreSQL-backed persistent storage for production
    - Scoped settings (global, user, project)
    - Type-safe settings records with validation

Backward Compatibility:
    These exports are maintained for existing code. New implementations should
    import directly from phlo.plugins.observatory_settings.

Exported Classes:
    - SettingsService: Abstract base for settings storage backends
    - InMemorySettingsService: Non-persistent in-memory implementation
    - SettingsRecord: Individual setting with metadata
    - SettingsScope: Enumeration of setting scopes (global, user, project)
    - get_settings_service: Factory function for settings service instances

Example:
    >>> from phlo_observatory.settings_service import get_settings_service
    >>> service = get_settings_service()
    >>> service.set('theme', 'dark', scope=SettingsScope.USER)

See Also:
    phlo.plugins.observatory_settings: Source of truth for settings API.
    phlo_observatory.settings: Observatory-specific configuration.

"""

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

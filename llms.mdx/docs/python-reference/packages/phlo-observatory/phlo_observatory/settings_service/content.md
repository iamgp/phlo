# settings_service (/docs/python-reference/packages/phlo-observatory/phlo_observatory/settings_service)



Observatory settings storage backend (backward-compatible re-exports).

This module provides backward-compatible access to the settings storage
infrastructure used by the Observatory UI for persisting user preferences,
configuration, and extension settings.

The settings system supports:

* In-memory storage for development and testing
* PostgreSQL-backed persistent storage for production
* Scoped settings (global, user, project)
* Type-safe settings records with validation

Backward Compatibility:
These exports are maintained for existing code. New implementations should
import directly from phlo.plugins.observatory\_settings.

Exported Classes:

* SettingsService: Abstract base for settings storage backends
* InMemorySettingsService: Non-persistent in-memory implementation
* SettingsRecord: Individual setting with metadata
* SettingsScope: Enumeration of setting scopes (global, user, project)
* get\_settings\_service: Factory function for settings service instances

Example:

> > > from phlo\_observatory.settings\_service import get\_settings\_service
> > > service = get\_settings\_service()
> > > service.set('theme', 'dark', scope=SettingsScope.USER)

See Also:
phlo.plugins.observatory\_settings: Source of truth for settings API.
phlo\_observatory.settings: Observatory-specific configuration.

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['InMemorySettingsService', 'SettingsRecord', 'SettingsScope', 'SettingsService', 'get_settings_service']&#x22;" />

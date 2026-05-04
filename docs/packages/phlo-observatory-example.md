# phlo-observatory-example

Example Observatory extension plugin for Phlo.

## Overview

This package demonstrates how to build a custom Observatory UI extension that integrates with the Phlo data platform. It provides example implementations of routes, navigation items, dashboard slots, and settings panels.

## Purpose

The `phlo-observatory-example` package serves as:

1. **Reference Implementation** - Shows best practices for building Observatory extensions
2. **Starting Template** - Can be forked to create custom extensions
3. **Testing Aid** - Used for testing the Observatory extension system
4. **Documentation** - Living documentation of the extension API

## Installation

```bash
pip install phlo-observatory-example
```

Or with the full Phlo distribution:

```bash
pip install phlo[defaults]
```

## Features

### Custom Routes

The extension registers a dedicated route at `/extensions/example`:

```python
from phlo.plugins.observatory import (
    ObservatoryExtensionPlugin,
    ObservatoryExtensionManifest,
    ObservatoryExtensionUI,
    ObservatoryExtensionRoute,
)

class ExampleObservatoryExtension(ObservatoryExtensionPlugin):
    @property
    def manifest(self) -> ObservatoryExtensionManifest:
        return ObservatoryExtensionManifest(
            name="example",
            version="0.1.0",
            ui=ObservatoryExtensionUI(
                routes=[
                    ObservatoryExtensionRoute(
                        path="/extensions/example",
                        module="/example.js",
                        export="registerRoutes",
                    )
                ],
            ),
        )
```

### Navigation Items

Adds a custom menu item to the Observatory sidebar:

```python
ui=ObservatoryExtensionUI(
    nav=[
        ObservatoryExtensionNavItem(
            title="Example",
            to="/extensions/example"
        )
    ],
)
```

### Dashboard Slots

Provides widgets for dashboard integration:

```python
ui=ObservatoryExtensionUI(
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
)
```

### Settings Panel

Adds configuration UI to Observatory settings:

```python
manifest = ObservatoryExtensionManifest(
    settings=ObservatoryExtensionSettings(
        settings_schema={
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
        settings=[
            ObservatoryExtensionSettingsPanel(
                module="/example.js",
                export="registerSettings"
            )
        ],
    ),
)
```

## Extension API

### ObservatoryExtensionPlugin Base Class

All extensions must inherit from `ObservatoryExtensionPlugin`:

```python
from phlo.plugins.observatory import ObservatoryExtensionPlugin, PluginMetadata

class MyExtension(ObservatoryExtensionPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my-extension",
            version="1.0.0",
            description="My custom Observatory extension",
        )

    @property
    def manifest(self) -> ObservatoryExtensionManifest:
        return ObservatoryExtensionManifest(...)
```

### Required Properties

Every extension must implement:

- `metadata` - Plugin identification and version (PluginMetadata)
- `manifest` - Full extension configuration (ObservatoryExtensionManifest)
- `asset_root` - Path to static assets (Traversable)

### Manifest Structure

The manifest defines all UI integrations:

```python
ObservatoryExtensionManifest(
    name="example",                           # Extension identifier
    version="0.1.0",                          # Extension version
    compat=ObservatoryExtensionCompatibility( # Compatibility requirements
        observatory_min="0.1.0"
    ),
    settings=ObservatoryExtensionSettings(    # Configuration schema
        settings_schema={...},                # JSON schema for settings
        defaults={...},                       # Default values
        scope="extension",                    # Settings scope
    ),
    ui=ObservatoryExtensionUI(                # UI configuration
        routes=[...],                         # Frontend routes
        nav=[...],                            # Navigation items
        slots=[...],                          # Dashboard widgets
        settings=[...],                       # Settings panels
    ),
)
```

## Development

### Local Testing

1. Install in development mode:

```bash
cd /path/to/phlo-observatory-example
pip install -e .
```

2. Start Phlo services:

```bash
phlo services start
```

3. Open Observatory and navigate to the Example Dashboard at `/extensions/example`

### Creating a Custom Extension

Fork this package to create your own extension:

1. Copy the package structure:
```
my-extension/
├── pyproject.toml
└── src/
    └── my_extension/
        ├── __init__.py
        ├── observatory_plugin.py
        └── observatory_assets/
            └── my-extension.js
```

2. Update `pyproject.toml` entry points:
```toml
[project.entry-points."phlo.observatory.extensions"]
my-extension = "my_extension:MyExtension"
```

3. Implement your plugin class:
```python
from phlo.plugins.observatory import ObservatoryExtensionPlugin, PluginMetadata

class MyExtension(ObservatoryExtensionPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my-extension",
            version="1.0.0",
            description="My custom extension",
        )
```

### Key Components

```
phlo_observatory_example/
├── __init__.py                 # Package exports and version
├── observatory_plugin.py       # Main plugin implementation
└── observatory_assets/         # Static frontend assets
    └── example.js             # Bundled JavaScript components
```

## Entry Point Registration

Extensions are auto-discovered via entry points in `pyproject.toml`:

```toml
[project.entry-points."phlo.plugins.observatory"]
example = "phlo_observatory_example:ExampleObservatoryExtension"
```

## Frontend Integration

### JavaScript Module Format

Extensions provide JavaScript modules that export registration functions:

```javascript
// observatory_assets/example.js
export function registerRoutes(router) {
  router.addRoute('/extensions/example', ExampleDashboard);
}

export function registerDashboardSlot(container) {
  container.mount(ExampleWidget);
}

export function registerSettings(container) {
  container.mount(SettingsPanel);
}
```

### API Integration

Backend endpoints are automatically prefixed with the extension name:

```python
# Access extension at /api/extensions/example/...
```

## Best Practices

1. **Keep extensions focused** - Do one thing well
2. **Use existing Phlo APIs** - Leverage capabilities system for data access
3. **Follow naming conventions** - Use kebab-case for extension names
4. **Document configuration** - Provide clear JSON schema and examples
5. **Test thoroughly** - Extensions affect the entire UI
6. **Version appropriately** - Follow semantic versioning
7. **Handle errors gracefully** - Don't crash the Observatory on errors

## Troubleshooting

### Extension Not Loading

Check entry point registration:

```bash
pip show phlo-observatory-example
# Verify entry points are correct in pyproject.toml
```

Verify the extension is discovered:

```bash
curl http://localhost:10010/api/extensions
# Should list "example" in active extensions
```

### Frontend Not Rendering

Check browser console for:
- Missing JavaScript dependencies
- Module loading errors
- API endpoint errors (404, 500)

### Settings Not Saving

Verify the settings schema is valid JSON Schema:

```python
settings_schema={
    "type": "object",
    "properties": {
        "my_setting": {"type": "string"},  # Valid types: string, number, boolean, etc.
    },
}
```

## Complete Example

Here's the actual implementation from the package:

```python
class ExampleObservatoryExtension(ObservatoryExtensionPlugin):
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
                settings_schema={
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
```

## See Also

- [phlo-observatory](phlo-observatory.md) - Main Observatory package
- [Plugin Development Guide](../guides/plugin-development.md)
- [Extension Model](../guides/extension-model.md)
- [Phlo API](../reference/phlo-api.md)

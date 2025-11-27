"""
Cascade Plugin System

Enable community contributions through a plugin architecture.

Cascade provides a plugin system that allows developers to extend
the framework with custom:
- Source connectors (ingest data from new APIs/databases)
- Quality checks (custom validation logic)
- Transformations (custom data processing steps)

## Plugin Types

### 1. Source Connector Plugins
Extend Cascade with new data sources (APIs, databases, file formats).

```python
from phlo.plugins import SourceConnectorPlugin

class MyAPIConnector(SourceConnectorPlugin):
    name = "my_api"
    version = "1.0.0"

    def fetch_data(self, config: dict) -> Iterator[dict]:
        # Implement data fetching logic
        pass
```

### 2. Quality Check Plugins
Add custom quality check types beyond the built-in checks.

```python
from phlo.plugins import QualityCheckPlugin

class CustomQualityCheck(QualityCheckPlugin):
    name = "custom_check"
    version = "1.0.0"

    def validate(self, df: pd.DataFrame) -> QualityCheckResult:
        # Implement custom validation logic
        pass
```

### 3. Transformation Plugins
Add custom transformation functions.

```python
from phlo.plugins import TransformationPlugin

class CustomTransform(TransformationPlugin):
    name = "custom_transform"
    version = "1.0.0"

    def transform(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        # Implement transformation logic
        pass
```

## Installing Plugins

Plugins are installed as Python packages with entry points:

```toml
# Plugin package's pyproject.toml
[project.entry-points."phlo.plugins.sources"]
my_api = "my_phlo_plugin:MyAPIConnector"

[project.entry-points."phlo.plugins.quality"]
custom_check = "my_phlo_plugin:CustomQualityCheck"

[project.entry-points."phlo.plugins.transforms"]
custom_transform = "my_phlo_plugin:CustomTransform"
```

After installing the plugin package:
```bash
pip install my-phlo-plugin
```

The plugin is automatically discovered and available:
```python
from phlo.plugins import discover_plugins

# Discover all installed plugins
plugins = discover_plugins()

# Use plugin
from phlo.plugins import get_source_connector
connector = get_source_connector("my_api")
data = connector.fetch_data(config={...})
```

## Plugin Development Guide

See docs/PLUGIN_DEVELOPMENT.md for complete guide on developing plugins.

## Security

Plugins are loaded from installed Python packages only. Ensure you:
- Only install trusted plugins
- Review plugin source code before installation
- Use virtual environments to isolate plugins
"""

from phlo.plugins.base import (
    Plugin,
    PluginMetadata,
    QualityCheckPlugin,
    SourceConnectorPlugin,
    TransformationPlugin,
)
from phlo.plugins.discovery import (
    discover_plugins,
    get_plugin,
    get_plugin_info,
    get_quality_check,
    get_source_connector,
    get_transformation,
    list_plugins,
    validate_plugins,
)
from phlo.plugins.registry import PluginRegistry

__all__ = [
    # Base classes
    "Plugin",
    "PluginMetadata",
    "SourceConnectorPlugin",
    "QualityCheckPlugin",
    "TransformationPlugin",
    # Discovery
    "discover_plugins",
    "list_plugins",
    "get_plugin",
    "get_plugin_info",
    "get_source_connector",
    "get_quality_check",
    "get_transformation",
    "validate_plugins",
    # Registry
    "PluginRegistry",
]

__version__ = "1.0.0"

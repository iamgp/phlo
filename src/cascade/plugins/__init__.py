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
from cascade.plugins import SourceConnectorPlugin

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
from cascade.plugins import QualityCheckPlugin

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
from cascade.plugins import TransformationPlugin

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
[project.entry-points."cascade.plugins.sources"]
my_api = "my_cascade_plugin:MyAPIConnector"

[project.entry-points."cascade.plugins.quality"]
custom_check = "my_cascade_plugin:CustomQualityCheck"

[project.entry-points."cascade.plugins.transforms"]
custom_transform = "my_cascade_plugin:CustomTransform"
```

After installing the plugin package:
```bash
pip install my-cascade-plugin
```

The plugin is automatically discovered and available:
```python
from cascade.plugins import discover_plugins

# Discover all installed plugins
plugins = discover_plugins()

# Use plugin
from cascade.plugins import get_source_connector
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

from cascade.plugins.base import (
    Plugin,
    QualityCheckPlugin,
    SourceConnectorPlugin,
    TransformationPlugin,
)
from cascade.plugins.discovery import (
    discover_plugins,
    get_plugin,
    get_quality_check,
    get_source_connector,
    get_transformation,
    list_plugins,
)
from cascade.plugins.registry import PluginRegistry

__all__ = [
    # Base classes
    "Plugin",
    "SourceConnectorPlugin",
    "QualityCheckPlugin",
    "TransformationPlugin",
    # Discovery
    "discover_plugins",
    "list_plugins",
    "get_plugin",
    "get_source_connector",
    "get_quality_check",
    "get_transformation",
    # Registry
    "PluginRegistry",
]

__version__ = "1.0.0"

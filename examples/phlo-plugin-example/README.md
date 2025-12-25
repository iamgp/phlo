# phlo-plugin-example

Reference plugin package demonstrating how to develop Phlo plugins.

This package includes examples of all three plugin types:

1. **Source Connector Plugin** - Fetch data from JSONPlaceholder API
2. **Quality Check Plugin** - Custom threshold validation
3. **Transformation Plugin** - Text transformation (uppercase)

## Installation

For development:

```bash
cd examples/phlo-plugin-example
pip install -e ".[dev]"
```

## Plugin Types Included

### 1. JSONPlaceholder Source

A source connector that fetches posts from [JSONPlaceholder API](https://jsonplaceholder.typicode.com/).

**Entry point:** `jsonplaceholder` (in `phlo.plugins.sources`)

**Configuration:**

```python
config = {
    "base_url": "https://jsonplaceholder.typicode.com",
    "limit": 10,  # Number of posts to fetch
}
```

**Usage:**

```python
from phlo.plugins import get_source_connector

source = get_source_connector("jsonplaceholder")
for post in source.fetch_data(config):
    print(post)
```

### 2. Threshold Check Quality Plugin

A quality check plugin that validates values are within a threshold.

**Entry point:** `threshold_check` (in `phlo.plugins.quality`)

**Configuration:**

```python
config = {
    "column": "value",
    "min": 0,
    "max": 100,
    "tolerance": 0.05,  # Allow 5% of rows to fail
}
```

**Usage:**

```python
from phlo.plugins import get_quality_check

plugin = get_quality_check("threshold_check")
check = plugin.create_check(column="score", min=0, max=100)
result = check.execute(df)
```

### 3. Uppercase Transform Plugin

A transformation plugin that converts string columns to uppercase.

**Entry point:** `uppercase` (in `phlo.plugins.transforms`)

**Configuration:**

```python
config = {
    "columns": ["title", "body"],  # Columns to transform
}
```

**Usage:**

```python
from phlo.plugins import get_transformation

plugin = get_transformation("uppercase")
result = plugin.transform(df, config={"columns": ["title"]})
```

## Testing

Run tests:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest tests/ --cov=src/phlo_example
```

## Code Quality

Lint the code:

```bash
ruff check src/
```

Format the code:

```bash
ruff format src/
```

## Development Guide

### Creating a Source Plugin

1. Inherit from `SourceConnectorPlugin`
2. Implement `fetch_data(config)` - yields dictionaries
3. Optionally implement `get_schema(config)` - returns column types
4. Optionally implement `test_connection(config)` - validates connectivity

```python
from phlo.plugins import SourceConnectorPlugin, PluginMetadata

class MySource(SourceConnectorPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my_source",
            version="1.0.0",
            description="My data source",
        )

    def fetch_data(self, config):
        # Yield records
        yield {"id": 1, "value": "data"}
```

### Creating a Quality Check Plugin

1. Inherit from `QualityCheckPlugin`
2. Implement `create_check(**kwargs)` - returns a QualityCheck instance

```python
from phlo.plugins import QualityCheckPlugin, PluginMetadata
from phlo_quality.checks import QualityCheck, QualityCheckResult

class MyCheckPlugin(QualityCheckPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my_check",
            version="1.0.0",
        )

    def create_check(self, **kwargs) -> QualityCheck:
        # Return check instance
        return MyCheck(**kwargs)
```

### Creating a Transform Plugin

1. Inherit from `TransformationPlugin`
2. Implement `transform(df, config)` - returns transformed DataFrame
3. Optionally implement `validate_config(config)` - validates configuration
4. Optionally implement `get_output_schema(input_schema, config)` - returns output schema

```python
from phlo.plugins import TransformationPlugin, PluginMetadata

class MyTransform(TransformationPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my_transform",
            version="1.0.0",
        )

    def transform(self, df, config):
        # Transform and return
        return df.copy()
```

## Plugin Discovery

After installation, plugins are automatically discovered via entry points:

```bash
# List all discovered plugins
phlo plugin list

# Show plugin info
phlo plugin info jsonplaceholder

# Validate plugins
phlo plugin check
```

## See Also

- [Plugin Development Guide](../../docs/PLUGIN_DEVELOPMENT.md)
- [Plugin System Documentation](../../README.md#plugin-system)
- [API Reference](../../docs/api/plugins.md)

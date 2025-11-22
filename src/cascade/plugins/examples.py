"""
Example plugins demonstrating the Cascade plugin system.

These examples show how to create plugins for:
- Source connectors (fetch data from external sources)
- Quality checks (custom validation logic)
- Transformations (custom data processing)

## Creating a Plugin Package

1. Create a new Python package:
   ```
   my-cascade-plugin/
   ├── pyproject.toml
   ├── README.md
   └── src/
       └── my_cascade_plugin/
           ├── __init__.py
           └── connectors.py
   ```

2. Define your plugin in connectors.py (see examples below)

3. Register plugin via entry points in pyproject.toml:
   ```toml
   [project.entry-points."cascade.plugins.sources"]
   weather_api = "my_cascade_plugin.connectors:WeatherAPIConnector"
   ```

4. Install the plugin package:
   ```bash
   pip install my-cascade-plugin
   ```

5. Use the plugin in Cascade:
   ```python
   from cascade.plugins import get_source_connector

   connector = get_source_connector("weather_api")
   data = connector.fetch_data(config={"api_key": "..."})
   ```
"""

from collections.abc import Iterator
from typing import Any

import pandas as pd

from cascade.plugins.base import (
    PluginMetadata,
    QualityCheckPlugin,
    SourceConnectorPlugin,
    TransformationPlugin,
)
from cascade.quality.checks import QualityCheck, QualityCheckResult

# ====================================================================
# Example 1: Source Connector Plugin
# ====================================================================


class WeatherAPIConnector(SourceConnectorPlugin):
    """
    Example source connector that fetches weather data from an API.

    Usage in pyproject.toml:
    ```toml
    [project.entry-points."cascade.plugins.sources"]
    weather_api = "my_cascade_plugin:WeatherAPIConnector"
    ```

    Usage in code:
    ```python
    from cascade.plugins import get_source_connector

    connector = get_source_connector("weather_api")
    config = {
        "api_url": "https://api.weather.com/v1/observations",
        "api_key": "your-api-key",
        "stations": ["KSFO", "KJFK", "KORD"],
    }

    for record in connector.fetch_data(config):
        print(record)
    ```
    """

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="weather_api",
            version="1.0.0",
            description="Fetch weather observations from Weather API",
            author="Cascade Community",
            license="MIT",
            homepage="https://github.com/cascade-community/weather-api-connector",
            tags=["weather", "api", "observations"],
            dependencies=["requests"],
        )

    def fetch_data(self, config: dict[str, Any]) -> Iterator[dict[str, Any]]:
        """
        Fetch weather data from API.

        Config parameters:
        - api_url: Base API URL
        - api_key: API authentication key
        - stations: List of station IDs to fetch
        """
        import requests

        api_url = config["api_url"]
        api_key = config["api_key"]
        stations = config.get("stations", [])

        headers = {"Authorization": f"Bearer {api_key}"}

        for station_id in stations:
            url = f"{api_url}/{station_id}"

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()

            # Transform API response to standard format
            yield {
                "station_id": station_id,
                "temperature": data["temp_f"],
                "humidity": data["humidity"],
                "pressure": data["pressure_mb"],
                "wind_speed": data["wind_mph"],
                "observation_time": data["observation_time"],
                "weather_condition": data["condition"],
            }

    def get_schema(self, config: dict[str, Any]) -> dict[str, str] | None:
        """Return schema of weather data."""
        return {
            "station_id": "string",
            "temperature": "float",
            "humidity": "float",
            "pressure": "float",
            "wind_speed": "float",
            "observation_time": "timestamp",
            "weather_condition": "string",
        }

    def test_connection(self, config: dict[str, Any]) -> bool:
        """Test API connectivity."""
        try:
            import requests

            api_url = config["api_url"]
            api_key = config["api_key"]

            # Try to fetch a test station
            test_station = config.get("stations", ["KSFO"])[0]
            url = f"{api_url}/{test_station}"

            response = requests.get(
                url, headers={"Authorization": f"Bearer {api_key}"}, timeout=5
            )
            return response.status_code == 200

        except Exception:
            return False


# ====================================================================
# Example 2: Quality Check Plugin
# ====================================================================


class SequentialIDCheck(QualityCheck):
    """Quality check that verifies IDs are sequential."""

    def __init__(self, column: str):
        self.column = column

    def execute(self, df: pd.DataFrame, context: Any) -> QualityCheckResult:
        """Check that IDs are sequential (1, 2, 3, ...)."""
        if self.column not in df.columns:
            return QualityCheckResult(
                passed=False,
                metric_name="sequential_id_check",
                metric_value=None,
                failure_message=f"Column '{self.column}' not found",
            )

        ids = df[self.column].sort_values()

        # Check if sequential starting from 1
        expected = range(1, len(ids) + 1)
        actual = ids.tolist()

        passed = actual == list(expected)

        if not passed:
            gaps = [
                i for i, (exp, act) in enumerate(zip(expected, actual)) if exp != act
            ]
            failure_msg = f"IDs are not sequential. Gaps at positions: {gaps[:10]}"
        else:
            failure_msg = None

        return QualityCheckResult(
            passed=passed,
            metric_name="sequential_id_check",
            metric_value={"min_id": int(ids.min()), "max_id": int(ids.max())},
            metadata={
                "column": self.column,
                "total_records": len(df),
                "min_id": int(ids.min()),
                "max_id": int(ids.max()),
            },
            failure_message=failure_msg,
        )

    @property
    def name(self) -> str:
        return f"sequential_id_{self.column}"


class SequentialIDCheckPlugin(QualityCheckPlugin):
    """
    Plugin that provides SequentialIDCheck.

    Usage in pyproject.toml:
    ```toml
    [project.entry-points."cascade.plugins.quality"]
    sequential_id = "my_cascade_plugin:SequentialIDCheckPlugin"
    ```

    Usage in code:
    ```python
    from cascade.plugins import get_quality_check
    from cascade.quality import cascade_quality

    plugin = get_quality_check("sequential_id")
    check = plugin.create_check(column="record_id")

    @cascade_quality(
        table="bronze.events",
        checks=[check],
    )
    def events_quality():
        pass
    ```
    """

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="sequential_id",
            version="1.0.0",
            description="Check that IDs are sequential without gaps",
            author="Cascade Community",
            license="MIT",
            tags=["quality", "id", "sequential"],
        )

    def create_check(self, column: str) -> QualityCheck:
        """
        Create a sequential ID check.

        Args:
            column: Column name containing IDs to check

        Returns:
            SequentialIDCheck instance
        """
        return SequentialIDCheck(column=column)


# ====================================================================
# Example 3: Transformation Plugin
# ====================================================================


class PivotTransform(TransformationPlugin):
    """
    Pivot table transformation plugin.

    Usage in pyproject.toml:
    ```toml
    [project.entry-points."cascade.plugins.transforms"]
    pivot = "my_cascade_plugin:PivotTransform"
    ```

    Usage in code:
    ```python
    from cascade.plugins import get_transformation

    pivot = get_transformation("pivot")

    result = pivot.transform(
        df,
        config={
            "index": "date",
            "columns": "category",
            "values": "amount",
            "aggfunc": "sum",
        }
    )
    ```
    """

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="pivot",
            version="1.0.0",
            description="Pivot table transformation",
            author="Cascade Community",
            license="MIT",
            tags=["transform", "pivot", "reshape"],
        )

    def transform(self, df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
        """
        Pivot a DataFrame.

        Config parameters:
        - index: Column(s) to use as index
        - columns: Column to pivot
        - values: Column(s) containing values
        - aggfunc: Aggregation function (default: "mean")
        """
        index = config["index"]
        columns = config["columns"]
        values = config["values"]
        aggfunc = config.get("aggfunc", "mean")

        return df.pivot_table(
            index=index,
            columns=columns,
            values=values,
            aggfunc=aggfunc,
        ).reset_index()

    def get_output_schema(
        self, input_schema: dict[str, str], config: dict[str, Any]
    ) -> dict[str, str] | None:
        """
        Get output schema after pivot.

        Note: Schema after pivot is dynamic based on data values,
        so we can't determine it statically.
        """
        return None  # Dynamic schema

    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate pivot configuration."""
        required_keys = ["index", "columns", "values"]
        return all(key in config for key in required_keys)


# ====================================================================
# Plugin Package Template
# ====================================================================

PLUGIN_PACKAGE_TEMPLATE = """
# Example plugin package structure

## Directory structure:
```
my-cascade-plugin/
├── pyproject.toml
├── README.md
├── LICENSE
└── src/
    └── my_cascade_plugin/
        ├── __init__.py
        ├── connectors.py
        ├── quality.py
        └── transforms.py
```

## pyproject.toml:
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-cascade-plugin"
version = "1.0.0"
description = "Custom Cascade plugins for my organization"
authors = [{name = "Your Name", email = "you@example.com"}]
license = {text = "MIT"}
requires-python = ">=3.11"
dependencies = [
    "cascade>=0.1.0",
    "pandas",
    "requests",  # If using HTTP APIs
]

# Register plugins via entry points
[project.entry-points."cascade.plugins.sources"]
weather_api = "my_cascade_plugin.connectors:WeatherAPIConnector"
stock_api = "my_cascade_plugin.connectors:StockAPIConnector"

[project.entry-points."cascade.plugins.quality"]
sequential_id = "my_cascade_plugin.quality:SequentialIDCheckPlugin"

[project.entry-points."cascade.plugins.transforms"]
pivot = "my_cascade_plugin.transforms:PivotTransform"
```

## __init__.py:
```python
from my_cascade_plugin.connectors import WeatherAPIConnector, StockAPIConnector
from my_cascade_plugin.quality import SequentialIDCheckPlugin
from my_cascade_plugin.transforms import PivotTransform

__all__ = [
    "WeatherAPIConnector",
    "StockAPIConnector",
    "SequentialIDCheckPlugin",
    "PivotTransform",
]

__version__ = "1.0.0"
```

## Installation:
```bash
pip install my-cascade-plugin
```

## Usage:
```python
from cascade.plugins import get_source_connector, get_quality_check

# Plugins are auto-discovered on import
connector = get_source_connector("weather_api")
data = connector.fetch_data(config={...})

# Use in quality checks
check_plugin = get_quality_check("sequential_id")
check = check_plugin.create_check(column="id")
```
"""

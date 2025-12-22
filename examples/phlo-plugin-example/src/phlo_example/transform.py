"""
Example transformation plugin.

Demonstrates:
- Transforming DataFrames
- Column selection and filtering
- Configuration validation
- Schema definition
"""

from typing import Any

import pandas as pd

from phlo.plugins import PluginMetadata, TransformationPlugin


class UppercaseTransformPlugin(TransformationPlugin):
    """
    Transformation plugin for uppercase conversion.

    Converts specified string columns to uppercase.

    Configuration:
        {
            "columns": ["title", "body"],  # Columns to transform
            "skip_na": True,  # Skip null values (default: True)
        }
    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="uppercase",
            version="1.0.0",
            description="Convert string columns to uppercase",
            author="Phlo Team",
            homepage="https://github.com/iamgp/phlo",
            tags=["string", "transform", "example"],
            license="MIT",
        )

    def transform(self, df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
        """
        Transform DataFrame by converting columns to uppercase.

        Args:
            df: Input DataFrame
            config: Configuration with:
                - columns: List of column names to transform
                - skip_na: Skip null values (default: True)

        Returns:
            Transformed DataFrame with uppercase values
        """
        if not self.validate_config(config):
            raise ValueError("Invalid configuration")

        # Copy to avoid modifying original
        result = df.copy()

        columns = config.get("columns", [])
        skip_na = config.get("skip_na", True)

        # Transform each column
        for column in columns:
            if column not in result.columns:
                raise ValueError(f"Column '{column}' not found in DataFrame")

            # Apply uppercase transformation
            if skip_na:
                result[column] = result[column].apply(lambda x: x.upper() if pd.notna(x) else x)
            else:
                result[column] = result[column].str.upper()

        return result

    def get_output_schema(
        self, input_schema: dict[str, str], config: dict[str, Any]
    ) -> dict[str, str] | None:
        """
        Get the schema of transformed data.

        Args:
            input_schema: Schema of input DataFrame
            config: Configuration

        Returns:
            Schema of output DataFrame (same as input)
        """
        # Uppercase transformation doesn't change types
        return input_schema

    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate transformation configuration.

        Args:
            config: Configuration to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        if not isinstance(config, dict):
            return False

        # Columns must be a list
        columns = config.get("columns", [])
        if not isinstance(columns, (list, tuple)):
            return False

        # Each column must be a string
        for column in columns:
            if not isinstance(column, str):
                return False

        # skip_na must be a boolean if provided
        skip_na = config.get("skip_na", True)
        if not isinstance(skip_na, bool):
            return False

        return True

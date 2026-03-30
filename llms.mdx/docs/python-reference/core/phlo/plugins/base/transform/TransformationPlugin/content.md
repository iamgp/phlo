# TransformationPlugin (/docs/python-reference/core/phlo/plugins/base/transform/TransformationPlugin)



Base class for transformation plugins.

Transformation plugins enable custom data processing steps
that can be composed in data pipelines.

Example:

```python
class PivotTransform(TransformationPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="pivot",
            version="1.0.0",
            description="Pivot table transformation",
        )

    def transform(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        index = config["index"]
        columns = config["columns"]
        values = config["values"]

        return df.pivot_table(
            index=index,
            columns=columns,
            values=values,
            aggfunc=config.get("aggfunc", "mean")
        )

    def get_output_schema(self, input_schema: dict, config: dict) -> dict:
        # Return schema of transformed data
        return \{...\}
```

Functions [#functions]

<PyFunction name="&#x22;transform&#x22;" type="&#x22;(self, df, config) -> pd.DataFrame&#x22;">
  Transform a DataFrame.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    ```python
    def transform(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        column = config["column"]
        multiplier = config.get("multiplier", 1.0)

        df = df.copy()
        df[column] = df[column] * multiplier
        return df
    ```
  </Callout>

  <PySourceCode>
    ````python
    @abstractmethod
    def transform(self, df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
        """Transform a DataFrame.

        Args:
            df: Input DataFrame
            config: Configuration for the transformation

        Returns:
            Transformed DataFrame

        Example:
            \```python
            def transform(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
                column = config["column"]
                multiplier = config.get("multiplier", 1.0)

                df = df.copy()
                df[column] = df[column] * multiplier
                return df
            \```

        """
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;df&#x22;" type="&#x22;pd.DataFrame&#x22;" value="undefined">
      Input DataFrame
    </PyParameter>

    <PyParameter name="&#x22;config&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Configuration for the transformation
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;pandas.DataFrame&#x22;">
    Transformed DataFrame
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_output_schema&#x22;" type="&#x22;(self, input_schema, config) -> dict[str, str] | None&#x22;">
  Get the schema of transformed data.

  This method is optional but recommended for type inference.

  <PySourceCode>
    ```python
    def get_output_schema(
        self, input_schema: dict[str, str], config: dict[str, Any]
    ) -> dict[str, str] | None:
        """Get the schema of transformed data.

        This method is optional but recommended for type inference.

        Args:
            input_schema: Schema of input DataFrame
            config: Configuration for the transformation

        Returns:
            Schema of output DataFrame or None if unknown

        """
        return None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;input_schema&#x22;" type="&#x22;dict[str, str]&#x22;" value="undefined">
      Schema of input DataFrame
    </PyParameter>

    <PyParameter name="&#x22;config&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Configuration for the transformation
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict[str, str] | None&#x22;">
    Schema of output DataFrame or None if unknown
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;validate_config&#x22;" type="&#x22;(self, config) -> bool&#x22;">
  Validate transformation configuration.

  This method is optional but recommended for catching errors early.

  <PySourceCode>
    ```python
    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate transformation configuration.

        This method is optional but recommended for catching errors early.

        Args:
            config: Configuration to validate

        Returns:
            True if configuration is valid, False otherwise

        """
        return True
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;config&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Configuration to validate
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    True if configuration is valid, False otherwise
  </PyFunctionReturn>
</PyFunction>

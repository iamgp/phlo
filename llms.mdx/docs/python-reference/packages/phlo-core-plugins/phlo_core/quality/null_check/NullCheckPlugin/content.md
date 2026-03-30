# NullCheckPlugin (/docs/python-reference/packages/phlo-core-plugins/phlo_core/quality/null_check/NullCheckPlugin)



Plugin for performing null value validation on data columns.

This plugin creates null check instances that validate whether specified
columns contain null values within acceptable thresholds. It supports both
strict validation (no nulls allowed) and lenient validation (allows a
configurable percentage of nulls per column).

The null check is particularly useful for:

* Validating required field completeness
* Detecting data quality issues in ETL pipelines
* Enforcing data completeness SLAs
* Identifying sparse columns that may need attention

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  PluginMetadata containing name, version, description,
  author, and tags for this plugin.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;create_check&#x22;" type="&#x22;(self, columns, allow_threshold=0.0) -> Any&#x22;">
  Create a null check instance.

  Creates and returns a configured NullCheck instance from phlo\_pandera
  that validates null value presence in specified columns.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Create a strict null check::

    from phlo\_core.quality.null\_check import NullCheckPlugin

    plugin = NullCheckPlugin()
    check = plugin.create\_check(
    columns=\["customer\_id", "order\_date"],
    allow\_threshold=0.0
    )

    Create a lenient null check for optional fields::

    check = plugin.create\_check(
    columns=\["middle\_name", "secondary\_email"],
    allow\_threshold=0.15  # 15% tolerance
    )

    Apply to DataFrame directly::

    result = check.validate(df)
  </Callout>

  <PySourceCode>
    ```python
    def create_check(self, columns: list[str], allow_threshold: float = 0.0) -> Any:
        """Create a null check instance.

        Creates and returns a configured NullCheck instance from phlo_pandera
        that validates null value presence in specified columns.

        Args:
            columns: List of column names to validate for null values.
                Each column in the list will be checked individually for
                null value presence against the threshold.
            allow_threshold: Maximum allowed null ratio per column as a float
                between 0.0 and 1.0. Defaults to 0.0 (strict validation, no
                nulls allowed). A threshold of 0.10 allows up to 10% of values
                in each column to be null.

        Returns:
            Any: Configured NullCheck instance ready to validate data.
            The returned object can be used with Pandera schemas or called
            directly with DataFrames.

        Raises:
            ValueError: If allow_threshold is not between 0.0 and 1.0.

        Example:
            Create a strict null check::

                from phlo_core.quality.null_check import NullCheckPlugin

                plugin = NullCheckPlugin()
                check = plugin.create_check(
                    columns=["customer_id", "order_date"],
                    allow_threshold=0.0
                )

            Create a lenient null check for optional fields::

                check = plugin.create_check(
                    columns=["middle_name", "secondary_email"],
                    allow_threshold=0.15  # 15% tolerance
                )

            Apply to DataFrame directly::

                result = check.validate(df)

        """
        from phlo_pandera.checks import NullCheck

        return NullCheck(columns=columns, allow_threshold=allow_threshold)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;columns&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
      List of column names to validate for null values.
      Each column in the list will be checked individually for
      null value presence against the threshold.
    </PyParameter>

    <PyParameter name="&#x22;allow_threshold&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;">
      Maximum allowed null ratio per column as a float
      between 0.0 and 1.0. Defaults to 0.0 (strict validation, no
      nulls allowed). A threshold of 0.10 allows up to 10% of values
      in each column to be null.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Configured NullCheck instance ready to validate data.
  </PyFunctionReturn>
</PyFunction>

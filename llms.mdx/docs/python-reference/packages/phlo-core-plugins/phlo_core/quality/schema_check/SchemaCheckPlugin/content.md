# SchemaCheckPlugin (/docs/python-reference/packages/phlo-core-plugins/phlo_core/quality/schema_check/SchemaCheckPlugin)



Plugin for performing schema validation on data.

This plugin creates schema check instances that validate data against
expected column structures and data types. It supports both strict
validation (fails immediately) and lazy validation (collects all errors).

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  PluginMetadata containing name, version, description,
  author, and tags for this plugin.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;create_check&#x22;" type="&#x22;(self, schema, lazy=True) -> Any&#x22;">
  Create a schema check instance.

  Creates and returns a configured SchemaCheck instance from phlo\_pandera
  that validates data against the provided schema.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Create a schema check with lazy validation::

    from phlo\_core.quality.schema\_check import SchemaCheckPlugin
    import pandera as pa

    plugin = SchemaCheckPlugin()
    schema = pa.DataFrameSchema(\{
    "id": pa.Column(pa.Int64, nullable=False),
    "value": pa.Column(pa.Float, nullable=True)
    })

    check = plugin.create\_check(schema=schema, lazy=True)

    Create a schema check with strict validation::

    strict\_check = plugin.create\_check(schema=schema, lazy=False)
  </Callout>

  <PySourceCode>
    ```python
    def create_check(self, schema: Any, lazy: bool = True) -> Any:
        """Create a schema check instance.

        Creates and returns a configured SchemaCheck instance from phlo_pandera
        that validates data against the provided schema.

        Args:
            schema: Expected schema object for validation. This is typically
                a Pandera DataFrameSchema or similar schema definition that
                defines expected columns, types, and constraints.
            lazy: Whether to collect all validation errors before failing.
                When True, all validation errors are collected and reported
                together. When False, validation fails on the first error.
                Defaults to True.

        Returns:
            Any: Configured SchemaCheck instance ready to validate data.
            The returned object has a ``validate()`` method that accepts
            a DataFrame and returns the validated data or raises a
            SchemaError if validation fails.

        Example:
            Create a schema check with lazy validation::

                from phlo_core.quality.schema_check import SchemaCheckPlugin
                import pandera as pa

                plugin = SchemaCheckPlugin()
                schema = pa.DataFrameSchema({
                    "id": pa.Column(pa.Int64, nullable=False),
                    "value": pa.Column(pa.Float, nullable=True)
                })

                check = plugin.create_check(schema=schema, lazy=True)

            Create a schema check with strict validation::

                strict_check = plugin.create_check(schema=schema, lazy=False)

        """
        from phlo_pandera.checks_extra import SchemaCheck

        return SchemaCheck(schema=schema, lazy=lazy)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Expected schema object for validation. This is typically
      a Pandera DataFrameSchema or similar schema definition that
      defines expected columns, types, and constraints.
    </PyParameter>

    <PyParameter name="&#x22;lazy&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      Whether to collect all validation errors before failing.
      When True, all validation errors are collected and reported
      together. When False, validation fails on the first error.
      Defaults to True.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Configured SchemaCheck instance ready to validate data.
  </PyFunctionReturn>
</PyFunction>

# PanderaQualityProvider (/docs/python-reference/packages/phlo-pandera/phlo_pandera/plugin/PanderaQualityProvider)



Pandera-based quality provider for Phlo.

This plugin class integrates the Phlo Quality Framework with Phlo's plugin
system. It provides access to all quality check classes, the `@phlo_pandera`
decorator, schema extraction, and reconciliation checks.

The plugin is automatically discovered by Phlo's plugin system via the
`phlo.quality_providers` entry point.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Plugin identification information (name, version, description).
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_decorator&#x22;" type="&#x22;(self) -> Callable&#x22;">
  Return the @phlo\_pandera decorator.

  Returns the main decorator used for defining quality checks in a
  declarative manner.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    ```python
    provider = PanderaQualityProvider()
    phlo_pandera = provider.get_decorator()

    @phlo_pandera(table="bronze.events", checks=[...])
    def quality_check():
        pass
    ```
  </Callout>

  <PySourceCode>
    ````python
    def get_decorator(self) -> Callable:
        """Return the @phlo_pandera decorator.

        Returns the main decorator used for defining quality checks in a
        declarative manner.

        Returns:
            The ``phlo_pandera`` decorator function.

        Example:
            \```python
            provider = PanderaQualityProvider()
            phlo_pandera = provider.get_decorator()

            @phlo_pandera(table="bronze.events", checks=[...])
            def quality_check():
                pass
            \```

        """
        from phlo_pandera import phlo_pandera

        return phlo_pandera
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Callable&#x22;">
    The `phlo_pandera` decorator function.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_check_classes&#x22;" type="&#x22;(self) -> dict[str, type]&#x22;">
  Return built-in check classes.

  Returns a dictionary mapping check type names to their corresponding
  class implementations.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    ```python
    provider = PanderaQualityProvider()
    checks = provider.get_check_classes()

    NullCheck = checks["null"]
    RangeCheck = checks["range"]
    ```
  </Callout>

  <PySourceCode>
    ````python
    def get_check_classes(self) -> dict[str, type]:
        """Return built-in check classes.

        Returns a dictionary mapping check type names to their corresponding
        class implementations.

        Returns:
            Dictionary of check class names to types, including:
            - null, range, freshness, unique, count
            - schema, pattern, quality_check (base class)

        Example:
            \```python
            provider = PanderaQualityProvider()
            checks = provider.get_check_classes()

            NullCheck = checks["null"]
            RangeCheck = checks["range"]
            \```

        """
        from phlo_pandera import (
            CountCheck,
            FreshnessCheck,
            NullCheck,
            PatternCheck,
            QualityCheck,
            RangeCheck,
            SchemaCheck,
            UniqueCheck,
        )

        return {
            "null": NullCheck,
            "range": RangeCheck,
            "freshness": FreshnessCheck,
            "unique": UniqueCheck,
            "count": CountCheck,
            "schema": SchemaCheck,
            "pattern": PatternCheck,
            "quality_check": QualityCheck,
        }
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary of check class names to types, including:
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_schema_extractor&#x22;" type="&#x22;(self) -> Any&#x22;">
  Return Pandera schema extractor.

  Returns the schema extractor class used to convert Pandera DataFrameModel
  schemas into normalized schemas for storage provider integration.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    ```python
    provider = PanderaQualityProvider()
    Extractor = provider.get_schema_extractor()

    extractor = Extractor()
    normalized_schema = extractor.extract(MyPanderaSchema)
    ```
  </Callout>

  <PySourceCode>
    ````python
    def get_schema_extractor(self) -> Any:
        """Return Pandera schema extractor.

        Returns the schema extractor class used to convert Pandera DataFrameModel
        schemas into normalized schemas for storage provider integration.

        Returns:
            PanderaSchemaExtractor class (not an instance).

        Example:
            \```python
            provider = PanderaQualityProvider()
            Extractor = provider.get_schema_extractor()

            extractor = Extractor()
            normalized_schema = extractor.extract(MyPanderaSchema)
            \```

        """
        from phlo_pandera import PanderaSchemaExtractor

        return PanderaSchemaExtractor
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    PanderaSchemaExtractor class (not an instance).
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_reconciliation_checks&#x22;" type="&#x22;(self) -> dict[str, type] | None&#x22;">
  Return reconciliation check classes.

  Returns a dictionary mapping reconciliation check type names to their
  corresponding class implementations. These checks validate data
  consistency across tables.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    ```python
    provider = PanderaQualityProvider()
    reconciliations = provider.get_reconciliation_checks()

    ReconciliationCheck = reconciliations["reconciliation"]
    KeyParityCheck = reconciliations["key_parity"]
    ```
  </Callout>

  <PySourceCode>
    ````python
    def get_reconciliation_checks(self) -> dict[str, type] | None:
        """Return reconciliation check classes.

        Returns a dictionary mapping reconciliation check type names to their
        corresponding class implementations. These checks validate data
        consistency across tables.

        Returns:
            Dictionary of reconciliation check names to types, including:
            - reconciliation (row count parity)
            - aggregate_consistency
            - key_parity
            - multi_aggregate
            - checksum

        Example:
            \```python
            provider = PanderaQualityProvider()
            reconciliations = provider.get_reconciliation_checks()

            ReconciliationCheck = reconciliations["reconciliation"]
            KeyParityCheck = reconciliations["key_parity"]
            \```

        """
        from phlo_pandera import (
            AggregateConsistencyCheck,
            AggregateSpec,
            ChecksumReconciliationCheck,
            KeyParityCheck,
            MultiAggregateConsistencyCheck,
            ReconciliationCheck,
        )

        return {
            "reconciliation": ReconciliationCheck,
            "aggregate_consistency": AggregateConsistencyCheck,
            "aggregate_spec": AggregateSpec,
            "key_parity": KeyParityCheck,
            "multi_aggregate": MultiAggregateConsistencyCheck,
            "checksum": ChecksumReconciliationCheck,
        }
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, type] | None&#x22;">
    Dictionary of reconciliation check names to types, including:
  </PyFunctionReturn>
</PyFunction>

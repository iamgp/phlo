# QualityProviderPlugin (/docs/python-reference/core/phlo/plugins/base/quality_provider/QualityProviderPlugin)



Base class for quality provider plugins.

Quality provider plugins supply the core quality primitives:

* The @phlo\_quality decorator
* Built-in check classes (NullCheck, RangeCheck, etc.)
* Schema extraction capabilities

Example:

```python
from phlo.plugins.base import QualityProviderPlugin, PluginMetadata

class PanderaQualityProvider(QualityProviderPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="pandera",
            version="0.1.0",
            description="Pandera-based quality provider",
        )

    def get_decorator(self) -> Callable:
        from phlo_pandera import phlo_quality
        return phlo_quality

    def get_check_classes(self) -> dict[str, type]:
        from phlo_pandera import (
            NullCheck, RangeCheck, FreshnessCheck,
            UniqueCheck, CountCheck, SchemaCheck,
        )
        return \{
            "null": NullCheck,
            "range": RangeCheck,
            "freshness": FreshnessCheck,
            "unique": UniqueCheck,
            "count": CountCheck,
            "schema": SchemaCheck,
        \}

    def get_schema_extractor(self) -> Any:
        from phlo_pandera import PanderaSchemaExtractor
        return PanderaSchemaExtractor
```

Functions [#functions]

<PyFunction name="&#x22;get_decorator&#x22;" type="&#x22;(self) -> Callable&#x22;">
  Return the quality decorator function.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    ```python
    def get_decorator(self) -> Callable:
        from phlo_pandera import phlo_quality
        return phlo_quality
    ```
  </Callout>

  <PySourceCode>
    ````python
    @abstractmethod
    def get_decorator(self) -> Callable:
        """Return the quality decorator function.

        Returns:
            The @phlo_quality decorator or equivalent.

        Example:
            \```python
            def get_decorator(self) -> Callable:
                from phlo_pandera import phlo_quality
                return phlo_quality
            \```

        """
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Callable&#x22;">
    The @phlo\_quality decorator or equivalent.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_check_classes&#x22;" type="&#x22;(self) -> dict[str, type]&#x22;">
  Return a mapping of check type names to classes.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    ```python
    def get_check_classes(self) -> dict[str, type]:
        from phlo_pandera import NullCheck, RangeCheck
        return \{"null": NullCheck, "range": RangeCheck\}
    ```
  </Callout>

  <PySourceCode>
    ````python
    @abstractmethod
    def get_check_classes(self) -> dict[str, type]:
        """Return a mapping of check type names to classes.

        Returns:
            Dictionary mapping short names to check classes.

        Example:
            \```python
            def get_check_classes(self) -> dict[str, type]:
                from phlo_pandera import NullCheck, RangeCheck
                return {"null": NullCheck, "range": RangeCheck}
            \```

        """
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary mapping short names to check classes.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_schema_extractor&#x22;" type="&#x22;(self) -> Any | None&#x22;">
  Return a schema extractor class for converting native schemas.

  <PySourceCode>
    ```python
    def get_schema_extractor(self) -> Any | None:
        """Return a schema extractor class for converting native schemas.

        Returns:
            Schema extractor class, or None if not available.

        """
        return None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;Any | None&#x22;">
    Schema extractor class, or None if not available.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_reconciliation_checks&#x22;" type="&#x22;(self) -> dict[str, type] | None&#x22;">
  Return reconciliation check classes.

  <PySourceCode>
    ```python
    def get_reconciliation_checks(self) -> dict[str, type] | None:
        """Return reconciliation check classes.

        Returns:
            Dictionary mapping check names to classes, or None.

        """
        return None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, type] | None&#x22;">
    Dictionary mapping check names to classes, or None.
  </PyFunctionReturn>
</PyFunction>

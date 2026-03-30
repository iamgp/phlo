# TransformationProviderPlugin (/docs/python-reference/core/phlo/plugins/base/transformation_provider/TransformationProviderPlugin)



Base class for transformation provider plugins.

Transformation provider plugins supply the core transformation primitives:

* The @phlo\_transformation decorator (or similar)
* Asset spec generation from transformation models
* CLI integration for running transformations
* Compilation and manifest capabilities

Example:

```python
from phlo.plugins.base import TransformationProviderPlugin, PluginMetadata

class DbtTransformationProvider(TransformationProviderPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dbt",
            version="0.1.0",
            description="dbt-based transformation provider",
        )

    def get_asset_retriever(self) -> Callable[[], list[Any]]:
        from phlo_dbt.assets import build_dbt_asset_specs
        return build_dbt_asset_specs

    def get_cli_plugin(self) -> Any:
        from phlo_dbt.cli_plugin import DbtCliPlugin
        return DbtCliPlugin
```

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_asset_retriever&#x22;" type="&#x22;(self) -> Callable[[], list[Any]]&#x22;">
  Return a function to retrieve transformation asset specs.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    ```python
    def get_asset_retriever(self) -> Callable[[], list[Any]]:
        from phlo_dbt.assets import build_dbt_asset_specs
        return build_dbt_asset_specs
    ```
  </Callout>

  <PySourceCode>
    ````python
    @abstractmethod
    def get_asset_retriever(self) -> Callable[[], list[Any]]:
        """Return a function to retrieve transformation asset specs.

        Returns:
            Function that returns a list of asset specifications.

        Example:
            \```python
            def get_asset_retriever(self) -> Callable[[], list[Any]]:
                from phlo_dbt.assets import build_dbt_asset_specs
                return build_dbt_asset_specs
            \```

        """
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Callable&#x22;">
    Function that returns a list of asset specifications.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_cli_plugin&#x22;" type="&#x22;(self) -> Any | None&#x22;">
  Return a CLI plugin class for transformation commands.

  <PySourceCode>
    ```python
    def get_cli_plugin(self) -> Any | None:
        """Return a CLI plugin class for transformation commands.

        Returns:
            CLI plugin class, or None if not available.

        """
        return None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;Any | None&#x22;">
    CLI plugin class, or None if not available.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_compiler&#x22;" type="&#x22;(self) -> Any | None&#x22;">
  Return a compiler function for the transformation.

  <PySourceCode>
    ```python
    def get_compiler(self) -> Any | None:
        """Return a compiler function for the transformation.

        Returns:
            Compiler function, or None if not available.

        """
        return None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;Any | None&#x22;">
    Compiler function, or None if not available.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_manifest_loader&#x22;" type="&#x22;(self) -> Any | None&#x22;">
  Return a manifest loader function.

  <PySourceCode>
    ```python
    def get_manifest_loader(self) -> Any | None:
        """Return a manifest loader function.

        Returns:
            Manifest loader function, or None if not available.

        """
        return None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;Any | None&#x22;">
    Manifest loader function, or None if not available.
  </PyFunctionReturn>
</PyFunction>

# IngestionProviderPlugin (/docs/python-reference/core/phlo/plugins/base/ingestion_provider/IngestionProviderPlugin)



Base class for ingestion provider plugins.

Ingestion provider plugins supply the core ingestion primitives:

* The @phlo\_ingestion decorator
* Asset registration and retrieval
* Source connectors and pipeline configurations

Example:

```python
from phlo.plugins.base import IngestionProviderPlugin, PluginMetadata

class DLTIngestionProvider(IngestionProviderPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dlt",
            version="0.1.0",
            description="DLT-based ingestion provider",
        )

    def get_decorator(self) -> Callable:
        from phlo_dlt import phlo_ingestion
        return phlo_ingestion

    def get_asset_retriever(self) -> Callable:
        from phlo_dlt import get_ingestion_assets
        return get_ingestion_assets
```

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_decorator&#x22;" type="&#x22;(self) -> Callable&#x22;">
  Return the ingestion decorator function.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    ```python
    def get_decorator(self) -> Callable:
        from phlo_dlt import phlo_ingestion
        return phlo_ingestion
    ```
  </Callout>

  <PySourceCode>
    ````python
    @abstractmethod
    def get_decorator(self) -> Callable:
        """Return the ingestion decorator function.

        Returns:
            The @phlo_ingestion decorator or equivalent.

        Example:
            \```python
            def get_decorator(self) -> Callable:
                from phlo_dlt import phlo_ingestion
                return phlo_ingestion
            \```

        """
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Callable&#x22;">
    The @phlo\_ingestion decorator or equivalent.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_asset_retriever&#x22;" type="&#x22;(self) -> Callable[[], list[Any]]&#x22;">
  Return a function to retrieve registered ingestion assets.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    ```python
    def get_asset_retriever(self) -> Callable[[], list[Any]]:
        from phlo_dlt import get_ingestion_assets
        return get_ingestion_assets
    ```
  </Callout>

  <PySourceCode>
    ````python
    @abstractmethod
    def get_asset_retriever(self) -> Callable[[], list[Any]]:
        """Return a function to retrieve registered ingestion assets.

        Returns:
            Function that returns a list of registered ingestion assets.

        Example:
            \```python
            def get_asset_retriever(self) -> Callable[[], list[Any]]:
                from phlo_dlt import get_ingestion_assets
                return get_ingestion_assets
            \```

        """
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Callable&#x22;">
    Function that returns a list of registered ingestion assets.
  </PyFunctionReturn>
</PyFunction>

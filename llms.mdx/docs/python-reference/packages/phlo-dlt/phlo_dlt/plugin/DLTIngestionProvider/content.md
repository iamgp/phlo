# DLTIngestionProvider (/docs/python-reference/packages/phlo-dlt/phlo_dlt/plugin/DLTIngestionProvider)



DLT-based ingestion provider for Phlo.

Ingestion provider plugin that exposes DLT-based ingestion
capabilities through the standardized ingestion provider interface.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Static plugin metadata for discovery.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_decorator&#x22;" type="&#x22;(self) -> Callable&#x22;">
  Return the @phlo\_ingestion decorator.

  <PySourceCode>
    ```python
    def get_decorator(self) -> Callable:
        """Return the @phlo_ingestion decorator.

        Returns:
            Callable: The phlo_ingestion decorator function.

        """
        from phlo_dlt import phlo_ingestion

        return phlo_ingestion
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Callable&#x22;">
    The phlo\_ingestion decorator function.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_asset_retriever&#x22;" type="&#x22;(self) -> Callable[[], list[Any]]&#x22;">
  Return function to get registered ingestion assets.

  <PySourceCode>
    ```python
    def get_asset_retriever(self) -> Callable[[], list[Any]]:
        """Return function to get registered ingestion assets.

        Returns:
            Callable[[], list[Any]]: Function that returns list of AssetSpec objects.

        """
        return get_ingestion_assets
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Callable&#x22;">
    Callable\[\[], list\[Any]]: Function that returns list of AssetSpec objects.
  </PyFunctionReturn>
</PyFunction>

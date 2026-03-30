# SlingIngestionProvider (/docs/python-reference/packages/phlo-sling/phlo_sling/plugin/SlingIngestionProvider)



Sling-based ingestion provider for Phlo.

This plugin class exposes Sling replication as an ingestion mechanism
within the Phlo platform. It provides the decorator and asset retrieval
functions needed to define and execute Sling-based data replication.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Information about this plugin including
  name, version, and description.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_decorator&#x22;" type="&#x22;(self) -> Callable&#x22;">
  Return the @phlo\_sling\_replication decorator.

  Returns the decorator function that can be used to register
  Sling-backed replication assets.

  <PySourceCode>
    ```python
    def get_decorator(self) -> Callable:
        """Return the @phlo_sling_replication decorator.

        Returns the decorator function that can be used to register
        Sling-backed replication assets.

        Returns:
            Callable decorator function for registering Sling replication
            definitions.

        """
        from phlo_sling import phlo_sling_replication

        return phlo_sling_replication
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Callable&#x22;">
    Callable decorator function for registering Sling replication
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_asset_retriever&#x22;" type="&#x22;(self) -> Callable[[], list[Any]]&#x22;">
  Return function to get registered replication assets.

  Returns a callable that, when invoked, returns the list of all
  registered Sling replication assets.

  <PySourceCode>
    ```python
    def get_asset_retriever(self) -> Callable[[], list[Any]]:
        """Return function to get registered replication assets.

        Returns a callable that, when invoked, returns the list of all
        registered Sling replication assets.

        Returns:
            Callable that returns a list of registered Sling asset
            specifications.

        """
        return get_sling_assets
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Callable&#x22;">
    Callable that returns a list of registered Sling asset
  </PyFunctionReturn>
</PyFunction>

# phlo_sling (/docs/python-reference/packages/phlo-sling/phlo_sling)



Phlo Sling package for data replication.

This package provides Sling-based data replication capabilities for the Phlo
platform, enabling declarative and programmatic definitions of replication
pipelines from various sources to target data stores.

The package exposes decorators for registering Sling-backed assets and
functions for retrieving registered assets at runtime.

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['SlingReplication', 'get_sling_assets', 'phlo_sling_assets', 'phlo_sling_replication']&#x22;" />

<Tabs items="[&#x22;Functions&#x22;,&#x22;Modules&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;phlo_sling_assets&#x22;" type="&#x22;(*args, **kwargs) -> Callable[..., Any]&#x22;">
      Lazily resolve and forward to the Sling asset discovery decorator.

      This function provides lazy loading of the actual decorator implementation
      to avoid circular imports and reduce startup time.

      <PySourceCode>
        ```python
        def phlo_sling_assets(*args: Any, **kwargs: Any) -> Callable[..., Any]:
            """Lazily resolve and forward to the Sling asset discovery decorator.

            This function provides lazy loading of the actual decorator implementation
            to avoid circular imports and reduce startup time.

            Args:
                *args: Positional arguments forwarded to the actual decorator.
                **kwargs: Keyword arguments forwarded to the actual decorator.

            Returns:
                The result of calling the actual phlo_sling_assets decorator with
                the provided arguments.

            """
            from phlo_sling.decorator import phlo_sling_assets as _phlo_sling_assets

            return _phlo_sling_assets(*args, **kwargs)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;args&#x22;" type="&#x22;Any&#x22;" value="&#x22;()&#x22;" />

        <PyParameter name="&#x22;kwargs&#x22;" type="&#x22;Any&#x22;" value="&#x22;{}&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;collections.abc.Callable&#x22;">
        The result of calling the actual phlo\_sling\_assets decorator with
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;phlo_sling_replication&#x22;" type="&#x22;(*args, **kwargs) -> Callable[..., Any]&#x22;">
      Lazily resolve and forward to the Sling replication decorator factory.

      This function provides lazy loading of the actual decorator implementation
      to avoid circular imports and reduce startup time.

      <PySourceCode>
        ```python
        def phlo_sling_replication(*args: Any, **kwargs: Any) -> Callable[..., Any]:
            """Lazily resolve and forward to the Sling replication decorator factory.

            This function provides lazy loading of the actual decorator implementation
            to avoid circular imports and reduce startup time.

            Args:
                *args: Positional arguments forwarded to the actual decorator.
                **kwargs: Keyword arguments forwarded to the actual decorator.

            Returns:
                The result of calling the actual phlo_sling_replication decorator
                with the provided arguments.

            """
            from phlo_sling.decorator import phlo_sling_replication as _phlo_sling_replication

            return _phlo_sling_replication(*args, **kwargs)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;args&#x22;" type="&#x22;Any&#x22;" value="&#x22;()&#x22;" />

        <PyParameter name="&#x22;kwargs&#x22;" type="&#x22;Any&#x22;" value="&#x22;{}&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;collections.abc.Callable&#x22;">
        The result of calling the actual phlo\_sling\_replication decorator
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_sling_assets&#x22;" type="&#x22;() -> list[Any]&#x22;">
      Lazily resolve and return registered sling replication assets.

      This function provides lazy loading of the asset retrieval implementation
      to avoid circular imports and reduce startup time.

      <PySourceCode>
        ```python
        def get_sling_assets() -> list[Any]:
            """Lazily resolve and return registered sling replication assets.

            This function provides lazy loading of the asset retrieval implementation
            to avoid circular imports and reduce startup time.

            Returns:
                List of registered Sling replication asset specifications.

            """
            from phlo_sling.decorator import get_sling_assets as _get_sling_assets

            return _get_sling_assets()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;list&#x22;">
        List of registered Sling replication asset specifications.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>

  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/packages/phlo-sling/phlo_sling/executor&#x22;" title="&#x22;executor&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-sling/phlo_sling/plugin&#x22;" title="&#x22;plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-sling/phlo_sling/decorator&#x22;" title="&#x22;decorator&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-sling/phlo_sling/cli_commands&#x22;" title="&#x22;cli_commands&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-sling/phlo_sling/cli_plugin&#x22;" title="&#x22;cli_plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-sling/phlo_sling/settings&#x22;" title="&#x22;settings&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-sling/phlo_sling/connections&#x22;" title="&#x22;connections&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-sling/phlo_sling/registry&#x22;" title="&#x22;registry&#x22;" />
    </Cards>
  </Tab>
</Tabs>

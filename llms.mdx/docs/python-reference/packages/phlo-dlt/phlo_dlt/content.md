# phlo_dlt (/docs/python-reference/packages/phlo-dlt/phlo_dlt)



Phlo DLT - DLT-based data ingestion package for Phlo.

This package provides DLT (Data Load Tool) based ingestion capabilities for Phlo,
enabling decorator-driven data extraction and loading into the lakehouse. It
integrates with Pandera for schema validation and supports multiple table store
backends through the Phlo capability system.

Key Features:

* Decorator-based ingestion definition (@phlo\_ingestion)
* Automatic schema validation with Pandera
* Support for append and merge strategies
* Partitioned ingestion with daily scheduling
* Write-Audit-Publish (WAP) pattern support
* Metadata column injection for lineage tracking

Main Exports:

* :func:`phlo_ingestion`: Primary decorator for defining ingestion pipelines
* :func:`get_ingestion_assets`: Retrieve all registered ingestion assets

Internal Modules:

* :mod:`phlo_dlt.decorator`: Core ingestion decorator implementation
* :mod:`phlo_dlt.executor`: DLT ingestion execution engine
* :mod:`phlo_dlt.dlt_helpers`: Shared utilities for DLT operations
* :mod:`phlo_dlt.pandera_checks`: Pandera schema validation integration
* :mod:`phlo_dlt.registry`: Table configuration and registration
* :mod:`phlo_dlt.settings`: Package configuration settings
* :mod:`phlo_dlt.plugin`: Plugin interface for Phlo integration
* :mod:`phlo_dlt.scaffold`: Workflow scaffolding utilities
* :mod:`phlo_dlt.cli_plugin`: CLI command plugin
* :mod:`phlo_dlt.cli_workflow`: Workflow management CLI commands

Dependencies:

* dlt: Data Load Tool for extraction
* pandera: Schema validation
* pyarrow: Parquet file handling
* pandas: Data manipulation

Example:

```python
from phlo_dlt import phlo_ingestion
from my_schemas import UserSchema

@phlo_ingestion(
    table_name="users",
    unique_key="id",
    group="raw",
    validation_schema=UserSchema,
    cron="0 */6 * * *",
)
def load_users(partition_date: str):
    # Return DLT source or data
    return fetch_user_data(partition_date)

# Get all registered assets
assets = get_ingestion_assets()
```

See Also:

* :mod:`phlo.ingestion`: Public API for ingestion operations
* :mod:`phlo_dlt.decorator`: Detailed decorator documentation
* Documentation: [https://docs.phlo.dev/packages/phlo-dlt](https://docs.phlo.dev/packages/phlo-dlt)

Note:
This package is typically accessed through `phlo.ingestion` rather than
directly. Use `import phlo` or `from phlo.ingestion import phlo_ingestion`.

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['get_ingestion_assets', 'phlo_ingestion']&#x22;" />

<Tabs items="[&#x22;Functions&#x22;,&#x22;Modules&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;phlo_ingestion&#x22;" type="&#x22;(*args, **kwargs) -> Callable[..., Any]&#x22;">
      Lazily resolve and forward to the ingestion decorator factory.

      This function provides a lazy-loading mechanism for the actual
      `phlo_ingestion` decorator from `phlo_dlt.decorator`. It avoids
      eager imports to prevent circular dependencies during plugin discovery.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        from phlo_dlt import phlo_ingestion

        @phlo_ingestion(table_name="events", unique_key="id", group="raw")
        def load_events(partition_date: str):
            return fetch_events(partition_date)
        ```
      </Callout>

      <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
        :func:`phlo_dlt.decorator.phlo_ingestion`: The actual decorator implementation.
      </Callout>

      <PySourceCode>
        ````python
        def phlo_ingestion(*args: Any, **kwargs: Any) -> Callable[..., Any]:
            """Lazily resolve and forward to the ingestion decorator factory.

            This function provides a lazy-loading mechanism for the actual
            ``phlo_ingestion`` decorator from ``phlo_dlt.decorator``. It avoids
            eager imports to prevent circular dependencies during plugin discovery.

            Args:
                *args: Positional arguments passed to the actual decorator.
                **kwargs: Keyword arguments passed to the actual decorator.

            Returns:
                Callable[..., Any]: The configured ingestion decorator.

            Example:
                \```python
                from phlo_dlt import phlo_ingestion

                @phlo_ingestion(table_name="events", unique_key="id", group="raw")
                def load_events(partition_date: str):
                    return fetch_events(partition_date)
                \```

            See Also:
                :func:`phlo_dlt.decorator.phlo_ingestion`: The actual decorator implementation.

            """
            from phlo_dlt.decorator import phlo_ingestion as _phlo_ingestion

            return _phlo_ingestion(*args, **kwargs)
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;args&#x22;" type="&#x22;Any&#x22;" value="&#x22;()&#x22;" />

        <PyParameter name="&#x22;kwargs&#x22;" type="&#x22;Any&#x22;" value="&#x22;{}&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;collections.abc.Callable&#x22;">
        Callable\[..., Any]: The configured ingestion decorator.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_ingestion_assets&#x22;" type="&#x22;() -> list[Any]&#x22;">
      Lazily resolve and return registered ingestion assets.

      This function retrieves all ingestion assets that have been registered
      via the `@phlo_ingestion` decorator. Assets are collected in a
      global registry during module import.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        from phlo_dlt import get_ingestion_assets

        assets = get_ingestion_assets()
        for asset in assets:
            print(f"Asset: \{asset.key\}")
        ```
      </Callout>

      <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
        :func:`phlo_dlt.decorator.get_ingestion_assets`: The actual implementation.
        :func:`phlo_ingestion`: Decorator that registers assets.
      </Callout>

      <PySourceCode>
        ````python
        def get_ingestion_assets() -> list[Any]:
            """Lazily resolve and return registered ingestion assets.

            This function retrieves all ingestion assets that have been registered
            via the ``@phlo_ingestion`` decorator. Assets are collected in a
            global registry during module import.

            Returns:
                list[Any]: List of registered asset specifications.

            Example:
                \```python
                from phlo_dlt import get_ingestion_assets

                assets = get_ingestion_assets()
                for asset in assets:
                    print(f"Asset: {asset.key}")
                \```

            See Also:
                :func:`phlo_dlt.decorator.get_ingestion_assets`: The actual implementation.
                :func:`phlo_ingestion`: Decorator that registers assets.

            """
            from phlo_dlt.decorator import get_ingestion_assets as _get_ingestion_assets

            return _get_ingestion_assets()
        ````
      </PySourceCode>

      <PyFunctionReturn type="&#x22;list&#x22;">
        list\[Any]: List of registered asset specifications.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>

  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/packages/phlo-dlt/phlo_dlt/executor&#x22;" title="&#x22;executor&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dlt/phlo_dlt/plugin&#x22;" title="&#x22;plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dlt/phlo_dlt/decorator&#x22;" title="&#x22;decorator&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dlt/phlo_dlt/cli_plugin&#x22;" title="&#x22;cli_plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dlt/phlo_dlt/cli_workflow&#x22;" title="&#x22;cli_workflow&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dlt/phlo_dlt/dlt_helpers&#x22;" title="&#x22;dlt_helpers&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dlt/phlo_dlt/scaffold&#x22;" title="&#x22;scaffold&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dlt/phlo_dlt/settings&#x22;" title="&#x22;settings&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dlt/phlo_dlt/pandera_checks&#x22;" title="&#x22;pandera_checks&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dlt/phlo_dlt/registry&#x22;" title="&#x22;registry&#x22;" />
    </Cards>
  </Tab>
</Tabs>

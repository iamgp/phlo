# cli_utils (/docs/python-reference/packages/phlo-iceberg/phlo_iceberg/cli_utils)



CLI helper utilities for Iceberg.

This module provides cached access to Iceberg catalog instances for use
in CLI commands. The caching ensures consistent catalog connections
across multiple CLI operations within the same process.

The primary use case is for Phlo CLI commands that need to interact
with Iceberg tables (listing, inspecting, creating, etc.).

Example:
CLI command using cached catalog::

from phlo\_iceberg.cli\_utils import get\_iceberg\_catalog

@click.command()
@click.argument("table\_name")
def inspect\_table(table\_name):

Reuses cached connection [#reuses-cached-connection]

catalog = get\_iceberg\_catalog(ref="main")
table = catalog.load\_table(table\_name)
print(f"Table: \{table.name}")
print(f"Schema: \{table.schema()}")

Note:
This module is separate from the main catalog module to avoid
circular dependencies between CLI utilities and core functionality.

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_iceberg_catalog&#x22;" type="&#x22;(ref='main')&#x22;">
      Get a cached Iceberg catalog instance for CLI operations.

      Uses LRU cache to provide consistent catalog connections across
      multiple CLI commands. The cache has no size limit (maxsize=None)
      since CLI processes are typically short-lived.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        Use in CLI commands::

        from phlo\_iceberg.cli\_utils import get\_iceberg\_catalog

        List tables [#list-tables]

        catalog = get\_iceberg\_catalog(ref="main")
        tables = catalog.list\_tables("raw")

        Later in same CLI session - reuses cached connection [#later-in-same-cli-session---reuses-cached-connection]

        catalog2 = get\_iceberg\_catalog(ref="main")
        assert catalog is catalog2  # Same instance
      </Callout>

      <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
        :func:`phlo_iceberg.catalog.get_catalog`: Core catalog function
        that this utility wraps.
      </Callout>

      <PySourceCode>
        ```python
        @lru_cache(maxsize=None)
        def get_iceberg_catalog(ref: str = "main"):
            """Get a cached Iceberg catalog instance for CLI operations.

            Uses LRU cache to provide consistent catalog connections across
            multiple CLI commands. The cache has no size limit (maxsize=None)
            since CLI processes are typically short-lived.

            Args:
                ref: Nessie branch or tag reference (default: ``main``).

            Returns:
                Catalog: PyIceberg catalog instance for the specified reference.

            Example:
                Use in CLI commands::

                    from phlo_iceberg.cli_utils import get_iceberg_catalog

                    # List tables
                    catalog = get_iceberg_catalog(ref="main")
                    tables = catalog.list_tables("raw")

                    # Later in same CLI session - reuses cached connection
                    catalog2 = get_iceberg_catalog(ref="main")
                    assert catalog is catalog2  # Same instance

            See Also:
                :func:`phlo_iceberg.catalog.get_catalog`: Core catalog function
                    that this utility wraps.

            """
            from phlo_iceberg.catalog import get_catalog

            return get_catalog(ref=ref)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;ref&#x22;" type="&#x22;str&#x22;" value="&#x22;'main'&#x22;">
          Nessie branch or tag reference (default: `main`).
        </PyParameter>
      </div>

      <PyFunctionReturn type="null">
        PyIceberg catalog instance for the specified reference.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>

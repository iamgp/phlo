# CatalogScanner (/docs/python-reference/core/phlo/capabilities/interfaces/CatalogScanner)



Protocol for catalog scanners used by metadata synchronization flows.

Functions [#functions]

<PyFunction name="&#x22;scan_all_tables&#x22;" type="&#x22;(self) -> dict[str, list[dict[str, Any]]]&#x22;">
  Return all discovered tables grouped by namespace.

  <PySourceCode>
    ```python
    def scan_all_tables(self) -> dict[str, list[dict[str, Any]]]:
        """Return all discovered tables grouped by namespace."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, list[dict[str, typing.Any]]]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_table_metadata&#x22;" type="&#x22;(self, namespace, table_name) -> dict[str, Any] | None&#x22;">
  Return normalized metadata for one discovered table.

  <PySourceCode>
    ```python
    def get_table_metadata(self, namespace: str, table_name: str) -> dict[str, Any] | None:
        """Return normalized metadata for one discovered table."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;namespace&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, typing.Any] | None&#x22;" />
</PyFunction>

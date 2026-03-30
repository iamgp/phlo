# TrinoNessieIcebergDevCatalogPlugin (/docs/python-reference/packages/phlo-nessie/phlo_nessie/adapters/trino/TrinoNessieIcebergDevCatalogPlugin)



Dev Trino catalog backed by the Nessie dev ref.

This plugin provides a separate catalog for Trino queries against the
'dev' branch in Nessie. Useful for development and testing without
affecting production data.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Plugin identity and description.
</PyAttribute>

<PyAttribute name="&#x22;targets&#x22;" type="&#x22;list[str]&#x22;" value="null">
  List of target systems (\['trino']).
</PyAttribute>

<PyAttribute name="&#x22;catalog_name&#x22;" type="&#x22;str&#x22;" value="null">
  Trino catalog name ('iceberg\_dev').
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_properties&#x22;" type="&#x22;(self) -> dict[str, str]&#x22;">
  Return Trino catalog configuration properties with dev prefix.

  <PySourceCode>
    ```python
    def get_properties(self) -> dict[str, str]:
        """Return Trino catalog configuration properties with dev prefix.

        Returns:
            dict[str, str]: Properties for Trino Iceberg connector,
                including 'iceberg.rest-catalog.prefix' set to 'dev'.

        """
        return _base_iceberg_catalog_properties(prefix="dev")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, str]: Properties for Trino Iceberg connector,
    including 'iceberg.rest-catalog.prefix' set to 'dev'.
  </PyFunctionReturn>
</PyFunction>

# TrinoNessieIcebergCatalogPlugin (/docs/python-reference/packages/phlo-nessie/phlo_nessie/adapters/trino/TrinoNessieIcebergCatalogPlugin)



Main Trino catalog backed by Nessie Iceberg REST.

This plugin provides the primary production catalog for Trino queries
against Iceberg tables stored in Nessie. Uses the default Nessie reference
(usually 'main').

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Plugin identity and description.
</PyAttribute>

<PyAttribute name="&#x22;targets&#x22;" type="&#x22;list[str]&#x22;" value="null">
  List of target systems (\['trino']).
</PyAttribute>

<PyAttribute name="&#x22;catalog_name&#x22;" type="&#x22;str&#x22;" value="null">
  Trino catalog name ('iceberg').
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_properties&#x22;" type="&#x22;(self) -> dict[str, str]&#x22;">
  Return Trino catalog configuration properties.

  <PySourceCode>
    ```python
    def get_properties(self) -> dict[str, str]:
        """Return Trino catalog configuration properties.

        Returns:
            dict[str, str]: Properties for Trino Iceberg connector.

        """
        return _base_iceberg_catalog_properties()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, str]: Properties for Trino Iceberg connector.
  </PyFunctionReturn>
</PyFunction>

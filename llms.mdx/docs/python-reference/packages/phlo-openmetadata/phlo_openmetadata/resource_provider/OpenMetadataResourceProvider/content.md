# OpenMetadataResourceProvider (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/resource_provider/OpenMetadataResourceProvider)



Expose OpenMetadata as a metadata catalog capability.

This plugin registers OpenMetadataCatalogProvider with the phlo
capability system, allowing other components to publish metadata
to OpenMetadata without direct coupling.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  PluginMetadata containing plugin identification information.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_resources&#x22;" type="&#x22;(self) -> list&#x22;">
  OpenMetadata does not expose raw resources in this slice.

  <PySourceCode>
    ```python
    def get_resources(self) -> list:
        """OpenMetadata does not expose raw resources in this slice.

        Returns:
            list: Empty list as OpenMetadata is a catalog capability only.

        """
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    Empty list as OpenMetadata is a catalog capability only.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_metadata_catalogs&#x22;" type="&#x22;(self) -> list[MetadataCatalogSpec]&#x22;">
  Expose OpenMetadata as a metadata catalog capability.

  <PySourceCode>
    ```python
    def get_metadata_catalogs(self) -> list[MetadataCatalogSpec]:
        """Expose OpenMetadata as a metadata catalog capability.

        Returns:
            list[MetadataCatalogSpec]: List containing MetadataCatalogSpec
                wrapping OpenMetadataCatalogProvider.

        """
        return [
            MetadataCatalogSpec(
                name="openmetadata",
                provider=OpenMetadataCatalogProvider(),
            )
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[MetadataCatalogSpec]: List containing MetadataCatalogSpec
    wrapping OpenMetadataCatalogProvider.
  </PyFunctionReturn>
</PyFunction>

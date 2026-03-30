# NessieResourceProvider (/docs/python-reference/packages/phlo-nessie/phlo_nessie/resource_provider/NessieResourceProvider)



Expose Nessie as a capability-native catalog/versioning provider.

This plugin registers Nessie with the Phlo capability system, exposing
it as a catalog, catalog scanner, and versioning resource for other
components to discover and use.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Plugin identity and description.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_resources&#x22;" type="&#x22;(self) -> list[ResourceSpec]&#x22;">
  Expose the raw Nessie client as a runtime resource.

  <PySourceCode>
    ```python
    def get_resources(self) -> list[ResourceSpec]:
        """Expose the raw Nessie client as a runtime resource.

        Returns:
            list[ResourceSpec]: Nessie catalog versioning resource.

        """
        return [ResourceSpec(name="catalog_versioning", resource=NessieResource())]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[ResourceSpec]: Nessie catalog versioning resource.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_catalogs&#x22;" type="&#x22;(self) -> list[CatalogSpec]&#x22;">
  Expose Nessie as a catalog capability.

  <PySourceCode>
    ```python
    def get_catalogs(self) -> list[CatalogSpec]:
        """Expose Nessie as a catalog capability.

        Returns:
            list[CatalogSpec]: Nessie catalog specification with
                capability support flags (refs, snapshots, promote).

        """
        support = CapabilitySupport(
            supports_refs=True,
            supports_snapshots=False,
            supports_promote=True,
        )
        return [
            CatalogSpec(
                name="nessie",
                provider=NessieResource(),
                support=support,
            )
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[CatalogSpec]: Nessie catalog specification with
    capability support flags (refs, snapshots, promote).
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_catalog_scanners&#x22;" type="&#x22;(self) -> list[CatalogScannerSpec]&#x22;">
  Expose Nessie table scanning as a capability.

  <PySourceCode>
    ```python
    def get_catalog_scanners(self) -> list[CatalogScannerSpec]:
        """Expose Nessie table scanning as a capability.

        Returns:
            list[CatalogScannerSpec]: Nessie table scanner specification.

        """
        return [
            CatalogScannerSpec(
                name="nessie",
                provider=NessieTableScanner.from_config(),
                support=CapabilitySupport(),
            )
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[CatalogScannerSpec]: Nessie table scanner specification.
  </PyFunctionReturn>
</PyFunction>

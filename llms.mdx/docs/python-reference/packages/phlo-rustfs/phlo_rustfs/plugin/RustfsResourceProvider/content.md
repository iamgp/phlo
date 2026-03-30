# RustfsResourceProvider (/docs/python-reference/packages/phlo-rustfs/phlo_rustfs/plugin/RustfsResourceProvider)



Resource provider plugin for RustFS capabilities.

Implements the ResourceProviderPlugin interface to expose RustFS object
storage capabilities to the Phlo resource registry. This plugin allows
other components to discover and connect to RustFS S3 storage.

The provider exposes a single object store capability named "rustfs"
that can be used for S3-compatible storage operations.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for the RustFS resource provider.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_resources&#x22;" type="&#x22;(self) -> list[ResourceSpec]&#x22;">
  Return resource specs exposed by this provider.

  Currently returns an empty list as RustFS does not expose any
  generic resources. Object store capabilities are exposed via
  get\_object\_stores instead.

  <PySourceCode>
    ```python
    def get_resources(self) -> list[ResourceSpec]:
        """Return resource specs exposed by this provider.

        Currently returns an empty list as RustFS does not expose any
        generic resources. Object store capabilities are exposed via
        get_object_stores instead.

        Returns:
            Empty list of ResourceSpec objects.

        """
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    Empty list of ResourceSpec objects.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_object_stores&#x22;" type="&#x22;(self) -> list[ObjectStoreSpec]&#x22;">
  Return object-store capability specs exposed by this provider.

  Returns a list containing a single ObjectStoreSpec for the RustFS
  S3-compatible storage. The spec includes metadata about the storage
  type and endpoint URL.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > provider = RustfsResourceProvider()
    > > > stores = provider.get\_object\_stores()
    > > > len(stores)
    > > > 1
    > > > stores\[0].name
    > > > "rustfs"
  </Callout>

  <PySourceCode>
    ```python
    def get_object_stores(self) -> list[ObjectStoreSpec]:
        """Return object-store capability specs exposed by this provider.

        Returns a list containing a single ObjectStoreSpec for the RustFS
        S3-compatible storage. The spec includes metadata about the storage
        type and endpoint URL.

        Returns:
            List containing one ObjectStoreSpec for the "rustfs" object store.

        Example:
            >>> provider = RustfsResourceProvider()
            >>> stores = provider.get_object_stores()
            >>> len(stores)
            1
            >>> stores[0].name
            "rustfs"

        """
        provider = RustfsObjectStoreProvider()
        return [
            ObjectStoreSpec(
                name="rustfs",
                provider=provider,
                metadata={
                    "storage_system": "s3",
                    "type": "s3",
                    "endpoint": provider.to_sling_connection()["endpoint"],
                },
            )
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List containing one ObjectStoreSpec for the "rustfs" object store.
  </PyFunctionReturn>
</PyFunction>

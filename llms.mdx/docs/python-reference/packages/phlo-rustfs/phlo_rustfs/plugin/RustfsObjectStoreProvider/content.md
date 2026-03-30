# RustfsObjectStoreProvider (/docs/python-reference/packages/phlo-rustfs/phlo_rustfs/plugin/RustfsObjectStoreProvider)



Capability provider for RustFS-backed object storage.

Provides S3-compatible connection details for RustFS storage. This class
implements the object store capability interface, allowing other components
to obtain S3 connection parameters for integrating with RustFS.

The provider reads configuration from RustfsSettings and formats it
into S3-compatible dictionaries suitable for Sling and other S3 clients.

Functions [#functions]

<PyFunction name="&#x22;to_sling_connection&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Return a Sling-compatible S3 connection definition.

  Constructs an S3 connection dictionary formatted for use with Sling.
  Includes endpoint URL, credentials, and region information read from
  the cached RustfsSettings.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > provider = RustfsObjectStoreProvider()
    > > > conn = provider.to\_sling\_connection()
    > > > print(conn\["type"])
    > > > "s3"
  </Callout>

  <PySourceCode>
    ```python
    def to_sling_connection(self) -> dict[str, Any]:
        """Return a Sling-compatible S3 connection definition.

        Constructs an S3 connection dictionary formatted for use with Sling.
        Includes endpoint URL, credentials, and region information read from
        the cached RustfsSettings.

        Returns:
            Dictionary with keys: type, endpoint, access_key_id,
            secret_access_key, and region.

        Example:
            >>> provider = RustfsObjectStoreProvider()
            >>> conn = provider.to_sling_connection()
            >>> print(conn["type"])
            "s3"

        """
        from phlo_rustfs.settings import get_settings

        settings = get_settings()
        return {
            "type": "s3",
            "endpoint": f"http://{settings.rustfs_endpoint()}",
            "access_key_id": settings.rustfs_access_key,
            "secret_access_key": settings.rustfs_secret_key,
            "region": settings.s3_region,
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary with keys: type, endpoint, access\_key\_id,
  </PyFunctionReturn>
</PyFunction>

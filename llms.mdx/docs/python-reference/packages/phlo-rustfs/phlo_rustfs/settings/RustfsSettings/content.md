# RustfsSettings (/docs/python-reference/packages/phlo-rustfs/phlo_rustfs/settings/RustfsSettings)



RustFS S3-compatible storage configuration.

Pydantic configuration model for RustFS connectivity. Settings are loaded
from environment variables with sensible defaults for local development.

Attributes [#attributes]

<PyAttribute name="&#x22;rustfs_host&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='rustfs', description='RustFS service hostname')&#x22;">
  Service hostname for RustFS container (default: "rustfs").
</PyAttribute>

<PyAttribute name="&#x22;rustfs_access_key&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='rustfsadmin', description='RustFS access key')&#x22;">
  Access key for S3 API authentication (default: "rustfsadmin").
</PyAttribute>

<PyAttribute name="&#x22;rustfs_secret_key&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='rustfsadmin', description='RustFS secret key')&#x22;">
  Secret key for S3 API authentication (default: "rustfsadmin").
</PyAttribute>

<PyAttribute name="&#x22;rustfs_api_port&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=9000, description='RustFS S3 API port')&#x22;">
  Port for S3-compatible API endpoint (default: 9000).
</PyAttribute>

<PyAttribute name="&#x22;rustfs_console_port&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=9001, description='RustFS console port')&#x22;">
  Port for web management console (default: 9001).
</PyAttribute>

<PyAttribute name="&#x22;s3_region&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='us-east-1', description='S3 region')&#x22;">
  AWS-style region identifier (default: "us-east-1").
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;model_post_init&#x22;" type="&#x22;(self, __context) -> None&#x22;">
  Resolve host and port after model initialization.

  Applies host resolution logic using phlo.config.network.resolve\_host.
  Updates rustfs\_host and rustfs\_api\_port based on environment variables
  and DNS resolution. Uses object.**setattr** to bypass Pydantic's
  immutability protections for post-initialization modifications.

  <PySourceCode>
    ```python
    def model_post_init(self, __context: Any) -> None:
        """Resolve host and port after model initialization.

        Applies host resolution logic using phlo.config.network.resolve_host.
        Updates rustfs_host and rustfs_api_port based on environment variables
        and DNS resolution. Uses object.__setattr__ to bypass Pydantic's
        immutability protections for post-initialization modifications.

        Args:
            __context: Pydantic internal context (unused).

        """
        host, port = resolve_host(
            self.rustfs_host, self.rustfs_api_port, port_env_var="RUSTFS_API_PORT"
        )
        object.__setattr__(self, "rustfs_host", host)
        object.__setattr__(self, "rustfs_api_port", port)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;__context&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Pydantic internal context (unused).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;rustfs_endpoint&#x22;" type="&#x22;(self) -> str&#x22;">
  Return host:port endpoint for RustFS S3 API.

  Formats the resolved host and API port into a standard endpoint
  string suitable for S3 SDK configuration.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > settings = RustfsSettings()
    > > > settings.rustfs\_endpoint()
    > > > "localhost:9000"
  </Callout>

  <PySourceCode>
    ```python
    def rustfs_endpoint(self) -> str:
        """Return host:port endpoint for RustFS S3 API.

        Formats the resolved host and API port into a standard endpoint
        string suitable for S3 SDK configuration.

        Returns:
            String in format "host:port" for the S3 API endpoint.

        Example:
            >>> settings = RustfsSettings()
            >>> settings.rustfs_endpoint()
            "localhost:9000"

        """
        return f"{self.rustfs_host}:{self.rustfs_api_port}"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    String in format "host:port" for the S3 API endpoint.
  </PyFunctionReturn>
</PyFunction>

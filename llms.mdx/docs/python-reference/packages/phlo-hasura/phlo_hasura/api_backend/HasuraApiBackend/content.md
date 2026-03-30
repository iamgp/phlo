# HasuraApiBackend (/docs/python-reference/packages/phlo-hasura/phlo_hasura/api_backend/HasuraApiBackend)



Expose Hasura through the neutral API backend capability.

This class wraps the Hasura GraphQL engine to provide a standardized
API backend interface. It handles health checks and returns metadata
describing the available endpoints.

Attributes [#attributes]

<PyAttribute name="&#x22;_client&#x22;" type="null" value="&#x22;client or HasuraClient()&#x22;">
  The internal HasuraClient instance for making API calls.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, client=None) -> None&#x22;">
  Initialize the Hasura API backend.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > backend = HasuraApiBackend()
    > > > custom\_backend = HasuraApiBackend(HasuraClient(
    > > > ...     hasura\_url="[http://custom:8080](http://custom:8080)"
    > > > ... ))
  </Callout>

  <PySourceCode>
    ```python
    def __init__(self, client: HasuraClient | None = None) -> None:
        """Initialize the Hasura API backend.

        Args:
            client: HasuraClient instance. If not provided, a new
                HasuraClient will be instantiated with default settings.

        Example:
            >>> backend = HasuraApiBackend()
            >>> custom_backend = HasuraApiBackend(HasuraClient(
            ...     hasura_url="http://custom:8080"
            ... ))

        """
        self._client = client or HasuraClient()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;client&#x22;" type="&#x22;HasuraClient | None&#x22;" value="&#x22;None&#x22;">
      HasuraClient instance. If not provided, a new
      HasuraClient will be instantiated with default settings.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;health_check&#x22;" type="&#x22;(self) -> bool&#x22;">
  Check whether the Hasura health endpoint responds successfully.

  Makes a GET request to the /healthz endpoint to verify that
  Hasura is running and responsive.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > backend = HasuraApiBackend()
    > > > if backend.health\_check():
    > > > ...     print("Hasura is up and running")
    > > > ... else:
    > > > ...     print("Hasura is not responding")
  </Callout>

  <PySourceCode>
    ```python
    def health_check(self) -> bool:
        """Check whether the Hasura health endpoint responds successfully.

        Makes a GET request to the /healthz endpoint to verify that
        Hasura is running and responsive.

        Returns:
            True if the health endpoint returns 200 or 204, False otherwise.

        Raises:
            No exceptions are raised; all errors are caught and return False.

        Example:
            >>> backend = HasuraApiBackend()
            >>> if backend.health_check():
            ...     print("Hasura is up and running")
            ... else:
            ...     print("Hasura is not responding")

        """
        try:
            response = requests.get(f"{self._client.hasura_url}/healthz", timeout=5)
        except requests.RequestException:
            return False
        return response.status_code in {200, 204}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    True if the health endpoint returns 200 or 204, False otherwise.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;describe&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Return a stable description of the Hasura backend surface.

  Returns metadata describing the Hasura GraphQL API endpoints,
  including the base URL, health check path, and available
  public endpoints.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > backend = HasuraApiBackend()
    > > > desc = backend.describe()
    > > > print(desc\["service\_name"])
    > > > "hasura"
    > > > for ep in desc\["public\_endpoints"]:
    > > > ...     print(f"\{ep\['name']}: \{ep\['url']}")
  </Callout>

  <PySourceCode>
    ```python
    def describe(self) -> dict[str, Any]:
        """Return a stable description of the Hasura backend surface.

        Returns metadata describing the Hasura GraphQL API endpoints,
        including the base URL, health check path, and available
        public endpoints.

        Returns:
            Dictionary containing:
                - service_name: The service identifier ("hasura")
                - backend_kind: The type of backend ("graphql")
                - default_path: Default GraphQL endpoint path
                - health_path: Health check endpoint path
                - metadata_path: Metadata API endpoint path
                - base_url: Base URL for all endpoints
                - public_endpoints: List of available endpoints with names and URLs

        Example:
            >>> backend = HasuraApiBackend()
            >>> desc = backend.describe()
            >>> print(desc["service_name"])
            "hasura"
            >>> for ep in desc["public_endpoints"]:
            ...     print(f"{ep['name']}: {ep['url']}")

        """
        base_url = self._client.hasura_url.rstrip("/")
        return {
            "service_name": "hasura",
            "backend_kind": "graphql",
            "default_path": "/v1/graphql",
            "health_path": "/healthz",
            "metadata_path": "/v1/metadata",
            "base_url": base_url,
            "public_endpoints": [
                {"name": "graphql", "url": f"{base_url}/v1/graphql"},
                {"name": "metadata", "url": f"{base_url}/v1/metadata"},
                {"name": "health", "url": f"{base_url}/healthz"},
            ],
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary containing:

    * service\_name: The service identifier ("hasura")
    * backend\_kind: The type of backend ("graphql")
    * default\_path: Default GraphQL endpoint path
    * health\_path: Health check endpoint path
    * metadata\_path: Metadata API endpoint path
    * base\_url: Base URL for all endpoints
    * public\_endpoints: List of available endpoints with names and URLs
  </PyFunctionReturn>
</PyFunction>

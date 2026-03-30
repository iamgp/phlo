# client (/docs/python-reference/packages/phlo-hasura/phlo_hasura/client)



Hasura Metadata API client for table tracking and permission management.

This module provides the HasuraClient class for interacting with Hasura's
Metadata API v1. It handles table tracking, permission management, relationship
creation, and metadata import/export operations.

The client automatically resolves URLs and handles authentication via the
admin secret. All API calls include proper error handling and logging.

Example:

> > > from phlo\_hasura.client import HasuraClient
> > > client = HasuraClient()
> > > client.track\_table("api", "orders")
> > > client.create\_select\_permission("api", "orders", "anon")

Environment Variables:
HASURA\_ADMIN\_SECRET: Admin secret for Hasura authentication.
HASURA\_PORT: Port override for Hasura URL resolution.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;HasuraClient&#x22;" href="&#x22;/docs/python-reference/packages/phlo-hasura/phlo_hasura/client/HasuraClient&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_resolve_hasura_url&#x22;" type="&#x22;(url) -> str&#x22;">
      Resolve Hasura URL, handling Docker hostname resolution.

      Uses the phlo network resolver to handle Docker-internal hostnames
      and port overrides from environment variables.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > \_resolve\_hasura\_url("[http://hasura:8080](http://hasura:8080)")
        > > > '[http://localhost:8080](http://localhost:8080)'  # When running outside Docker
      </Callout>

      <PySourceCode>
        ```python
        def _resolve_hasura_url(url: str) -> str:
            """Resolve Hasura URL, handling Docker hostname resolution.

            Uses the phlo network resolver to handle Docker-internal hostnames
            and port overrides from environment variables.

            Args:
                url: The raw URL to resolve (may contain Docker hostnames like 'hasura').

            Returns:
                The resolved URL with proper hostname and port.

            Example:
                >>> _resolve_hasura_url("http://hasura:8080")
                'http://localhost:8080'  # When running outside Docker

            """
            return resolve_url(url, port_env_var="HASURA_PORT")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;url&#x22;" type="&#x22;str&#x22;" value="undefined">
          The raw URL to resolve (may contain Docker hostnames like 'hasura').
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        The resolved URL with proper hostname and port.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>

# HasuraResourceProvider (/docs/python-reference/packages/phlo-hasura/phlo_hasura/resource_provider/HasuraResourceProvider)



Expose Hasura as a swappable API backend capability.

This provider integrates Hasura with the Phlo capability system,
allowing it to be discovered and used as a GraphQL API backend.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for capability discovery.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > provider = HasuraResourceProvider()
    > > > meta = provider.metadata
    > > > print(meta.name, meta.tags)
    > > > hasura \['api', 'graphql', 'bi']
  </Callout>
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_resources&#x22;" type="&#x22;(self) -> list&#x22;">
  Return list of raw resources exposed by this provider.

  This provider does not expose any raw resources directly.
  Resources are accessed through the API backend interface.

  <PySourceCode>
    ```python
    def get_resources(self) -> list:
        """Return list of raw resources exposed by this provider.

        This provider does not expose any raw resources directly.
        Resources are accessed through the API backend interface.

        Returns:
            Empty list as no raw resources are provided.

        """
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    Empty list as no raw resources are provided.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_api_backends&#x22;" type="&#x22;(self) -> list[ApiBackendSpec]&#x22;">
  Expose Hasura as an API backend capability.

  Returns Hasura API backend specifications that can be used
  by other components requiring a GraphQL API backend.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > provider = HasuraResourceProvider()
    > > > backends = provider.get\_api\_backends()
    > > > backends\[0].name
    > > > 'hasura'
    > > > backends\[0].metadata\['backend\_kind']
    > > > 'graphql'
  </Callout>

  <PySourceCode>
    ```python
    def get_api_backends(self) -> list[ApiBackendSpec]:
        """Expose Hasura as an API backend capability.

        Returns Hasura API backend specifications that can be used
        by other components requiring a GraphQL API backend.

        Returns:
            List containing the Hasura API backend specification with
            name, provider instance, and metadata.

        Example:
            >>> provider = HasuraResourceProvider()
            >>> backends = provider.get_api_backends()
            >>> backends[0].name
            'hasura'
            >>> backends[0].metadata['backend_kind']
            'graphql'

        """
        return [
            ApiBackendSpec(
                name="hasura",
                provider=HasuraApiBackend(),
                metadata={
                    "backend_kind": "graphql",
                    "service_name": "hasura",
                    "category": "api",
                },
            )
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List containing the Hasura API backend specification with
  </PyFunctionReturn>
</PyFunction>

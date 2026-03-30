# TrinoResourceProvider (/docs/python-reference/packages/phlo-trino/phlo_trino/plugin/TrinoResourceProvider)



Resource provider plugin for Trino.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for Trino resource registration.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_resources&#x22;" type="&#x22;(self) -> list[ResourceSpec]&#x22;">
  Return Trino resources exposed by this plugin.

  <PySourceCode>
    ```python
    def get_resources(self) -> list[ResourceSpec]:
        """Return Trino resources exposed by this plugin.

        Returns:
            Resource specifications for Trino integrations.

        """
        return [ResourceSpec(name="trino", resource=TrinoResource())]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    Resource specifications for Trino integrations.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_query_engines&#x22;" type="&#x22;(self) -> list[QueryEngineSpec]&#x22;">
  Return Trino query-engine capability specs.

  <PySourceCode>
    ```python
    def get_query_engines(self) -> list[QueryEngineSpec]:
        """Return Trino query-engine capability specs.

        Returns:
            Query engine capability specifications for Trino.

        """
        return [
            QueryEngineSpec(
                name="trino",
                provider=TrinoResource(),
                metadata={
                    "host": get_trino_settings().trino_host,
                    "port": get_trino_settings().trino_port,
                    "default_catalog": get_trino_settings().trino_catalog,
                    "default_ref": get_trino_settings().trino_default_ref,
                    "service_type": "Trino",
                    "sqlalchemy_uri_template": "trino://{host}:{port}/{default_catalog}",
                },
                support=TRINO_QUERY_ENGINE_SUPPORT,
            )
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    Query engine capability specifications for Trino.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_governance_backends&#x22;" type="&#x22;(self) -> list[GovernanceBackendSpec]&#x22;">
  Return Trino governance backend specs.

  <PySourceCode>
    ```python
    def get_governance_backends(self) -> list[GovernanceBackendSpec]:
        """Return Trino governance backend specs.

        Returns:
            Governance backend specifications for Trino SQL grants.

        """
        return [
            GovernanceBackendSpec(
                name="trino",
                provider=TrinoGovernanceBackend(),
                support=CapabilitySupport(),
            )
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    Governance backend specifications for Trino SQL grants.
  </PyFunctionReturn>
</PyFunction>

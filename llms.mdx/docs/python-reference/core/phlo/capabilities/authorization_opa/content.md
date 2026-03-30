# authorization_opa (/docs/python-reference/core/phlo/capabilities/authorization_opa)



External OPA-backed authorization policy provider.

This is an example external provider that uses Open Policy Agent (OPA) as the
policy decision point. It implements the same AuthorizationPolicyBackend contract
as the built-in RBAC provider, enabling parity and easy migration.

Usage:

1. Start OPA: docker run -p 8181:8181 openpolicyagent/opa run --server
2. Configure PHLO\_OPA\_URL=[http://localhost:8181](http://localhost:8181) in .phlo/.env
3. Register this provider via plugin or direct registration

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;OPAAuthorizationPolicyBackend&#x22;" href="&#x22;/docs/python-reference/core/phlo/capabilities/authorization_opa/OPAAuthorizationPolicyBackend&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;create_opa_provider&#x22;" type="&#x22;(opa_url=None, opa_policy_package='phlo.authz') -> tuple[OPAAuthorizationPolicyBackend, CapabilitySupport]&#x22;">
      Factory function to create an OPA provider with support metadata.

      <PySourceCode>
        ```python
        def create_opa_provider(
            opa_url: str | None = None,
            opa_policy_package: str = "phlo.authz",
        ) -> tuple[OPAAuthorizationPolicyBackend, CapabilitySupport]:
            """Factory function to create an OPA provider with support metadata.

            Args:
                opa_url: URL of the OPA server. Defaults to http://localhost:8181
                opa_policy_package: OPA policy package path. Defaults to phlo.authz

            Returns:
                Tuple of (provider, support_metadata)
            """
            provider = OPAAuthorizationPolicyBackend(
                opa_url=opa_url,
                opa_policy_package=opa_policy_package,
            )
            support = CapabilitySupport(
                supports_permissions=True,
                supports_attributes=True,
            )
            return provider, support
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;opa_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          URL of the OPA server. Defaults to [http://localhost:8181](http://localhost:8181)
        </PyParameter>

        <PyParameter name="&#x22;opa_policy_package&#x22;" type="&#x22;str&#x22;" value="&#x22;'phlo.authz'&#x22;">
          OPA policy package path. Defaults to phlo.authz
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;tuple&#x22;">
        Tuple of (provider, support\_metadata)
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>

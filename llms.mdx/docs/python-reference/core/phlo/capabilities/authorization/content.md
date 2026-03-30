# authorization (/docs/python-reference/core/phlo/capabilities/authorization)



Default authorization policy backend capability provider.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PolicyRule&#x22;" href="&#x22;/docs/python-reference/core/phlo/capabilities/authorization/PolicyRule&#x22;" />

      <Card title="&#x22;DefaultAuthorizationPolicyBackend&#x22;" href="&#x22;/docs/python-reference/core/phlo/capabilities/authorization/DefaultAuthorizationPolicyBackend&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;register_default_capability_providers&#x22;" type="&#x22;() -> None&#x22;">
      Register the default authorization policy backend provider.

      <PySourceCode>
        ```python
        def register_default_capability_providers() -> None:
            """Register the default authorization policy backend provider."""
            register_authorization_policy_backend(
                AuthorizationPolicyBackendSpec(
                    name="default",
                    provider=DefaultAuthorizationPolicyBackend(),
                    metadata={
                        "policy_format": "rbac",
                        "default_policies": [],
                    },
                    support=CapabilitySupport(
                        supports_permissions=True,
                        supports_attributes=False,
                    ),
                )
            )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>

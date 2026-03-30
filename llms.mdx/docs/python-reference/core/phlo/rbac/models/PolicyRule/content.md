# PolicyRule (/docs/python-reference/core/phlo/rbac/models/PolicyRule)



A single policy rule.

Attributes [#attributes]

<PyAttribute name="&#x22;policy_id&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;effect&#x22;" type="&#x22;PolicyEffect&#x22;" value="null" />

<PyAttribute name="&#x22;principal_roles&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />

<PyAttribute name="&#x22;principal_attributes&#x22;" type="&#x22;Mapping[str, str]&#x22;" value="null" />

<PyAttribute name="&#x22;action&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;resource_type&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;resource_id_pattern&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;resource_attributes&#x22;" type="&#x22;Mapping[str, str]&#x22;" value="null" />

Functions [#functions]

<PyFunction name="&#x22;from_dict&#x22;" type="&#x22;(cls, data) -> PolicyRule&#x22;">
  Parse a policy rule from a dictionary.

  <PySourceCode>
    ```python
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PolicyRule:
        """Parse a policy rule from a dictionary."""
        effect = PolicyEffect(data.get("effect", "deny"))
        principal = data.get("principal", {})
        resource = data.get("resource", {})

        return cls(
            policy_id=data["policy_id"],
            effect=effect,
            principal_roles=tuple(principal.get("roles", [])),
            principal_attributes=principal.get("attributes", {}),
            action=data.get("action", "*"),
            resource_type=resource.get("type", "*"),
            resource_id_pattern=resource.get("id_pattern", "*"),
            resource_attributes=resource.get("attributes", {}),
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;cls&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;data&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.rbac.models.PolicyRule&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, policy_id, effect, principal_roles, principal_attributes, action, resource_type, resource_id_pattern, resource_attributes) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;policy_id&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;effect&#x22;" type="&#x22;PolicyEffect&#x22;" value="null" />

    <PyParameter name="&#x22;principal_roles&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />

    <PyParameter name="&#x22;principal_attributes&#x22;" type="&#x22;Mapping[str, str]&#x22;" value="null" />

    <PyParameter name="&#x22;action&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;resource_type&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;resource_id_pattern&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;resource_attributes&#x22;" type="&#x22;Mapping[str, str]&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

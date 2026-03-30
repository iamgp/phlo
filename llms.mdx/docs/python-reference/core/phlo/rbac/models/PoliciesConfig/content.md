# PoliciesConfig (/docs/python-reference/core/phlo/rbac/models/PoliciesConfig)



Canonical policies configuration (policies.yaml).

Attributes [#attributes]

<PyAttribute name="&#x22;version&#x22;" type="&#x22;int&#x22;" value="null" />

<PyAttribute name="&#x22;policies&#x22;" type="&#x22;tuple[PolicyRule, ...]&#x22;" value="null" />

Functions [#functions]

<PyFunction name="&#x22;from_dict&#x22;" type="&#x22;(cls, data) -> PoliciesConfig&#x22;">
  Parse policies configuration from a dictionary.

  <PySourceCode>
    ```python
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PoliciesConfig:
        """Parse policies configuration from a dictionary."""
        version = data.get("version", 1)
        policies_data = data.get("policies", [])

        policies = tuple(PolicyRule.from_dict(p) for p in policies_data)
        return cls(version=version, policies=policies)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;cls&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;data&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.rbac.models.PoliciesConfig&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_policies_for_action&#x22;" type="&#x22;(self, action, resource_type=None) -> list[PolicyRule]&#x22;">
  Get all policies matching an action and optionally resource type.

  <PySourceCode>
    ```python
    def get_policies_for_action(
        self,
        action: str,
        resource_type: str | None = None,
    ) -> list[PolicyRule]:
        """Get all policies matching an action and optionally resource type."""
        result = []
        for policy in self.policies:
            if self._action_matches(policy.action, action) and (
                resource_type is None or policy.resource_type == resource_type
            ):
                result.append(policy)
        return result
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;action&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;resource_type&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.rbac.models.PolicyRule]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_action_matches&#x22;" type="&#x22;(self, pattern, action) -> bool&#x22;">
  Check if action matches pattern (supports wildcards).

  <PySourceCode>
    ```python
    def _action_matches(self, pattern: str, action: str) -> bool:
        """Check if action matches pattern (supports wildcards)."""
        import fnmatch

        if pattern == "*":
            return True
        return fnmatch.fnmatch(action, pattern)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;pattern&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;action&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, version, policies) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;version&#x22;" type="&#x22;int&#x22;" value="null" />

    <PyParameter name="&#x22;policies&#x22;" type="&#x22;tuple[PolicyRule, ...]&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

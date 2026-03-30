# CanonicalRBAC (/docs/python-reference/core/phlo/rbac/models/CanonicalRBAC)



Combined canonical RBAC model.

Attributes [#attributes]

<PyAttribute name="&#x22;roles&#x22;" type="&#x22;RolesConfig&#x22;" value="null" />

<PyAttribute name="&#x22;policies&#x22;" type="&#x22;PoliciesConfig&#x22;" value="null" />

<PyAttribute name="&#x22;version_hash&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;from_configs&#x22;" type="&#x22;(cls, roles, policies) -> CanonicalRBAC&#x22;">
  Create a canonical RBAC model from configs.

  <PySourceCode>
    ```python
    @classmethod
    def from_configs(
        cls,
        roles: RolesConfig,
        policies: PoliciesConfig,
    ) -> CanonicalRBAC:
        """Create a canonical RBAC model from configs."""
        import hashlib
        import json

        content = json.dumps(
            {
                "roles_version": roles.version,
                "policies_version": policies.version,
                "roles": {k: {"inherits": v.inherits} for k, v in roles.roles.items()},
                "subjects": {
                    "services": dict(roles.subjects.services),
                    "users": dict(roles.subjects.users),
                },
                "policies": [
                    {
                        "policy_id": p.policy_id,
                        "effect": p.effect.value,
                        "principal_roles": p.principal_roles,
                        "principal_attributes": dict(p.principal_attributes),
                        "action": p.action,
                        "resource_type": p.resource_type,
                        "resource_id_pattern": p.resource_id_pattern,
                        "resource_attributes": dict(p.resource_attributes),
                    }
                    for p in policies.policies
                ],
            },
            sort_keys=True,
        )
        version_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return cls(roles=roles, policies=policies, version_hash=version_hash)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;cls&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;roles&#x22;" type="&#x22;RolesConfig&#x22;" value="null" />

    <PyParameter name="&#x22;policies&#x22;" type="&#x22;PoliciesConfig&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.rbac.models.CanonicalRBAC&#x22;" />
</PyFunction>

<PyFunction name="&#x22;validate&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  Validate the canonical RBAC model.

  <PySourceCode>
    ```python
    def validate(self) -> list[str]:
        """Validate the canonical RBAC model.

        Returns:
            List of validation errors (empty if valid).
        """
        errors: list[str] = []

        # Check that all principal roles exist
        for policy in self.policies.policies:
            for role in policy.principal_roles:
                if role not in self.roles.roles:
                    errors.append(f"Policy {policy.policy_id} references unknown role: {role}")

        # Check for cycles in role hierarchy
        for role_name in self.roles.roles:
            try:
                self.roles.expand_role_hierarchy(role_name)
            except ValueError as e:
                errors.append(str(e))

        return errors
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of validation errors (empty if valid).
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, roles, policies, version_hash=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;roles&#x22;" type="&#x22;RolesConfig&#x22;" value="null" />

    <PyParameter name="&#x22;policies&#x22;" type="&#x22;PoliciesConfig&#x22;" value="null" />

    <PyParameter name="&#x22;version_hash&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

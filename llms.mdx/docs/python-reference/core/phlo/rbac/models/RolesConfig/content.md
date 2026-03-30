# RolesConfig (/docs/python-reference/core/phlo/rbac/models/RolesConfig)



Canonical roles configuration (roles.yaml).

Attributes [#attributes]

<PyAttribute name="&#x22;version&#x22;" type="&#x22;int&#x22;" value="null" />

<PyAttribute name="&#x22;roles&#x22;" type="&#x22;Mapping[str, Role]&#x22;" value="null" />

<PyAttribute name="&#x22;subjects&#x22;" type="&#x22;SubjectAssignment&#x22;" value="&#x22;field(default_factory=SubjectAssignment)&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;from_dict&#x22;" type="&#x22;(cls, data) -> RolesConfig&#x22;">
  Parse roles configuration from a dictionary.

  <PySourceCode>
    ```python
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RolesConfig:
        """Parse roles configuration from a dictionary."""
        version = data.get("version", 1)
        roles_data = data.get("roles", {})
        subjects_data = data.get("subjects", {})

        roles: dict[str, Role] = {}
        for name, config in roles_data.items():
            inherits = tuple(config.get("inherits", []))
            description = config.get("description")
            roles[name] = Role(name=name, inherits=inherits, description=description)

        services = subjects_data.get("services", {})
        users = subjects_data.get("users", {})
        subjects = SubjectAssignment(
            services=dict(services),
            users=dict(users),
        )

        return cls(version=version, roles=roles, subjects=subjects)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;cls&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;data&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.rbac.models.RolesConfig&#x22;" />
</PyFunction>

<PyFunction name="&#x22;expand_role_hierarchy&#x22;" type="&#x22;(self, role_name) -> tuple[str, ...]&#x22;">
  Expand a role to include all inherited roles.

  <PySourceCode>
    ```python
    def expand_role_hierarchy(self, role_name: str) -> tuple[str, ...]:
        """Expand a role to include all inherited roles.

        Args:
            role_name: Name of the role to expand.

        Returns:
            Tuple of role names including the role and all inherited roles.

        Raises:
            ValueError: If the role does not exist or there's a cycle.
        """
        if role_name not in self.roles:
            raise ValueError(f"Unknown role: {role_name}")

        path: list[str] = []
        result_set: set[str] = set()

        def _expand(name: str) -> list[str]:
            if name in path:
                raise ValueError(f"Cycle detected in role hierarchy: {' -> '.join(path)} -> {name}")

            if name in result_set:
                return []

            if name not in self.roles:
                raise ValueError(f"Role '{name}' referenced in hierarchy does not exist")

            path.append(name)
            result_set.add(name)

            role = self.roles[name]
            result = [name]
            for parent in role.inherits:
                result.extend(_expand(parent))

            path.pop()
            return result

        return tuple(_expand(role_name))
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;role_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Name of the role to expand.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;tuple&#x22;">
    Tuple of role names including the role and all inherited roles.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_effective_roles&#x22;" type="&#x22;(self, role_name) -> frozenset[str]&#x22;">
  Get all effective roles including inherited ones.

  <PySourceCode>
    ```python
    def get_effective_roles(self, role_name: str) -> frozenset[str]:
        """Get all effective roles including inherited ones.

        Args:
            role_name: Name of the role.

        Returns:
            Frozenset of all role names in the hierarchy.
        """
        return frozenset(self.expand_role_hierarchy(role_name))
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;role_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Name of the role.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;frozenset&#x22;">
    Frozenset of all role names in the hierarchy.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, version, roles, subjects=SubjectAssignment()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;version&#x22;" type="&#x22;int&#x22;" value="null" />

    <PyParameter name="&#x22;roles&#x22;" type="&#x22;Mapping[str, Role]&#x22;" value="null" />

    <PyParameter name="&#x22;subjects&#x22;" type="&#x22;SubjectAssignment&#x22;" value="&#x22;SubjectAssignment()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

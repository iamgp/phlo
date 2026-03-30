# RoleHierarchy (/docs/python-reference/packages/phlo-hasura/phlo_hasura/permissions/RoleHierarchy)



Manages role hierarchy for permission inheritance.

Implements role-based permission inheritance where roles can inherit
permissions from other roles. For example, an "admin" role might
inherit all permissions from "analyst" and "anon" roles.

Attributes [#attributes]

<PyAttribute name="&#x22;hierarchy&#x22;" type="null" value="&#x22;hierarchy or {'admin': ['analyst', 'anon'], 'analyst': ['anon'], 'anon': []}&#x22;">
  Dictionary mapping roles to their inherited roles.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, hierarchy=None)&#x22;">
  Initialize role hierarchy.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > default = RoleHierarchy()
    > > > custom = RoleHierarchy(\{
    > > > ...     "superuser": \["admin", "user"],
    > > > ...     "admin": \["user"],
    > > > ...     "user": \[]
    > > > ... })
  </Callout>

  <PySourceCode>
    ```python
    def __init__(self, hierarchy: Optional[dict[str, list[str]]] = None):
        """Initialize role hierarchy.

        Args:
            hierarchy: Dictionary mapping roles to lists of inherited roles.
                Default hierarchy is:
                - admin -> [analyst, anon]
                - analyst -> [anon]
                - anon -> []

        Example:
            >>> default = RoleHierarchy()
            >>> custom = RoleHierarchy({
            ...     "superuser": ["admin", "user"],
            ...     "admin": ["user"],
            ...     "user": []
            ... })

        """
        self.hierarchy = hierarchy or {
            "admin": ["analyst", "anon"],
            "analyst": ["anon"],
            "anon": [],
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;hierarchy&#x22;" type="&#x22;Optional[dict[str, list[str]]]&#x22;" value="&#x22;None&#x22;">
      Dictionary mapping roles to lists of inherited roles.
      Default hierarchy is:

      * admin -> \[analyst, anon]
      * analyst -> \[anon]
      * anon -> \[]
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;get_inherited_roles&#x22;" type="&#x22;(self, role) -> list[str]&#x22;">
  Get all roles inherited by a role.

  Performs a depth-first traversal of the role hierarchy to find
  all roles that the specified role inherits from, including itself.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > hierarchy = RoleHierarchy()
    > > > hierarchy.get\_inherited\_roles("admin")
    > > > \['admin', 'analyst', 'anon']
    > > > hierarchy.get\_inherited\_roles("anon")
    > > > \['anon']
  </Callout>

  <PySourceCode>
    ```python
    def get_inherited_roles(self, role: str) -> list[str]:
        """Get all roles inherited by a role.

        Performs a depth-first traversal of the role hierarchy to find
        all roles that the specified role inherits from, including itself.

        Args:
            role: Role name to get inherited roles for.

        Returns:
            List of inherited role names including the input role itself.

        Example:
            >>> hierarchy = RoleHierarchy()
            >>> hierarchy.get_inherited_roles("admin")
            ['admin', 'analyst', 'anon']
            >>> hierarchy.get_inherited_roles("anon")
            ['anon']

        """
        inherited = [role]

        def visit(r: str) -> None:
            """Depth-first traversal that accumulates inherited roles."""
            for inherited_role in self.hierarchy.get(r, []):
                if inherited_role not in inherited:
                    inherited.append(inherited_role)
                    visit(inherited_role)

        visit(role)
        return inherited
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;role&#x22;" type="&#x22;str&#x22;" value="undefined">
      Role name to get inherited roles for.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of inherited role names including the input role itself.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;expand_permissions&#x22;" type="&#x22;(self, config) -> dict[str, Any]&#x22;">
  Expand permissions based on role hierarchy.

  Takes a permission configuration and expands it to include
  all inherited permissions. Higher-level roles receive the
  permissions of their inherited roles.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > config = \{
    > > > ...     "tables": \{
    > > > ...         "api.users": \{
    > > > ...             "select": \{"admin": \{"filter": \{}, "columns": \["\*"]}}
    > > > ...         }
    > > > ...     }
    > > > ... }
    > > > expanded = hierarchy.expand\_permissions(config)
    > > >
    > > > Now includes select permissions for analyst and anon too [#now-includes-select-permissions-for-analyst-and-anon-too]
  </Callout>

  <PySourceCode>
    ```python
    def expand_permissions(self, config: dict[str, Any]) -> dict[str, Any]:
        """Expand permissions based on role hierarchy.

        Takes a permission configuration and expands it to include
        all inherited permissions. Higher-level roles receive the
        permissions of their inherited roles.

        Args:
            config: Permission configuration dictionary with tables and roles.

        Returns:
            Expanded configuration with inherited permissions included.
            Each role in the hierarchy receives all permissions from the
            roles it inherits.

        Example:
            >>> config = {
            ...     "tables": {
            ...         "api.users": {
            ...             "select": {"admin": {"filter": {}, "columns": ["*"]}}
            ...         }
            ...     }
            ... }
            >>> expanded = hierarchy.expand_permissions(config)
            >>> # Now includes select permissions for analyst and anon too

        """
        expanded = {"tables": {}}

        for table_path, permissions in config.get("tables", {}).items():
            expanded["tables"][table_path] = {}

            for perm_type in ["select", "insert", "update", "delete"]:
                if perm_type not in permissions:
                    continue

                expanded["tables"][table_path][perm_type] = {}

                for role, perm_config in permissions[perm_type].items():
                    inherited_roles = self.get_inherited_roles(role)

                    for inherited_role in inherited_roles:
                        if inherited_role not in expanded["tables"][table_path][perm_type]:
                            expanded["tables"][table_path][perm_type][inherited_role] = (
                                perm_config.copy()
                            )

        return expanded
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;config&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Permission configuration dictionary with tables and roles.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Expanded configuration with inherited permissions included.
  </PyFunctionReturn>
</PyFunction>

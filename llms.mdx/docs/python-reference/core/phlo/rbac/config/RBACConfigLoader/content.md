# RBACConfigLoader (/docs/python-reference/core/phlo/rbac/config/RBACConfigLoader)



Loads and validates canonical RBAC configuration files.

Attributes [#attributes]

<PyAttribute name="&#x22;base_path&#x22;" type="&#x22;Path&#x22;" value="null">
  Return the base path for RBAC config files.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, base_path=None)&#x22;">
  Initialize the RBAC config loader.

  <PySourceCode>
    ```python
    def __init__(self, base_path: Path | None = None):
        """Initialize the RBAC config loader.

        Args:
            base_path: Base path for RBAC config files. Defaults to .phlo in cwd.
        """
        self._base_path = base_path or Path.cwd() / ".phlo"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;base_path&#x22;" type="&#x22;Path | None&#x22;" value="&#x22;None&#x22;">
      Base path for RBAC config files. Defaults to .phlo in cwd.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;load_roles&#x22;" type="&#x22;(self, path=None) -> RolesConfig&#x22;">
  Load roles configuration from YAML file.

  <PySourceCode>
    ```python
    def load_roles(self, path: Path | None = None) -> RolesConfig:
        """Load roles configuration from YAML file.

        Args:
            path: Path to roles.yaml. Defaults to base_path/authorization/roles.yaml.

        Returns:
            Parsed RolesConfig.

        Raises:
            FileNotFoundError: If the roles file doesn't exist.
            ValueError: If the roles file is invalid.
        """
        if path is None:
            path = self._base_path / "authorization" / "roles.yaml"

        if not path.exists():
            raise FileNotFoundError(f"Roles config not found: {path}")

        with path.open() as f:
            data = yaml.safe_load(f) or {}

        try:
            return RolesConfig.from_dict(data)
        except Exception as e:
            raise ValueError(f"Invalid roles config: {e}") from e
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;path&#x22;" type="&#x22;Path | None&#x22;" value="&#x22;None&#x22;">
      Path to roles.yaml. Defaults to base\_path/authorization/roles.yaml.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo.rbac.models.RolesConfig&#x22;">
    Parsed RolesConfig.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;load_policies&#x22;" type="&#x22;(self, path=None) -> PoliciesConfig&#x22;">
  Load policies configuration from YAML file.

  <PySourceCode>
    ```python
    def load_policies(self, path: Path | None = None) -> PoliciesConfig:
        """Load policies configuration from YAML file.

        Args:
            path: Path to policies.yaml. Defaults to base_path/authorization/policies.yaml.

        Returns:
            Parsed PoliciesConfig.

        Raises:
            FileNotFoundError: If the policies file doesn't exist.
            ValueError: If the policies file is invalid.
        """
        if path is None:
            path = self._base_path / "authorization" / "policies.yaml"

        if not path.exists():
            raise FileNotFoundError(f"Policies config not found: {path}")

        with path.open() as f:
            data = yaml.safe_load(f) or {}

        try:
            return PoliciesConfig.from_dict(data)
        except Exception as e:
            raise ValueError(f"Invalid policies config: {e}") from e
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;path&#x22;" type="&#x22;Path | None&#x22;" value="&#x22;None&#x22;">
      Path to policies.yaml. Defaults to base\_path/authorization/policies.yaml.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo.rbac.models.PoliciesConfig&#x22;">
    Parsed PoliciesConfig.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;load&#x22;" type="&#x22;(self) -> CanonicalRBAC&#x22;">
  Load the complete canonical RBAC configuration.

  <PySourceCode>
    ```python
    def load(self) -> CanonicalRBAC:
        """Load the complete canonical RBAC configuration.

        Returns:
            Combined CanonicalRBAC model.

        Raises:
            FileNotFoundError: If required config files don't exist.
            ValueError: If the configuration is invalid.
        """
        roles = self.load_roles()
        policies = self.load_policies()

        rbac = CanonicalRBAC.from_configs(roles, policies)

        errors = rbac.validate()
        if errors:
            raise ValueError(f"Invalid RBAC configuration: {errors}")

        return rbac
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.rbac.models.CanonicalRBAC&#x22;">
    Combined CanonicalRBAC model.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;validate&#x22;" type="&#x22;(self) -> tuple[bool, list[str]]&#x22;">
  Validate the RBAC configuration.

  <PySourceCode>
    ```python
    def validate(self) -> tuple[bool, list[str]]:
        """Validate the RBAC configuration.

        Returns:
            Tuple of (is_valid, error_messages).
        """
        try:
            rbac = self.load()
            errors = rbac.validate()
            return len(errors) == 0, errors
        except Exception as e:
            return False, [str(e)]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;tuple&#x22;">
    Tuple of (is\_valid, error\_messages).
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;compute_version_hash&#x22;" type="&#x22;(self) -> str&#x22;">
  Compute a hash of the current RBAC configuration.

  <PySourceCode>
    ```python
    def compute_version_hash(self) -> str:
        """Compute a hash of the current RBAC configuration.

        Returns:
            SHA256 hash of the configuration (truncated to 16 chars).

        Raises:
            FileNotFoundError: If required config files don't exist.
        """
        roles_path = self._base_path / "authorization" / "roles.yaml"
        policies_path = self._base_path / "authorization" / "policies.yaml"

        content: dict[str, Any] = {}
        if roles_path.exists():
            with roles_path.open() as f:
                content["roles"] = yaml.safe_load(f) or {}
        if policies_path.exists():
            with policies_path.open() as f:
                content["policies"] = yaml.safe_load(f) or {}

        json_content = json.dumps(content, sort_keys=True)
        return hashlib.sha256(json_content.encode()).hexdigest()[:16]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    SHA256 hash of the configuration (truncated to 16 chars).
  </PyFunctionReturn>
</PyFunction>

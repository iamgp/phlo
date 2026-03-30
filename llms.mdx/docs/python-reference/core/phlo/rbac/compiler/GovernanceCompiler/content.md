# GovernanceCompiler (/docs/python-reference/core/phlo/rbac/compiler/GovernanceCompiler)



Abstract base class for governance backend compilers.

Each compiler converts canonical RBAC policies into backend-native
artifacts (SQL grants, IAM policies, Hasura permissions, etc.).

Attributes [#attributes]

<PyAttribute name="&#x22;backend_name&#x22;" type="&#x22;str&#x22;" value="null">
  Return the name of the backend this compiler targets.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, backend=None)&#x22;">
  Initialize the compiler.

  <PySourceCode>
    ```python
    def __init__(self, backend: GovernanceBackend | None = None):
        """Initialize the compiler.

        Args:
            backend: Optional governance backend instance for apply/verify operations.
        """
        self._backend = backend
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;backend&#x22;" type="&#x22;GovernanceBackend | None&#x22;" value="&#x22;None&#x22;">
      Optional governance backend instance for apply/verify operations.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;supports_action&#x22;" type="&#x22;(self, action) -> bool&#x22;">
  Check if this compiler supports the given canonical action.

  <PySourceCode>
    ```python
    @abstractmethod
    def supports_action(self, action: str) -> bool:
        """Check if this compiler supports the given canonical action.

        Args:
            action: Canonical action name (e.g., "dataset.read").

        Returns:
            True if the compiler can handle this action.
        """
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;action&#x22;" type="&#x22;str&#x22;" value="undefined">
      Canonical action name (e.g., "dataset.read").
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    True if the compiler can handle this action.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;compile&#x22;" type="&#x22;(self, rbac, context) -> list[BackendArtifact]&#x22;">
  Compile canonical RBAC into backend artifacts.

  <PySourceCode>
    ```python
    @abstractmethod
    def compile(
        self,
        rbac: CanonicalRBAC,
        context: CompilerContext,
    ) -> list[BackendArtifact]:
        """Compile canonical RBAC into backend artifacts.

        Args:
            rbac: The canonical RBAC model.
            context: Compilation context.

        Returns:
            List of compiled artifacts representing desired backend state.
        """
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;rbac&#x22;" type="&#x22;CanonicalRBAC&#x22;" value="undefined">
      The canonical RBAC model.
    </PyParameter>

    <PyParameter name="&#x22;context&#x22;" type="&#x22;CompilerContext&#x22;" value="undefined">
      Compilation context.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of compiled artifacts representing desired backend state.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;plan&#x22;" type="&#x22;(self, rbac, context) -> SyncPlan&#x22;">
  Create a sync plan by comparing desired vs actual state.

  <PySourceCode>
    ```python
    @abstractmethod
    def plan(
        self,
        rbac: CanonicalRBAC,
        context: CompilerContext,
    ) -> SyncPlan:
        """Create a sync plan by comparing desired vs actual state.

        Args:
            rbac: The canonical RBAC model.
            context: Planning context.

        Returns:
            SyncPlan describing required changes.
        """
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;rbac&#x22;" type="&#x22;CanonicalRBAC&#x22;" value="undefined">
      The canonical RBAC model.
    </PyParameter>

    <PyParameter name="&#x22;context&#x22;" type="&#x22;CompilerContext&#x22;" value="undefined">
      Planning context.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo.rbac.models.SyncPlan&#x22;">
    SyncPlan describing required changes.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;apply&#x22;" type="&#x22;(self, plan, context) -> tuple[list[str], list[str]]&#x22;">
  Apply the planned changes to the backend.

  <PySourceCode>
    ```python
    @abstractmethod
    def apply(
        self,
        plan: SyncPlan,
        context: CompilerContext,
    ) -> tuple[list[str], list[str]]:
        """Apply the planned changes to the backend.

        Args:
            plan: The sync plan to apply.
            context: Apply context.

        Returns:
            Tuple of (success_ids, error_messages).
        """
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plan&#x22;" type="&#x22;SyncPlan&#x22;" value="undefined">
      The sync plan to apply.
    </PyParameter>

    <PyParameter name="&#x22;context&#x22;" type="&#x22;CompilerContext&#x22;" value="undefined">
      Apply context.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;tuple&#x22;">
    Tuple of (success\_ids, error\_messages).
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;verify&#x22;" type="&#x22;(self, rbac, context) -> VerifyResult&#x22;">
  Verify backend state matches desired state.

  <PySourceCode>
    ```python
    @abstractmethod
    def verify(
        self,
        rbac: CanonicalRBAC,
        context: CompilerContext,
    ) -> VerifyResult:
        """Verify backend state matches desired state.

        Args:
            rbac: The canonical RBAC model.
            context: Verification context.

        Returns:
            VerifyResult describing drift.
        """
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;rbac&#x22;" type="&#x22;CanonicalRBAC&#x22;" value="undefined">
      The canonical RBAC model.
    </PyParameter>

    <PyParameter name="&#x22;context&#x22;" type="&#x22;CompilerContext&#x22;" value="undefined">
      Verification context.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo.rbac.models.VerifyResult&#x22;">
    VerifyResult describing drift.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;revert&#x22;" type="&#x22;(self, revert_ids, context) -> tuple[list[str], list[str]]&#x22;">
  Revert previously applied changes.

  <PySourceCode>
    ```python
    @abstractmethod
    def revert(
        self,
        revert_ids: list[str],
        context: CompilerContext,
    ) -> tuple[list[str], list[str]]:
        """Revert previously applied changes.

        Args:
            revert_ids: List of revert IDs to undo.
            context: Revert context.

        Returns:
            Tuple of (success_ids, error_messages).
        """
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;revert_ids&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
      List of revert IDs to undo.
    </PyParameter>

    <PyParameter name="&#x22;context&#x22;" type="&#x22;CompilerContext&#x22;" value="undefined">
      Revert context.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;tuple&#x22;">
    Tuple of (success\_ids, error\_messages).
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;read_current_state&#x22;" type="&#x22;(self, context) -> list[BackendArtifact]&#x22;">
  Read the current managed state from the backend.

  <PySourceCode>
    ```python
    @abstractmethod
    def read_current_state(
        self,
        context: CompilerContext,
    ) -> list[BackendArtifact]:
        """Read the current managed state from the backend.

        Args:
            context: Context for reading state.

        Returns:
            List of currently managed artifacts.
        """
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;CompilerContext&#x22;" value="undefined">
      Context for reading state.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of currently managed artifacts.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_generate_revert_id&#x22;" type="&#x22;(self) -> str&#x22;">
  Generate a unique revert ID.

  <PySourceCode>
    ```python
    def _generate_revert_id(self) -> str:
        """Generate a unique revert ID."""
        return f"{self.backend_name}_{uuid.uuid4().hex[:8]}"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_matches_managed&#x22;" type="&#x22;(self, name, context) -> bool&#x22;">
  Check if an artifact name is managed by Phlo.

  <PySourceCode>
    ```python
    def _matches_managed(
        self,
        name: str,
        context: CompilerContext,
    ) -> bool:
        """Check if an artifact name is managed by Phlo."""
        return name.startswith(context.managed_prefix)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;CompilerContext&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_apply_generic_policy_change&#x22;" type="&#x22;(self, change) -> None&#x22;">
  Apply a change through the generic governance backend protocol.

  <PySourceCode>
    ```python
    def _apply_generic_policy_change(
        self,
        change: PolicyChange,
    ) -> None:
        """Apply a change through the generic governance backend protocol."""
        if self._backend is None:
            raise RuntimeError(f"No {self.backend_name} governance backend registered")

        if change.change_type == "create":
            self._backend.apply_policy(policy=self._artifact_to_access_policy(change.artifact))
            return

        if change.change_type == "delete":
            self._backend.revoke_policy(policy_id=change.artifact.name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;change&#x22;" type="&#x22;PolicyChange&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_artifact_to_access_policy&#x22;" type="&#x22;(self, artifact) -> AccessPolicy&#x22;">
  Convert a backend artifact into the generic governance policy shape.

  <PySourceCode>
    ```python
    def _artifact_to_access_policy(self, artifact: BackendArtifact) -> AccessPolicy:
        """Convert a backend artifact into the generic governance policy shape."""
        action = artifact.metadata.get("permission_type") or artifact.metadata.get(
            "privilege", "SELECT"
        )
        resource = artifact.metadata.get("resource") or artifact.metadata.get(
            "table", artifact.name
        )
        effect = "DENY" if artifact.metadata.get("effect") == "deny" else "ALLOW"

        return AccessPolicy(
            policy_id=artifact.name,
            principal=artifact.metadata.get("role", artifact.name),
            table_pattern=resource,
            action=action,
            effect=effect,
            columns=None,
            row_filter=None,
            data_masking=None,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;artifact&#x22;" type="&#x22;BackendArtifact&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.AccessPolicy&#x22;" />
</PyFunction>

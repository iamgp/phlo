# HasuraCompiler (/docs/python-reference/core/phlo/rbac/compiler/HasuraCompiler)



Compiler for Hasura permissions.

Attributes [#attributes]

<PyAttribute name="&#x22;ACTION_MAPPING&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;{'dataset.read': 'select', 'dataset.query': 'select', 'asset.read': 'select', 'asset.execute': 'select', 'service.read': 'select', 'service.manage': 'select', 'admin.read': 'select', 'admin.manage': 'select'}&#x22;" />

<PyAttribute name="&#x22;backend_name&#x22;" type="&#x22;str&#x22;" value="null" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, backend=None)&#x22;">
  <PySourceCode>
    ```python
    def __init__(self, backend: GovernanceBackend | None = None):
        super().__init__(backend)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;backend&#x22;" type="&#x22;GovernanceBackend | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;supports_action&#x22;" type="&#x22;(self, action) -> bool&#x22;">
  <PySourceCode>
    ```python
    def supports_action(self, action: str) -> bool:
        return action in self.ACTION_MAPPING
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;action&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>

<PyFunction name="&#x22;compile&#x22;" type="&#x22;(self, rbac, context) -> list[BackendArtifact]&#x22;">
  Compile canonical RBAC into Hasura artifacts.

  <PySourceCode>
    ```python
    def compile(
        self,
        rbac: CanonicalRBAC,
        context: CompilerContext,
    ) -> list[BackendArtifact]:
        """Compile canonical RBAC into Hasura artifacts."""
        artifacts: list[BackendArtifact] = []

        import json

        for policy in rbac.policies.policies:
            if not self.supports_action(policy.action):
                continue

            if policy.effect != PolicyEffect.ALLOW:
                continue

            permission_type = self.ACTION_MAPPING.get(policy.action, "select")

            for role_name in policy.principal_roles:
                resource_id = policy.resource_id_pattern.replace("*", "%")

                permission = {
                    "role": role_name,
                    "permission": {
                        "columns": "*",
                        "filter": {},
                        "allow_upsert": True,
                    },
                }

                artifacts.append(
                    BackendArtifact(
                        backend=self.backend_name,
                        artifact_type="permission",
                        name=f"{role_name}_{resource_id}_{permission_type}",
                        statement=json.dumps(permission),
                        managed=True,
                        metadata={
                            "role": role_name,
                            "table": resource_id,
                            "permission_type": permission_type,
                            "policy_id": policy.policy_id,
                        },
                    )
                )

        return artifacts
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;rbac&#x22;" type="&#x22;CanonicalRBAC&#x22;" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;CompilerContext&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.rbac.models.BackendArtifact]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;plan&#x22;" type="&#x22;(self, rbac, context) -> SyncPlan&#x22;">
  <PySourceCode>
    ```python
    def plan(
        self,
        rbac: CanonicalRBAC,
        context: CompilerContext,
    ) -> SyncPlan:
        desired = self.compile(rbac, context)
        current = self.read_current_state(context)

        desired_by_name = {a.name: a for a in desired}
        current_by_name = {a.name: a for a in current}

        changes: list[PolicyChange] = []

        for name, artifact in desired_by_name.items():
            if name not in current_by_name:
                changes.append(
                    PolicyChange(
                        change_type="create",
                        backend=self.backend_name,
                        artifact=artifact,
                        revert_id=self._generate_revert_id(),
                    )
                )

        for name, artifact in current_by_name.items():
            if name not in desired_by_name:
                changes.append(
                    PolicyChange(
                        change_type="delete",
                        backend=self.backend_name,
                        artifact=artifact,
                    )
                )

        return SyncPlan(
            version_hash=rbac.version_hash or "",
            backend=self.backend_name,
            changes=tuple(changes),
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;rbac&#x22;" type="&#x22;CanonicalRBAC&#x22;" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;CompilerContext&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.rbac.models.SyncPlan&#x22;" />
</PyFunction>

<PyFunction name="&#x22;apply&#x22;" type="&#x22;(self, plan, context) -> tuple[list[str], list[str]]&#x22;">
  <PySourceCode>
    ```python
    def apply(
        self,
        plan: SyncPlan,
        context: CompilerContext,
    ) -> tuple[list[str], list[str]]:
        success_ids: list[str] = []
        errors: list[str] = []

        for change in plan.changes:
            try:
                self._apply_generic_policy_change(change)
                if change.change_type == "create" and change.revert_id:
                    success_ids.append(change.revert_id)
            except Exception as e:
                errors.append(f"Failed to apply {change.artifact.name}: {e}")

        return success_ids, errors
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plan&#x22;" type="&#x22;SyncPlan&#x22;" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;CompilerContext&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;tuple[list[str], list[str]]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;verify&#x22;" type="&#x22;(self, rbac, context) -> VerifyResult&#x22;">
  <PySourceCode>
    ```python
    def verify(
        self,
        rbac: CanonicalRBAC,
        context: CompilerContext,
    ) -> VerifyResult:
        desired = self.compile(rbac, context)
        current = self.read_current_state(context)

        desired_by_name = {d.name: d for d in desired}
        current_by_name = {c.name: c for c in current}

        missing = [desired_by_name[n] for n in desired_by_name if n not in current_by_name]
        extra = [current_by_name[n] for n in current_by_name if n not in desired_by_name]

        return VerifyResult(
            backend=self.backend_name,
            in_sync=len(missing) == 0 and len(extra) == 0,
            missing=tuple(missing),
            extra=tuple(extra),
            mismatched=(),
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;rbac&#x22;" type="&#x22;CanonicalRBAC&#x22;" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;CompilerContext&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.rbac.models.VerifyResult&#x22;" />
</PyFunction>

<PyFunction name="&#x22;revert&#x22;" type="&#x22;(self, revert_ids, context) -> tuple[list[str], list[str]]&#x22;">
  <PySourceCode>
    ```python
    def revert(
        self,
        revert_ids: list[str],
        context: CompilerContext,
    ) -> tuple[list[str], list[str]]:
        return [], []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;revert_ids&#x22;" type="&#x22;list[str]&#x22;" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;CompilerContext&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;tuple[list[str], list[str]]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;read_current_state&#x22;" type="&#x22;(self, context) -> list[BackendArtifact]&#x22;">
  <PySourceCode>
    ```python
    def read_current_state(
        self,
        context: CompilerContext,
    ) -> list[BackendArtifact]:
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;CompilerContext&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.rbac.models.BackendArtifact]&#x22;" />
</PyFunction>

# TrinoCompiler (/docs/python-reference/core/phlo/rbac/compiler/TrinoCompiler)



Compiler for Trino SQL grants.

Attributes [#attributes]

<PyAttribute name="&#x22;ACTION_MAPPING&#x22;" type="&#x22;dict[str, tuple[str, ...]]&#x22;" value="&#x22;{'dataset.read': ('SELECT',), 'dataset.query': ('SELECT',), 'asset.read': ('SELECT',), 'asset.execute': ('SELECT',), 'service.read': ('SELECT',), 'service.manage': ('ALL PRIVILEGES',), 'admin.read': ('SELECT',), 'admin.manage': ('ALL PRIVILEGES',)}&#x22;" />

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

<PyFunction name="&#x22;_encode_revert_id&#x22;" type="&#x22;(self, artifact_name) -> str&#x22;">
  Encode a Trino artifact name into a reversible revert ID.

  <PySourceCode>
    ```python
    def _encode_revert_id(self, artifact_name: str) -> str:
        """Encode a Trino artifact name into a reversible revert ID."""
        encoded = base64.urlsafe_b64encode(artifact_name.encode()).decode().rstrip("=")
        return f"{self.backend_name}:{encoded}"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;artifact_name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_decode_revert_id&#x22;" type="&#x22;(self, revert_id) -> str&#x22;">
  Decode a Trino revert ID back into an artifact name.

  <PySourceCode>
    ```python
    def _decode_revert_id(self, revert_id: str) -> str:
        """Decode a Trino revert ID back into an artifact name."""
        prefix = f"{self.backend_name}:"
        if not revert_id.startswith(prefix):
            raise ValueError(f"Invalid Trino revert ID: {revert_id}")

        encoded = revert_id[len(prefix) :]
        padding = "=" * (-len(encoded) % 4)
        try:
            return base64.urlsafe_b64decode(f"{encoded}{padding}").decode()
        except Exception as exc:  # pragma: no cover - defensive decode guard
            raise ValueError(f"Invalid Trino revert ID: {revert_id}") from exc
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;revert_id&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;" />
</PyFunction>

<PyFunction name="&#x22;compile&#x22;" type="&#x22;(self, rbac, context) -> list[BackendArtifact]&#x22;">
  Compile canonical RBAC into Trino artifacts.

  <PySourceCode>
    ```python
    def compile(
        self,
        rbac: CanonicalRBAC,
        context: CompilerContext,
    ) -> list[BackendArtifact]:
        """Compile canonical RBAC into Trino artifacts."""
        artifacts: list[BackendArtifact] = []

        for policy in rbac.policies.policies:
            if not self.supports_action(policy.action):
                continue

            if policy.effect != PolicyEffect.ALLOW:
                continue

            privileges = self.ACTION_MAPPING.get(policy.action, ())

            for role_name in policy.principal_roles:
                resource_id = policy.resource_id_pattern.replace("*", "%")
                artifact_name = f"{role_name}_{policy.resource_type}_{resource_id}"

                for privilege in privileges:
                    if policy.resource_type == "dataset":
                        statement = f"GRANT {privilege} ON TABLE {resource_id} TO ROLE {role_name}"
                    elif policy.resource_type == "service":
                        statement = f"GRANT {privilege} ON SCHEMA {resource_id} TO ROLE {role_name}"
                    else:
                        statement = f"GRANT {privilege} ON {policy.resource_type} {resource_id} TO ROLE {role_name}"

                    artifacts.append(
                        BackendArtifact(
                            backend=self.backend_name,
                            artifact_type="grant",
                            name=artifact_name,
                            statement=statement,
                            managed=True,
                            metadata={
                                "role": role_name,
                                "privilege": privilege,
                                "resource": resource_id,
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
  Create a sync plan for Trino.

  <PySourceCode>
    ```python
    def plan(
        self,
        rbac: CanonicalRBAC,
        context: CompilerContext,
    ) -> SyncPlan:
        """Create a sync plan for Trino."""
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
                        revert_id=self._encode_revert_id(artifact.name),
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
  Apply planned changes to Trino.

  <PySourceCode>
    ```python
    def apply(
        self,
        plan: SyncPlan,
        context: CompilerContext,
    ) -> tuple[list[str], list[str]]:
        """Apply planned changes to Trino."""
        if self._backend is None:
            return [], ["No backend configured"]

        success_ids: list[str] = []
        errors: list[str] = []

        for change in plan.changes:
            if change.change_type == "create":
                try:
                    self._apply_artifact(change.artifact)
                    if change.revert_id:
                        success_ids.append(change.revert_id)
                except Exception as e:
                    errors.append(f"Failed to apply {change.artifact.name}: {e}")
            elif change.change_type == "delete":
                try:
                    self._revert_artifact(change.artifact)
                except Exception as e:
                    errors.append(f"Failed to revert {change.artifact.name}: {e}")

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

<PyFunction name="&#x22;_apply_artifact&#x22;" type="&#x22;(self, artifact) -> None&#x22;">
  Apply a single artifact to Trino.

  <PySourceCode>
    ```python
    def _apply_artifact(self, artifact: BackendArtifact) -> None:
        """Apply a single artifact to Trino."""
        if self._backend is None:
            raise RuntimeError("No backend configured")

        privilege = artifact.metadata.get("privilege", "SELECT")
        role = artifact.metadata.get("role", "")
        resource = artifact.metadata.get("resource", "")

        if artifact.artifact_type == "grant":
            if "REVOKE" in artifact.statement:
                return
            parts = artifact.statement.split(" TO ROLE ")
            if len(parts) == 2:
                table = resource
                policy = AccessPolicy(
                    principal=role,
                    table_pattern=table,
                    action=privilege,
                    effect="ALLOW",
                    columns=None,
                    row_filter=None,
                    data_masking=None,
                    policy_id=artifact.name,
                )
                self._backend.apply_policy(policy=policy)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;artifact&#x22;" type="&#x22;BackendArtifact&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_revert_artifact&#x22;" type="&#x22;(self, artifact) -> None&#x22;">
  Revert a single artifact from Trino.

  <PySourceCode>
    ```python
    def _revert_artifact(self, artifact: BackendArtifact) -> None:
        """Revert a single artifact from Trino."""
        if self._backend is None:
            raise RuntimeError("No backend configured")

        privilege = artifact.metadata.get("privilege", "SELECT")
        role = artifact.metadata.get("role", "")
        resource = artifact.metadata.get("resource", "")

        if artifact.artifact_type == "grant":
            self._backend.revoke_policy(
                policy_id=f"{privilege}:{resource}:{role}",
            )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;artifact&#x22;" type="&#x22;BackendArtifact&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;verify&#x22;" type="&#x22;(self, rbac, context) -> VerifyResult&#x22;">
  Verify Trino state matches desired state.

  <PySourceCode>
    ```python
    def verify(
        self,
        rbac: CanonicalRBAC,
        context: CompilerContext,
    ) -> VerifyResult:
        """Verify Trino state matches desired state."""
        desired = self.compile(rbac, context)
        current = self.read_current_state(context)

        desired_by_name = {d.name: d for d in desired}
        current_by_name = {c.name: c for c in current}

        missing = [desired_by_name[n] for n in desired_by_name if n not in current_by_name]
        extra = [current_by_name[n] for n in current_by_name if n not in desired_by_name]
        mismatched = []

        return VerifyResult(
            backend=self.backend_name,
            in_sync=len(missing) == 0 and len(extra) == 0,
            missing=tuple(missing),
            extra=tuple(extra),
            mismatched=tuple(mismatched),
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
  Revert previously applied changes.

  <PySourceCode>
    ```python
    def revert(
        self,
        revert_ids: list[str],
        context: CompilerContext,
    ) -> tuple[list[str], list[str]]:
        """Revert previously applied changes."""
        if self._backend is None:
            return [], ["No backend configured"]

        success_ids: list[str] = []
        errors: list[str] = []

        current_by_name = {artifact.name: artifact for artifact in self.read_current_state(context)}
        for revert_id in revert_ids:
            try:
                artifact_name = self._decode_revert_id(revert_id)
            except ValueError as e:
                errors.append(str(e))
                continue

            artifact = current_by_name.get(artifact_name)
            if artifact is None:
                errors.append(f"Failed to revert {revert_id}: artifact {artifact_name!r} not found")
                continue

            try:
                self._revert_artifact(artifact)
                success_ids.append(revert_id)
            except Exception as e:
                errors.append(f"Failed to revert {revert_id}: {e}")

        return success_ids, errors
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
  Read current managed state from Trino.

  <PySourceCode>
    ```python
    def read_current_state(
        self,
        context: CompilerContext,
    ) -> list[BackendArtifact]:
        """Read current managed state from Trino."""
        if self._backend is None:
            return []

        artifacts: list[BackendArtifact] = []

        try:
            grants = self._backend.list_policies()
            for grant in grants:
                grantee = grant.get("grantee", "")
                privilege = grant.get("privilege", "")
                table = grant.get("table", "")
                schema = grant.get("schema", "")

                if not grantee or not self._matches_managed(grantee, context):
                    continue

                resource = f"{schema}.{table}" if schema and table else (schema or table)
                resource_type = "dataset" if table else "service"

                artifacts.append(
                    BackendArtifact(
                        backend=self.backend_name,
                        artifact_type="grant",
                        name=f"{grantee}_{resource_type}_{resource}",
                        statement=f"GRANT {privilege} ON TABLE {resource} TO ROLE {grantee}",
                        managed=True,
                        metadata={
                            "role": grantee,
                            "privilege": privilege,
                            "resource": resource,
                            "resource_type": resource_type,
                        },
                    )
                )
        except Exception:
            pass

        return artifacts
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;CompilerContext&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.rbac.models.BackendArtifact]&#x22;" />
</PyFunction>

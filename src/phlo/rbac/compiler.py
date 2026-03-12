"""Governance backend compiler interface and implementations.

This module provides the base compiler interface for converting canonical
RBAC policies into backend-native artifacts.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from phlo.capabilities.interfaces import AccessPolicy, GovernanceBackend
from phlo.rbac.models import (
    BackendArtifact,
    CanonicalRBAC,
    PolicyChange,
    PolicyEffect,
    SyncPlan,
    VerifyResult,
)


@dataclass
class CompilerContext:
    """Context passed to compilers during planning and apply."""

    environment: str
    backend_name: str
    managed_prefix: str = "phlo_"
    dry_run: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


class GovernanceCompiler(ABC):
    """Abstract base class for governance backend compilers.

    Each compiler converts canonical RBAC policies into backend-native
    artifacts (SQL grants, IAM policies, Hasura permissions, etc.).
    """

    def __init__(self, backend: GovernanceBackend | None = None):
        """Initialize the compiler.

        Args:
            backend: Optional governance backend instance for apply/verify operations.
        """
        self._backend = backend

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Return the name of the backend this compiler targets."""

    @abstractmethod
    def supports_action(self, action: str) -> bool:
        """Check if this compiler supports the given canonical action.

        Args:
            action: Canonical action name (e.g., "dataset.read").

        Returns:
            True if the compiler can handle this action.
        """

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

    def _generate_revert_id(self) -> str:
        """Generate a unique revert ID."""
        return f"{self.backend_name}_{uuid.uuid4().hex[:8]}"

    def _matches_managed(
        self,
        name: str,
        context: CompilerContext,
    ) -> bool:
        """Check if an artifact name is managed by Phlo."""
        return name.startswith(context.managed_prefix)

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


class TrinoCompiler(GovernanceCompiler):
    """Compiler for Trino SQL grants."""

    ACTION_MAPPING: dict[str, tuple[str, ...]] = {
        "dataset.read": ("SELECT",),
        "dataset.query": ("SELECT",),
        "asset.read": ("SELECT",),
        "asset.execute": ("SELECT",),
        "service.read": ("SELECT",),
        "service.manage": ("ALL PRIVILEGES",),
        "admin.read": ("SELECT",),
        "admin.manage": ("ALL PRIVILEGES",),
    }

    def __init__(self, backend: GovernanceBackend | None = None):
        super().__init__(backend)

    @property
    def backend_name(self) -> str:
        return "trino"

    def supports_action(self, action: str) -> bool:
        return action in self.ACTION_MAPPING

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
                effective_roles = rbac.roles.get_effective_roles(role_name)
                for effective_role in effective_roles:
                    resource_id = policy.resource_id_pattern.replace("*", "%")
                    artifact_name = f"{effective_role}_{policy.resource_type}_{resource_id}"

                    for privilege in privileges:
                        if policy.resource_type == "dataset":
                            statement = (
                                f"GRANT {privilege} ON TABLE {resource_id} TO ROLE {effective_role}"
                            )
                        elif policy.resource_type == "service":
                            statement = f"GRANT {privilege} ON SCHEMA {resource_id} TO ROLE {effective_role}"
                        else:
                            statement = f"GRANT {privilege} ON {policy.resource_type} {resource_id} TO ROLE {effective_role}"

                        artifacts.append(
                            BackendArtifact(
                                backend=self.backend_name,
                                artifact_type="grant",
                                name=artifact_name,
                                statement=statement,
                                managed=True,
                                metadata={
                                    "role": effective_role,
                                    "privilege": privilege,
                                    "resource": resource_id,
                                    "policy_id": policy.policy_id,
                                },
                            )
                        )

        return artifacts

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

    def _apply_artifact(self, artifact: BackendArtifact) -> None:
        """Apply a single artifact to Trino."""
        if self._backend is None:
            raise RuntimeError("No backend configured")

        artifact.metadata.get("privilege", "SELECT")
        role = artifact.metadata.get("role", "")
        resource = artifact.metadata.get("resource", "")

        if artifact.artifact_type == "grant":
            if "REVOKE" in artifact.statement:
                return
            parts = artifact.statement.split(" TO ROLE ")
            if len(parts) == 2:
                action_part, role_part = parts
                action = (
                    action_part.replace("GRANT ", "")
                    .replace(" ON TABLE ", " ")
                    .replace(" ON SCHEMA ", " ")
                    .split()[-1]
                )
                table = resource
                policy = AccessPolicy(
                    principal=role,
                    table_pattern=table,
                    action=action,
                    effect="GRANT",
                    columns=None,
                    row_filter=None,
                    data_masking=None,
                    policy_id=artifact.name,
                )
                self._backend.apply_policy(policy=policy)

    def _revert_artifact(self, artifact: BackendArtifact) -> None:
        """Revert a single artifact from Trino."""
        if self._backend is None:
            raise RuntimeError("No backend configured")

        role = artifact.metadata.get("role", "")
        resource = artifact.metadata.get("resource", "")

        if artifact.artifact_type == "grant":
            self._backend.revoke_policy(
                policy_id=f"SELECT:{resource}:{role}",
            )

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

        current = self.read_current_state(context)
        for revert_id in revert_ids:
            for artifact in current:
                if artifact.metadata.get("revert_id") == revert_id:
                    try:
                        self._revert_artifact(artifact)
                        success_ids.append(revert_id)
                    except Exception as e:
                        errors.append(f"Failed to revert {revert_id}: {e}")

        return success_ids, errors

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

                artifacts.append(
                    BackendArtifact(
                        backend=self.backend_name,
                        artifact_type="grant",
                        name=f"{grantee}_{resource}",
                        statement=f"GRANT {privilege} ON TABLE {resource} TO ROLE {grantee}",
                        managed=True,
                        metadata={
                            "role": grantee,
                            "privilege": privilege,
                            "resource": resource,
                        },
                    )
                )
        except Exception:
            pass

        return artifacts


class PostgreSQLCompiler(GovernanceCompiler):
    """Compiler for PostgreSQL roles and grants."""

    ACTION_MAPPING: dict[str, tuple[str, ...]] = {
        "dataset.read": ("SELECT",),
        "dataset.query": ("SELECT",),
        "asset.read": ("SELECT",),
        "asset.execute": ("SELECT",),
        "service.read": ("USAGE",),
        "service.manage": ("ALL PRIVILEGES",),
        "admin.read": ("SELECT",),
        "admin.manage": ("ALL PRIVILEGES",),
    }

    def __init__(self, backend: GovernanceBackend | None = None):
        super().__init__(backend)

    @property
    def backend_name(self) -> str:
        return "postgresql"

    def supports_action(self, action: str) -> bool:
        return action in self.ACTION_MAPPING

    def compile(
        self,
        rbac: CanonicalRBAC,
        context: CompilerContext,
    ) -> list[BackendArtifact]:
        """Compile canonical RBAC into PostgreSQL artifacts."""
        artifacts: list[BackendArtifact] = []

        for policy in rbac.policies.policies:
            if not self.supports_action(policy.action):
                continue

            if policy.effect != PolicyEffect.ALLOW:
                continue

            privileges = self.ACTION_MAPPING.get(policy.action, ())

            for role_name in policy.principal_roles:
                effective_roles = rbac.roles.get_effective_roles(role_name)
                for effective_role in effective_roles:
                    resource_id = policy.resource_id_pattern.replace("*", "%")

                    for privilege in privileges:
                        statement = f"GRANT {privilege} ON SCHEMA {resource_id} TO {effective_role}"

                        artifacts.append(
                            BackendArtifact(
                                backend=self.backend_name,
                                artifact_type="grant",
                                name=f"{effective_role}_{policy.resource_type}_{resource_id}",
                                statement=statement,
                                managed=True,
                                metadata={
                                    "role": effective_role,
                                    "privilege": privilege,
                                    "resource": resource_id,
                                    "policy_id": policy.policy_id,
                                },
                            )
                        )

        return artifacts

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

    def revert(
        self,
        revert_ids: list[str],
        context: CompilerContext,
    ) -> tuple[list[str], list[str]]:
        return [], []

    def read_current_state(
        self,
        context: CompilerContext,
    ) -> list[BackendArtifact]:
        return []


class HasuraCompiler(GovernanceCompiler):
    """Compiler for Hasura permissions."""

    ACTION_MAPPING: dict[str, str] = {
        "dataset.read": "select",
        "dataset.query": "select",
        "asset.read": "select",
        "asset.execute": "select",
        "service.read": "select",
        "service.manage": "select",
        "admin.read": "select",
        "admin.manage": "select",
    }

    def __init__(self, backend: GovernanceBackend | None = None):
        super().__init__(backend)

    @property
    def backend_name(self) -> str:
        return "hasura"

    def supports_action(self, action: str) -> bool:
        return action in self.ACTION_MAPPING

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
                effective_roles = rbac.roles.get_effective_roles(role_name)
                for effective_role in effective_roles:
                    resource_id = policy.resource_id_pattern.replace("*", "%")

                    permission = {
                        "role": effective_role,
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
                            name=f"{effective_role}_{resource_id}_{permission_type}",
                            statement=json.dumps(permission),
                            managed=True,
                            metadata={
                                "role": effective_role,
                                "table": resource_id,
                                "permission_type": permission_type,
                                "policy_id": policy.policy_id,
                            },
                        )
                    )

        return artifacts

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

    def revert(
        self,
        revert_ids: list[str],
        context: CompilerContext,
    ) -> tuple[list[str], list[str]]:
        return [], []

    def read_current_state(
        self,
        context: CompilerContext,
    ) -> list[BackendArtifact]:
        return []


class MinIOCompiler(GovernanceCompiler):
    """Compiler for MinIO IAM policies."""

    ACTION_MAPPING: dict[str, list[str]] = {
        "object.read": ["s3:GetObject", "s3:ListBucket"],
        "object.write": ["s3:PutObject", "s3:DeleteObject"],
    }

    def __init__(self, backend: GovernanceBackend | None = None):
        super().__init__(backend)

    @property
    def backend_name(self) -> str:
        return "minio"

    def supports_action(self, action: str) -> bool:
        return action in self.ACTION_MAPPING

    def compile(
        self,
        rbac: CanonicalRBAC,
        context: CompilerContext,
    ) -> list[BackendArtifact]:
        """Compile canonical RBAC into MinIO artifacts."""
        artifacts: list[BackendArtifact] = []

        import json

        for policy in rbac.policies.policies:
            if not self.supports_action(policy.action):
                continue

            if policy.effect != PolicyEffect.ALLOW:
                continue

            actions = self.ACTION_MAPPING.get(policy.action, [])

            for role_name in policy.principal_roles:
                effective_roles = rbac.roles.get_effective_roles(role_name)
                for effective_role in effective_roles:
                    resource_pattern = policy.resource_id_pattern.replace("*", "*")

                    statements = []
                    for action in actions:
                        statements.append(
                            {
                                "Effect": "Allow",
                                "Action": action,
                                "Resource": [f"arn:aws:s3:::{resource_pattern}/*"],
                            }
                        )

                    policy_doc = {
                        "Version": "2012-10-17",
                        "Statement": statements,
                    }

                    policy_name = f"{context.managed_prefix}{effective_role}_{policy.action}"

                    artifacts.append(
                        BackendArtifact(
                            backend=self.backend_name,
                            artifact_type="iam_policy",
                            name=policy_name,
                            statement=json.dumps(policy_doc, indent=2),
                            managed=True,
                            metadata={
                                "role": effective_role,
                                "actions": actions,
                                "resource": resource_pattern,
                                "policy_id": policy.policy_id,
                            },
                        )
                    )

        return artifacts

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

    def revert(
        self,
        revert_ids: list[str],
        context: CompilerContext,
    ) -> tuple[list[str], list[str]]:
        return [], []

    def read_current_state(
        self,
        context: CompilerContext,
    ) -> list[BackendArtifact]:
        return []


class NessieCompiler(GovernanceCompiler):
    """Compiler for Nessie authorization rules."""

    ACTION_MAPPING: dict[str, list[str]] = {
        "catalog.read": ["READ"],
        "catalog.manage": ["READ", "WRITE", "DELETE"],
    }

    def __init__(self, backend: GovernanceBackend | None = None):
        super().__init__(backend)

    @property
    def backend_name(self) -> str:
        return "nessie"

    def supports_action(self, action: str) -> bool:
        return action in self.ACTION_MAPPING

    def compile(
        self,
        rbac: CanonicalRBAC,
        context: CompilerContext,
    ) -> list[BackendArtifact]:
        """Compile canonical RBAC into Nessie artifacts."""
        artifacts: list[BackendArtifact] = []

        import json

        for policy in rbac.policies.policies:
            if not self.supports_action(policy.action):
                continue

            if policy.effect != PolicyEffect.ALLOW:
                continue

            permissions = self.ACTION_MAPPING.get(policy.action, [])

            for role_name in policy.principal_roles:
                effective_roles = rbac.roles.get_effective_roles(role_name)
                for effective_role in effective_roles:
                    resource_pattern = policy.resource_id_pattern.replace("*", "*")

                    rule = {
                        "name": f"{effective_role}_{policy.action}_{resource_pattern}",
                        "roles": [effective_role],
                        "permissions": permissions,
                        "resource": resource_pattern,
                    }

                    artifacts.append(
                        BackendArtifact(
                            backend=self.backend_name,
                            artifact_type="authz_rule",
                            name=f"{effective_role}_{policy.action}_{resource_pattern}",
                            statement=json.dumps(rule, indent=2),
                            managed=True,
                            metadata={
                                "role": effective_role,
                                "permissions": permissions,
                                "resource": resource_pattern,
                                "policy_id": policy.policy_id,
                            },
                        )
                    )

        return artifacts

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

    def revert(
        self,
        revert_ids: list[str],
        context: CompilerContext,
    ) -> tuple[list[str], list[str]]:
        return [], []

    def read_current_state(
        self,
        context: CompilerContext,
    ) -> list[BackendArtifact]:
        return []


COMPILER_REGISTRY: dict[str, type[GovernanceCompiler]] = {
    "trino": TrinoCompiler,
    "postgresql": PostgreSQLCompiler,
    "hasura": HasuraCompiler,
    "minio": MinIOCompiler,
    "nessie": NessieCompiler,
}


def get_compiler(
    backend_name: str,
    backend: GovernanceBackend | None = None,
) -> GovernanceCompiler | None:
    """Get a compiler instance for the specified backend.

    Args:
        backend_name: Name of the backend.
        backend: Optional governance backend instance.

    Returns:
        Compiler instance or None if not found.
    """
    compiler_class = COMPILER_REGISTRY.get(backend_name)
    if compiler_class is None:
        return None
    return compiler_class(backend=backend)

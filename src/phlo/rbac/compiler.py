"""Governance backend compiler interface and implementations.

This module provides the base compiler interface for converting canonical
RBAC policies into backend-native artifacts.
"""

from __future__ import annotations

import base64
import re
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

_SQL_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_.%*-]*$")
_SQL_PRIVILEGE_RE = re.compile(r"^[A-Z][A-Z ]*$")


def _validate_sql_identifier(value: str, label: str) -> str:
    """Validate that *value* is a safe SQL identifier fragment.

    Raises ``ValueError`` when *value* contains characters outside the
    allowed set (alphanumeric, underscore, dot, percent, asterisk, hyphen).
    """
    if not _SQL_IDENTIFIER_RE.match(value):
        raise ValueError(f"Unsafe {label}: {value!r}")
    return value


def _validate_sql_privilege(value: str) -> str:
    """Validate that *value* is a safe SQL privilege keyword (e.g. ``SELECT``, ``ALL PRIVILEGES``)."""
    if not _SQL_PRIVILEGE_RE.match(value):
        raise ValueError(f"Unsafe privilege: {value!r}")
    return value


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

    def _encode_revert_id(self, artifact_name: str) -> str:
        """Encode a Trino artifact name into a reversible revert ID."""
        encoded = base64.urlsafe_b64encode(artifact_name.encode()).decode().rstrip("=")
        return f"{self.backend_name}:{encoded}"

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
                _validate_sql_identifier(role_name, "role_name")
                resource_id = policy.resource_id_pattern.replace("*", "%")
                _validate_sql_identifier(resource_id, "resource_id")
                _validate_sql_identifier(policy.resource_type, "resource_type")
                artifact_name = f"{role_name}_{policy.resource_type}_{resource_id}"

                for privilege in privileges:
                    _validate_sql_privilege(privilege)
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
                _validate_sql_identifier(role_name, "role_name")
                resource_id = policy.resource_id_pattern.replace("*", "%")
                _validate_sql_identifier(resource_id, "resource_id")

                for privilege in privileges:
                    _validate_sql_privilege(privilege)
                    statement = f"GRANT {privilege} ON SCHEMA {resource_id} TO {role_name}"

                    artifacts.append(
                        BackendArtifact(
                            backend=self.backend_name,
                            artifact_type="grant",
                            name=f"{role_name}_{policy.resource_type}_{resource_id}",
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
        raise NotImplementedError("PostgreSQLCompiler.revert is not implemented")

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
        raise NotImplementedError("HasuraCompiler.revert is not implemented")

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

                policy_name = f"{context.managed_prefix}{role_name}_{policy.action}"

                artifacts.append(
                    BackendArtifact(
                        backend=self.backend_name,
                        artifact_type="iam_policy",
                        name=policy_name,
                        statement=json.dumps(policy_doc, indent=2),
                        managed=True,
                        metadata={
                            "role": role_name,
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
        raise NotImplementedError("MinIOCompiler.revert is not implemented")

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
                resource_pattern = policy.resource_id_pattern.replace("*", "*")

                rule = {
                    "name": f"{role_name}_{policy.action}_{resource_pattern}",
                    "roles": [role_name],
                    "permissions": permissions,
                    "resource": resource_pattern,
                }

                artifacts.append(
                    BackendArtifact(
                        backend=self.backend_name,
                        artifact_type="authz_rule",
                        name=f"{role_name}_{policy.action}_{resource_pattern}",
                        statement=json.dumps(rule, indent=2),
                        managed=True,
                        metadata={
                            "role": role_name,
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
        raise NotImplementedError("NessieCompiler.revert is not implemented")

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

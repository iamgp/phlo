"""Tests for RBAC compiler behavior."""

from __future__ import annotations

from typing import cast

from phlo.capabilities.interfaces import GovernanceBackend
from phlo.rbac.compiler import CompilerContext, TrinoCompiler
from phlo.rbac.models import BackendArtifact, PolicyChange, SyncPlan


class _FakeTrinoBackend:
    def __init__(self) -> None:
        self.applied_policies = []
        self.revoked_policy_ids = []
        self._policies = []

    def list_policies(self, *, table_name: str | None = None) -> list[dict[str, str]]:
        return list(self._policies)

    def apply_policy(self, *, policy) -> None:
        self.applied_policies.append(policy)

    def revoke_policy(self, *, policy_id: str) -> None:
        self.revoked_policy_ids.append(policy_id)


def test_trino_apply_uses_privilege_as_action() -> None:
    backend = _FakeTrinoBackend()
    compiler = TrinoCompiler(backend=cast(GovernanceBackend, backend))
    artifact = BackendArtifact(
        backend="trino",
        artifact_type="grant",
        name="phlo_admin_dataset_analytics.table",
        statement="GRANT SELECT ON TABLE analytics.table TO ROLE phlo_admin",
        metadata={
            "role": "phlo_admin",
            "privilege": "SELECT",
            "resource": "analytics.table",
        },
    )

    compiler._apply_artifact(artifact)

    assert len(backend.applied_policies) == 1
    assert backend.applied_policies[0].action == "SELECT"
    assert backend.applied_policies[0].effect == "ALLOW"
    assert backend.applied_policies[0].table_pattern == "analytics.table"


def test_trino_revert_decodes_revert_id_to_artifact_name() -> None:
    backend = _FakeTrinoBackend()
    backend._policies = [
        {
            "grantee": "phlo_admin",
            "schema": "analytics",
            "table": "table",
            "privilege": "SELECT",
        }
    ]
    compiler = TrinoCompiler(backend=cast(GovernanceBackend, backend))
    artifact_name = "phlo_admin_dataset_analytics.table"
    revert_id = compiler._encode_revert_id(artifact_name)
    context = CompilerContext(environment="test", backend_name="trino")

    success_ids, errors = compiler.revert([revert_id], context)

    assert success_ids == [revert_id]
    assert errors == []
    assert backend.revoked_policy_ids == ["SELECT:analytics.table:phlo_admin"]


def test_trino_plan_emits_revert_ids_that_round_trip() -> None:
    compiler = TrinoCompiler()
    artifact = BackendArtifact(
        backend="trino",
        artifact_type="grant",
        name="phlo_admin_dataset_analytics.table",
        statement="GRANT SELECT ON TABLE analytics.table TO ROLE phlo_admin",
        metadata={},
    )
    plan = SyncPlan(
        version_hash="abc123",
        backend="trino",
        changes=(
            PolicyChange(
                change_type="create",
                backend="trino",
                artifact=artifact,
                revert_id=compiler._encode_revert_id(artifact.name),
            ),
        ),
    )

    revert_id = plan.changes[0].revert_id

    assert revert_id is not None
    assert compiler._decode_revert_id(revert_id) == artifact.name


def test_trino_read_current_state_uses_compile_compatible_names() -> None:
    backend = _FakeTrinoBackend()
    backend._policies = [
        {
            "grantee": "phlo_admin",
            "schema": "analytics",
            "table": "table",
            "privilege": "SELECT",
        }
    ]
    compiler = TrinoCompiler(backend=cast(GovernanceBackend, backend))
    context = CompilerContext(environment="test", backend_name="trino")

    artifacts = compiler.read_current_state(context)

    assert len(artifacts) == 1
    assert artifacts[0].name == "phlo_admin_dataset_analytics.table"
    assert artifacts[0].metadata["resource_type"] == "dataset"

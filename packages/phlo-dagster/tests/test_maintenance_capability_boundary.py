"""Guard Dagster maintenance from importing concrete provider resources."""

import ast
from pathlib import Path
from unittest.mock import MagicMock

from phlo_dagster import iceberg_maintenance
from phlo_dagster.iceberg_maintenance_utils import MaintenanceConfig


class FakeMaintenanceRetentionStore:
    """Structural fake for the provider-neutral Dagster retention contract."""

    def __init__(self) -> None:
        self.expected_snapshot_id: int | str | None = None

    def _plan(self) -> dict[str, object]:
        return {
            "operation": "cleanup_orphan_files",
            "table_name": "raw.events",
            "ref": "main",
            "catalog": "iceberg",
            "retention_hours": 168,
            "before_snapshot_id": 41,
            "candidate_files": [{"path": "orphan.parquet", "size_bytes": 100}],
            "protected_snapshot_ids": [41],
            "table_snapshot_refs": {},
            "table_snapshot_ref_evidence": "available",
            "nessie_ref_evidence": "unavailable",
            "scan_status": "available",
            "affected_objects": 1,
            "affected_bytes": 100,
            "unavailable_fields": [],
            "plan_token": "fake-plan-token",
        }

    def expire_snapshots(self, **kwargs: object) -> dict[str, object]:
        return self._result(kwargs, "expire_snapshots")

    def cleanup_orphan_files(self, **kwargs: object) -> dict[str, object]:
        return self._result(kwargs, "cleanup_orphan_files")

    def _result(self, kwargs: dict[str, object], operation: str) -> dict[str, object]:
        plan = self._plan()
        plan["operation"] = operation
        if kwargs.get("dry_run"):
            return {
                "status": "planned",
                "accepted": True,
                "executed": False,
                "before_revision": 41,
                "plan_token": "fake-plan-token",
                "planned": plan,
            }
        self.expected_snapshot_id = kwargs.get("expected_snapshot_id")
        return {
            "status": "blocked",
            "accepted": False,
            "executed": False,
            "before_revision": 41,
            "plan_token": "fake-plan-token",
            "planned": {**plan, "trino_boundary": "not_invoked"},
            "failure": {
                "code": "bounded_execution_unsupported",
                "message": "The provider accepts only a threshold; no deletion is submitted.",
                "retryable": False,
            },
            "retry_safe": False,
        }


def test_maintenance_source_does_not_import_concrete_provider_modules() -> None:
    """Retention orchestration may import Phlo core and itself, not provider packages."""
    source_root = Path(__file__).parents[1] / "src" / "phlo_dagster"
    provider_imports: list[ast.AST] = []
    maintenance_sources = (
        "iceberg_maintenance.py",
        "iceberg_maintenance_utils.py",
        "maintenance_policy.py",
        "maintenance_sensor.py",
    )
    for filename in maintenance_sources:
        source_path = source_root / filename
        tree = ast.parse(source_path.read_text())
        provider_imports.extend(
            node
            for node in ast.walk(tree)
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("phlo_")
                and not node.module.startswith("phlo_dagster")
            )
            or (
                isinstance(node, ast.Import)
                and any(
                    alias.name.startswith("phlo_") and not alias.name.startswith("phlo_dagster")
                    for alias in node.names
                )
            )
        )

    assert provider_imports == []


def test_orphan_execute_uses_plan_result_and_refuses_without_executor(monkeypatch) -> None:
    """The Dagster op forwards the real plan fence and never resolves Trino."""
    store = FakeMaintenanceRetentionStore()
    resolutions: list[tuple[str, str]] = []

    def resolve(capability_type: str, name: str):
        resolutions.append((capability_type, name))
        return MagicMock(provider=store)

    monkeypatch.setattr(iceberg_maintenance, "resolve_capability", resolve)
    monkeypatch.setattr(iceberg_maintenance, "resolve_namespaces", lambda config: ["raw"])
    monkeypatch.setattr(iceberg_maintenance, "list_tables", lambda namespace, ref: ["raw.events"])
    config = MaintenanceConfig(
        namespace="raw",
        ref="main",
        dry_run=False,
        catalog="iceberg",
        confirmation_token="fake-plan-token",
        max_affected_objects=10,
        max_affected_bytes=1000,
    )

    context = MagicMock()
    context.run_id = "run-1"
    context.job_name = "maintenance"
    result = iceberg_maintenance.cleanup_orphan_files.compute_fn.decorated_fn(context, config)

    assert resolutions == [("table_store", "iceberg")]
    assert store.expected_snapshot_id == 41
    assert result["tables_processed"] == 1
    assert result["total_candidate_files"] == 1
    assert result["total_deleted_files"] == 0
    assert result["errors"]
    warning_messages = [call.args[0] for call in context.log.warning.call_args_list]
    assert any("no provider deletion is submitted" in message for message in warning_messages)
    assert any("only a threshold" in message for message in warning_messages)

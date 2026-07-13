"""Guard Dagster maintenance from importing concrete provider resources."""

import ast
from types import SimpleNamespace
from unittest.mock import MagicMock
from pathlib import Path

from phlo_dagster import iceberg_maintenance
from phlo_dagster.iceberg_maintenance_utils import MaintenanceConfig
from phlo_iceberg.resource import IcebergResource, _maintenance_plan_token


def test_retention_controller_does_not_import_iceberg_resource() -> None:
    """Dagster orchestration must resolve neutral capabilities, never provider modules."""
    source_root = Path(__file__).parents[1] / "src" / "phlo_dagster"
    provider_imports: list[ast.AST] = []
    for source_path in source_root.rglob("*.py"):
        tree = ast.parse(source_path.read_text())
        provider_imports.extend(
            node
            for node in ast.walk(tree)
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("phlo_iceberg")
            )
            or (
                isinstance(node, ast.Import)
                and any(alias.name.startswith("phlo_iceberg") for alias in node.names)
            )
        )

    assert provider_imports == []


def test_orphan_execute_uses_plan_result_and_refuses_without_executor(monkeypatch) -> None:
    """The Dagster op forwards the real plan fence and never resolves Trino."""
    resource = IcebergResource(ref="main")
    plan: dict[str, object] = {
        "operation": "cleanup_orphan_files",
        "table_name": "raw.events",
        "ref": "main",
        "catalog": "iceberg",
        "retention_hours": 168,
        "retention_threshold": "7d",
        "minimum_safe_retention_hours": 168,
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
    }
    plan["plan_token"] = _maintenance_plan_token(plan)
    monkeypatch.setattr(resource, "_orphan_retention_metadata", lambda **_: (plan, object()))

    resolutions: list[tuple[str, str]] = []

    def resolve(capability_type: str, name: str):
        resolutions.append((capability_type, name))
        return SimpleNamespace(provider=resource)

    monkeypatch.setattr(iceberg_maintenance, "resolve_capability", resolve)
    monkeypatch.setattr(iceberg_maintenance, "resolve_namespaces", lambda config: ["raw"])
    monkeypatch.setattr(iceberg_maintenance, "list_tables", lambda namespace, ref: ["raw.events"])
    config = MaintenanceConfig(
        namespace="raw",
        ref="main",
        dry_run=False,
        catalog="iceberg",
        confirmation_token=plan["plan_token"],
        max_affected_objects=10,
        max_affected_bytes=1000,
    )

    context = MagicMock()
    context.run_id = "run-1"
    context.job_name = "maintenance"
    result = iceberg_maintenance.cleanup_orphan_files.compute_fn.decorated_fn(context, config)

    assert resolutions == [("table_store", "iceberg")]
    assert result["tables_processed"] == 1
    assert result["total_candidate_files"] == 1
    assert result["total_deleted_files"] == 0
    assert result["errors"]
    warning_messages = [call.args[0] for call in context.log.warning.call_args_list]
    assert any("no provider deletion is submitted" in message for message in warning_messages)
    assert any("only a threshold" in message for message in warning_messages)

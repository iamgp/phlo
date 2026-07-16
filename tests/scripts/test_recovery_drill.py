from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parents[2] / "scripts" / "recovery_drill.py"
SPEC = importlib.util.spec_from_file_location("recovery_drill", SCRIPT_PATH)
assert SPEC and SPEC.loader
recovery_drill = importlib.util.module_from_spec(SPEC)
sys.modules["recovery_drill"] = recovery_drill
SPEC.loader.exec_module(recovery_drill)


def test_compose_uses_isolated_ports_and_supported_stack_images(tmp_path):
    stack = recovery_drill.Stack("owned-drill", tmp_path / "source", 15432, 19000, 19120)

    compose = recovery_drill.compose_yaml(stack)

    assert "postgres:16-alpine" in compose
    assert "minio/minio:RELEASE.2025-09-07T16-13-09Z" in compose
    assert "ghcr.io/projectnessie/nessie:0.107.2" in compose
    assert "127.0.0.1:15432:5432" in compose
    assert "nessie.catalog.warehouses.warehouse.location: s3://lake/warehouse" in compose
    assert "nessie.catalog.service.s3.default-options.endpoint: http://minio:9000/" in compose
    assert 'nessie.catalog.service.s3.default-options.path-style-access: "true"' in compose
    assert recovery_drill.MC_IMAGE.startswith("minio/mc@sha256:")
    assert ":latest" not in recovery_drill.MC_IMAGE


def test_helper_is_network_local_and_uses_locked_dependency_export(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(recovery_drill, "run", lambda command, **_: calls.append(command))

    recovery_drill.prepare_helper(tmp_path)

    assert recovery_drill.HELPER_IMAGE.startswith("python@sha256:")
    assert "http://nessie:19120/iceberg/main" in recovery_drill.helper_source()
    assert '"s3.endpoint": "http://minio:9000"' in recovery_drill.helper_source()
    assert calls == [
        [
            "uv",
            "export",
            "--locked",
            "--package",
            "phlo-iceberg",
            "--no-emit-workspace",
            "--no-editable",
            "--format",
            "requirements-txt",
            "--output-file",
            str(tmp_path / "requirements.txt"),
        ]
    ]
    assert (tmp_path / "iceberg_helper.py").read_text(
        encoding="utf-8"
    ) == recovery_drill.helper_source()


def test_manifest_round_trip_requires_fixture_and_checksum(tmp_path):
    fixture = {"project_id": "project", "table_name": "recovery.rows", "snapshot_id": "42"}
    (tmp_path / "postgres.sql").write_text("backup", encoding="utf-8")
    (tmp_path / "lake").mkdir()

    recovery_drill.write_manifest(tmp_path, fixture, "a" * 64)

    assert recovery_drill.read_manifest(tmp_path) == {
        "fixture": fixture,
        "probe_checksum": "a" * 64,
    }


@pytest.mark.parametrize(
    "contents",
    [
        "",
        "[]",
        json.dumps({"fixture": {}}),
        json.dumps(
            {
                "fixture": {"project_id": "p", "table_name": "t", "snapshot_id": "s"},
                "probe_checksum": "not-a-checksum",
            }
        ),
    ],
)
def test_manifest_rejects_missing_or_corrupt_verification_evidence(tmp_path, contents):
    (tmp_path / "manifest.json").write_text(contents, encoding="utf-8")

    with pytest.raises(recovery_drill.RecoveryDrillError, match="backup manifest"):
        recovery_drill.read_manifest(tmp_path)


def test_manifest_rejects_missing_backup_files(tmp_path):
    recovery_drill.write_manifest(
        tmp_path, {"project_id": "p", "table_name": "t", "snapshot_id": "s"}, "a" * 64
    )

    with pytest.raises(recovery_drill.RecoveryDrillError, match="backup manifest"):
        recovery_drill.read_manifest(tmp_path)


def test_restored_evidence_requires_exact_resource_and_catalog_change():
    fixture = {"project_id": "project", "table_name": "recovery.rows", "snapshot_id": "42"}

    class Store:
        def get_run(self, *_):
            return {"run_id": "fixture"}

        def list_resources(self, *_):
            return [
                {
                    "resource_id": "rows",
                    "table_name": "recovery.rows",
                    "catalog": "iceberg",
                    "ref_name": "main",
                    "snapshot_after": "42",
                }
            ]

        def list_catalog_changes(self, *_):
            return [
                {
                    "catalog_change_id": "main",
                    "content_key": "recovery.rows",
                    "catalog_ref": "main",
                    "snapshot_after": "42",
                }
            ]

    recovery_drill.verify_evidence(Store(), fixture)

    class MissingCatalog(Store):
        def list_catalog_changes(self, *_):
            return []

    with pytest.raises(recovery_drill.RecoveryDrillError, match="RunCatalogChange"):
        recovery_drill.verify_evidence(MissingCatalog(), fixture)


def test_cleanup_uses_only_project_scoped_compose_down(tmp_path, monkeypatch):
    stack = recovery_drill.Stack("owned-drill", tmp_path / "source", 1, 2, 3)
    calls = []
    monkeypatch.setattr(recovery_drill, "run", lambda command, **_: calls.append(command))

    recovery_drill.cleanup(stack)

    assert calls == [
        [
            "docker",
            "compose",
            "-p",
            "owned-drill",
            "-f",
            str(stack.compose_file),
            "down",
            "--volumes",
            "--remove-orphans",
        ]
    ]


def test_remove_owned_only_removes_matching_drill_directory(tmp_path):
    owned = tmp_path / "owned"
    owned.mkdir()
    (owned / recovery_drill.OWNER_MARKER).write_text(
        json.dumps({"token": "mine"}), encoding="utf-8"
    )
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / recovery_drill.OWNER_MARKER).write_text(
        json.dumps({"token": "other"}), encoding="utf-8"
    )

    recovery_drill.remove_owned(owned, "mine")
    recovery_drill.remove_owned(foreign, "mine")

    assert not owned.exists()
    assert foreign.exists()

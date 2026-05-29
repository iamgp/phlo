"""Tests for agent-facing authoring API routes."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi.testclient import TestClient

from phlo_api.main import app


@dataclass(frozen=True)
class _FakeWorkflowResult:
    workflow_type: str
    domain: str
    table: str
    files: list[str]
    next_steps: list[str]


def test_authoring_routes_create_and_list_templates(monkeypatch, tmp_path) -> None:
    from phlo_api.api import authoring

    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setenv(
        "PHLO_API_TOKENS",
        '{"project-token":{"subject":"agent","scopes":["project:write"]}}',
    )

    def fake_create_workflow(**kwargs):  # noqa: ANN003, ANN202
        return _FakeWorkflowResult(
            workflow_type=kwargs["workflow_type"],
            domain=kwargs["domain"],
            table=kwargs["table"],
            files=["workflows/ingestion/demo/orders.py"],
            next_steps=["phlo materialize dlt_orders"],
        )

    monkeypatch.setattr(authoring, "_create_workflow", fake_create_workflow)

    client = TestClient(app)
    headers = {"Authorization": "Bearer project-token"}
    created = client.post(
        "/api/authoring/workflows",
        json={"domain": "demo", "table": "orders", "unique_key": "id"},
        headers=headers,
    )
    templates = client.get("/api/authoring/templates")

    assert created.status_code == 200
    assert created.json()["files"] == ["workflows/ingestion/demo/orders.py"]
    assert templates.status_code == 200
    assert any(item["name"] == "csv-batch" for item in templates.json()["items"])


def test_authoring_create_workflow_returns_conflict_for_existing_files(
    monkeypatch, tmp_path
) -> None:
    from phlo_api.api import authoring

    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setenv(
        "PHLO_API_TOKENS",
        '{"project-token":{"subject":"agent","scopes":["project:write"]}}',
    )

    def fake_create_workflow(**kwargs):  # noqa: ANN003, ANN202
        raise FileExistsError("Files already exist:\n  - workflows/ingestion/demo/orders.py")

    monkeypatch.setattr(authoring, "_create_workflow", fake_create_workflow)

    response = TestClient(app).post(
        "/api/authoring/workflows",
        json={"domain": "demo", "table": "orders", "unique_key": "id"},
        headers={"Authorization": "Bearer project-token"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == {
        "error": "workflow_already_exists",
        "message": "Files already exist:\n  - workflows/ingestion/demo/orders.py",
        "target": "demo/orders",
    }
    audit_path = tmp_path / ".phlo" / "audit" / "operations.jsonl"
    assert "workflow_already_exists" in audit_path.read_text(encoding="utf-8")


def test_authoring_write_routes_require_project_write_scope(monkeypatch, tmp_path) -> None:
    from phlo_api.api import authoring

    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setenv(
        "PHLO_API_TOKENS",
        '{"read-token":{"subject":"reader","scopes":["lakehouse:read"]},'
        '"project-token":{"subject":"agent","scopes":["project:write"]}}',
    )
    workflow_file = tmp_path / "workflow.py"
    workflow_file.write_text("# workflow\n", encoding="utf-8")
    monkeypatch.setattr(authoring, "_validate_workflow_file", lambda path: None)

    client = TestClient(app)
    missing = client.post(
        "/api/authoring/workflows/validate", json={"workflow_path": str(workflow_file)}
    )
    forbidden = client.post(
        "/api/authoring/workflows/validate",
        json={"workflow_path": str(workflow_file)},
        headers={"Authorization": "Bearer read-token"},
    )
    allowed = client.post(
        "/api/authoring/workflows/validate",
        json={"workflow_path": str(workflow_file)},
        headers={"Authorization": "Bearer project-token"},
    )

    assert missing.status_code == 401
    assert forbidden.status_code == 403
    assert allowed.status_code == 200
    assert allowed.json()["valid"] is True
    audit_path = tmp_path / ".phlo" / "audit" / "operations.jsonl"
    assert "validate_workflow" in audit_path.read_text(encoding="utf-8")


def test_authoring_doctor_route_returns_json(monkeypatch) -> None:
    from phlo_api.api import authoring

    monkeypatch.setattr(authoring, "_run_diagnostics_quietly", lambda verbose=False: [])

    response = TestClient(app).get("/api/authoring/doctor")

    assert response.status_code == 200
    assert response.json() == {"checks": [], "summary": {"fail": 0, "ok": 0, "skip": 0, "warn": 0}}

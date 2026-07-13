from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from phlo.capabilities import WorkflowFilePreview, WorkflowProposal
from phlo_api.main import app
from phlo_api.observatory_api import observatory
from phlo_api.observatory_api import observatory_workflow_wizard as wizard


client = TestClient(app)


@pytest.fixture(autouse=True)
def _workflow_project_write_auth(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(
        "PHLO_API_TOKENS",
        '{"project-token":{"subject":"operator","scopes":["project:write"]}}',
    )
    client.headers.update({"Authorization": "Bearer project-token"})
    yield
    client.headers.pop("Authorization", None)


def _can_load_workflow_plugin(module_name: str) -> bool:
    try:
        module = import_module(module_name)
    except Exception:
        return False
    return callable(getattr(module, "get_workflow_wizard_contributions", None))


def test_workflow_wizard_lists_package_contributions() -> None:
    response = client.get("/api/observatory/workflow-wizard")

    assert response.status_code == 200
    payload = response.json()
    ids = [item["id"] for item in payload["contributions"]]
    if _can_load_workflow_plugin("phlo_dlt.plugin"):
        assert "dlt.rest-api-source" in ids
    assert "sling.replication-source" in ids
    assert "dbt.transform" in ids
    assert "pandera.quality-checks" in ids
    assert "dagster.orchestration" in ids
    assert "openmetadata.catalog" in ids
    assert payload["stages"] == ["source", "transform", "quality", "publish"]


def test_workflow_wizard_proposal_requires_graph_nodes() -> None:
    response = client.post(
        "/api/observatory/workflow-wizard/proposals",
        json={
            "workflow_name": "customer_health",
            "domain": "customers",
            "graph": {"nodes": [], "edges": []},
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["graph"] == ["Add at least one workflow node."]


def test_workflow_wizard_proposal_requires_project_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = {
        "workflow_name": "customer_health",
        "domain": "customers",
        "graph": {
            "nodes": [
                {
                    "id": "source",
                    "contribution_id": "dlt.rest-api-source",
                    "stage": "source",
                    "values": {"table_name": "orders"},
                }
            ],
            "edges": [],
        },
    }
    client.headers.pop("Authorization", None)
    anonymous = client.post("/api/observatory/workflow-wizard/proposals", json=request)
    assert anonymous.status_code == 401

    monkeypatch.setenv(
        "PHLO_API_TOKENS",
        '{"viewer-token":{"subject":"viewer","scopes":["project:read"]}}',
    )
    viewer = client.post(
        "/api/observatory/workflow-wizard/proposals",
        json=request,
        headers={"Authorization": "Bearer viewer-token"},
    )
    assert viewer.status_code == 403


def test_workflow_wizard_builds_dlt_dbt_graph_proposal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))

    response = client.post(
        "/api/observatory/workflow-wizard/proposals",
        json={
            "workflow_name": "customer_health",
            "domain": "customers",
            "graph": {
                "nodes": [
                    {
                        "id": "source",
                        "contribution_id": "dlt.rest-api-source",
                        "stage": "source",
                        "values": {
                            "domain": "customers",
                            "table_name": "orders",
                            "unique_key": "order_id",
                            "api_base_url": "https://api.example.test",
                            "fields": ["total:float", "created_at:datetime"],
                        },
                    },
                    {
                        "id": "model",
                        "contribution_id": "dbt.transform",
                        "stage": "transform",
                        "values": {
                            "project_name": "customer_health",
                            "source_name": "raw",
                            "source_table": "orders",
                            "staging_model_name": "stg_orders",
                            "staging_source_relation": "raw.orders",
                            "dedupe_model_name": "clean_orders",
                            "partition_by": "order_id",
                            "order_by": "created_at",
                            "test_model_name": "clean_orders",
                            "unique_key": "order_id",
                        },
                    },
                ],
                "edges": [{"id": "source-model", "source": "source", "target": "model"}],
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["planned_assets"] == ["dlt_orders"]
    assert payload["planned_models"] == ["stg_orders", "clean_orders"]
    assert "workflows/ingestion/customers/orders.py" in [item["path"] for item in payload["files"]]
    assert payload["actions"][0]["enabled"] is True


def test_workflow_wizard_builds_composed_transform_graph_proposal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))

    response = client.post(
        "/api/observatory/workflow-wizard/proposals",
        json={
            "workflow_name": "recipe_catalog",
            "domain": "recipes",
            "graph": {
                "nodes": [
                    {
                        "id": "source",
                        "contribution_id": "dlt.rest-api-source",
                        "stage": "source",
                        "values": {
                            "domain": "recipes",
                            "table_name": "recipes",
                            "unique_key": "id",
                            "api_base_url": "https://dummyjson.com/recipes",
                            "response_path": "recipes",
                            "fields": ["name:str", "rating:float"],
                        },
                    },
                    {
                        "id": "transform",
                        "contribution_id": "dbt.transform",
                        "stage": "transform",
                        "values": {
                            "project_name": "recipe_catalog",
                            "source_name": "raw",
                            "source_table": "recipes",
                            "staging_model_name": "stg_recipes",
                            "staging_source_relation": "raw.recipes",
                            "filter_model_name": "filtered_recipes",
                            "where": "rating >= 4.5",
                            "dedupe_model_name": "clean_recipes",
                            "partition_by": "id",
                            "order_by": "reviewCount",
                            "test_model_name": "clean_recipes",
                            "unique_key": "id",
                        },
                    },
                ],
                "edges": [
                    {"id": "source-transform", "source": "source", "target": "transform"},
                ],
            },
        },
    )

    assert response.status_code == 200
    paths = [item["path"] for item in response.json()["files"]]
    assert "workflows/transforms/dbt/dbt_project.yml" in paths
    assert "workflows/transforms/dbt/models/sources/raw.yml" in paths
    assert "workflows/transforms/dbt/models/stg_recipes.sql" in paths
    assert "workflows/transforms/dbt/models/filtered_recipes.sql" in paths
    assert "workflows/transforms/dbt/models/clean_recipes.sql" in paths
    assert "workflows/transforms/dbt/models/clean_recipes.yml" in paths


def test_workflow_wizard_builds_quality_and_publish_graph_proposal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))

    response = client.post(
        "/api/observatory/workflow-wizard/proposals",
        json={
            "workflow_name": "recipe_catalog",
            "domain": "recipes",
            "graph": {
                "nodes": [
                    {
                        "id": "source",
                        "contribution_id": "sling.replication-source",
                        "stage": "source",
                        "values": {
                            "domain": "recipes",
                            "source_name": "POSTGRES",
                            "source_stream": "public.recipes",
                            "target_table": "recipes",
                            "primary_key": "id",
                            "replication_mode": "incremental",
                            "update_key": "updated_at",
                        },
                    },
                    {
                        "id": "quality",
                        "contribution_id": "pandera.quality-checks",
                        "stage": "quality",
                        "values": {
                            "target_table": "recipes.clean_recipes",
                            "check_name": "clean_recipes_quality",
                            "unique_key": "id",
                            "not_null_columns": "id\nname",
                            "range_checks": "rating:0:5",
                        },
                    },
                    {
                        "id": "orchestration",
                        "contribution_id": "dagster.orchestration",
                        "stage": "publish",
                        "values": {
                            "job_name": "recipe_catalog_job",
                            "asset_group": "recipes",
                            "schedule": "0 2 * * *",
                        },
                    },
                    {
                        "id": "catalog",
                        "contribution_id": "openmetadata.catalog",
                        "stage": "publish",
                        "values": {
                            "service_name": "phlo",
                            "database": "warehouse",
                            "schema": "recipes",
                            "owner": "data-platform",
                            "tags": "domain.recipes\nsource.postgres",
                        },
                    },
                ],
                "edges": [
                    {"id": "source-quality", "source": "source", "target": "quality"},
                    {"id": "quality-orchestration", "source": "quality", "target": "orchestration"},
                    {"id": "orchestration-catalog", "source": "orchestration", "target": "catalog"},
                ],
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    paths = [item["path"] for item in payload["files"]]
    assert payload["planned_assets"] == ["sling_recipes"]
    assert payload["disabled_stages"] == {}
    assert "workflows/ingestion/recipes/recipes_sling.py" in paths
    assert "workflows/ingestion/recipes/recipes_sling.yml" in paths
    assert "workflows/quality/recipes/recipes_quality.py" in paths
    assert "workflows/orchestration/recipe_catalog.py" in paths
    assert "workflows/catalog/recipes/recipe_catalog.yml" in paths


def test_workflow_wizard_apply_fails_on_conflict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setenv(
        "PHLO_API_TOKENS",
        '{"project-token":{"subject":"operator","scopes":["project:write"]}}',
    )
    existing = tmp_path / "workflows" / "ingestion" / "customers"
    existing.mkdir(parents=True)
    (existing / "orders.py").write_text("# existing\n", encoding="utf-8")

    response = client.post(
        "/api/observatory/workflow-wizard/proposals",
        json={
            "workflow_name": "customer_health",
            "domain": "customers",
            "graph": {
                "nodes": [
                    {
                        "id": "source",
                        "contribution_id": "dlt.rest-api-source",
                        "stage": "source",
                        "values": {
                            "domain": "customers",
                            "table_name": "orders",
                            "unique_key": "order_id",
                        },
                    }
                ],
                "edges": [],
            },
        },
    )
    proposal = response.json()

    assert proposal["actions"][0]["enabled"] is False
    apply_response = client.post(
        "/api/observatory/workflow-wizard/actions",
        json={"action_id": proposal["actions"][0]["id"], "proposal_id": proposal["proposal_id"]},
        headers={"Authorization": "Bearer project-token"},
    )

    assert apply_response.status_code == 409
    assert "File conflicts" in apply_response.json()["detail"]


def test_workflow_wizard_apply_records_operation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setenv(
        "PHLO_API_TOKENS",
        '{"project-token":{"subject":"operator","scopes":["project:write"]}}',
    )
    observatory._clear_read_model_cache()
    proposal_response = client.post(
        "/api/observatory/workflow-wizard/proposals",
        json={
            "workflow_name": "customer_health",
            "domain": "customers",
            "graph": {
                "nodes": [
                    {
                        "id": "source",
                        "contribution_id": "dlt.rest-api-source",
                        "stage": "source",
                        "values": {
                            "domain": "customers",
                            "table_name": "orders",
                            "unique_key": "order_id",
                        },
                    }
                ],
                "edges": [],
            },
        },
    )
    proposal = proposal_response.json()

    apply_response = client.post(
        "/api/observatory/workflow-wizard/actions",
        json={"action_id": proposal["actions"][0]["id"], "proposal_id": proposal["proposal_id"]},
        headers={"Authorization": "Bearer project-token"},
    )

    assert apply_response.status_code == 200
    operations = client.get("/api/observatory/operations").json()["items"]
    assert operations[0]["kind"] == "workflow.apply"
    assert operations[0]["status"] == "succeeded"
    assert operations[0]["metadata"]["action_id"] == proposal["actions"][0]["id"]
    assert "workflows/ingestion/customers/orders.py" in operations[0]["metadata"]["files"]


def test_workflow_wizard_conflict_records_failed_operation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setenv(
        "PHLO_API_TOKENS",
        '{"project-token":{"subject":"operator","scopes":["project:write"]}}',
    )
    observatory._clear_read_model_cache()
    existing = tmp_path / "workflows" / "ingestion" / "customers"
    existing.mkdir(parents=True)
    (existing / "orders.py").write_text("# existing\n", encoding="utf-8")
    proposal_response = client.post(
        "/api/observatory/workflow-wizard/proposals",
        json={
            "workflow_name": "customer_health",
            "domain": "customers",
            "graph": {
                "nodes": [
                    {
                        "id": "source",
                        "contribution_id": "dlt.rest-api-source",
                        "stage": "source",
                        "values": {
                            "domain": "customers",
                            "table_name": "orders",
                            "unique_key": "order_id",
                        },
                    }
                ],
                "edges": [],
            },
        },
    )
    proposal = proposal_response.json()

    apply_response = client.post(
        "/api/observatory/workflow-wizard/actions",
        json={"action_id": proposal["actions"][0]["id"], "proposal_id": proposal["proposal_id"]},
        headers={"Authorization": "Bearer project-token"},
    )

    assert apply_response.status_code == 409
    operations = client.get("/api/observatory/operations").json()["items"]
    assert operations[0]["kind"] == "workflow.apply"
    assert operations[0]["status"] == "failed"
    assert "File conflicts" in operations[0]["health"]["message"]


def test_workflow_wizard_apply_requires_project_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    proposal = client.post(
        "/api/observatory/workflow-wizard/proposals",
        json={
            "workflow_name": "customer_health",
            "domain": "customers",
            "graph": {
                "nodes": [
                    {
                        "id": "source",
                        "contribution_id": "dlt.rest-api-source",
                        "stage": "source",
                        "values": {"table_name": "orders"},
                    }
                ],
                "edges": [],
            },
        },
    ).json()
    body = {"action_id": proposal["actions"][0]["id"], "proposal_id": proposal["proposal_id"]}

    client.headers.pop("Authorization", None)
    anonymous = client.post("/api/observatory/workflow-wizard/actions", json=body)
    assert anonymous.status_code == 401

    monkeypatch.setenv(
        "PHLO_API_TOKENS",
        '{"viewer-token":{"subject":"viewer","scopes":["project:read"]}}',
    )
    viewer = client.post(
        "/api/observatory/workflow-wizard/actions",
        json=body,
        headers={"Authorization": "Bearer viewer-token"},
    )
    assert viewer.status_code == 403
    assert not (tmp_path / "workflows").exists()


def test_workflow_wizard_apply_rejects_tampered_proposal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setenv(
        "PHLO_API_TOKENS",
        '{"project-token":{"subject":"operator","scopes":["project:write"]}}',
    )
    response = client.post(
        "/api/observatory/workflow-wizard/proposals",
        json={
            "workflow_name": "customer_health",
            "domain": "customers",
            "graph": {
                "nodes": [
                    {
                        "id": "source",
                        "contribution_id": "dlt.rest-api-source",
                        "stage": "source",
                        "values": {"table_name": "orders"},
                    }
                ],
                "edges": [],
            },
        },
    )
    proposal = response.json()
    stored_path = (
        tmp_path / ".phlo" / "workflow-wizard" / "proposals" / f"{proposal['proposal_id']}.json"
    )
    stored = json.loads(stored_path.read_text(encoding="utf-8"))
    stored["proposal"]["files"][0]["path"] = str(tmp_path.parent / "sentinel.py")
    stored_path.write_text(json.dumps(stored), encoding="utf-8")

    applied = client.post(
        "/api/observatory/workflow-wizard/actions",
        json={"action_id": proposal["actions"][0]["id"], "proposal_id": proposal["proposal_id"]},
        headers={"Authorization": "Bearer project-token"},
    )

    assert applied.status_code == 409
    assert not (tmp_path.parent / "sentinel.py").exists()
    assert not (tmp_path / "workflows").exists()


def test_workflow_wizard_apply_is_idempotent_for_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setenv(
        "PHLO_API_TOKENS",
        '{"project-token":{"subject":"operator","scopes":["project:write"]}}',
    )
    proposal = client.post(
        "/api/observatory/workflow-wizard/proposals",
        json={
            "workflow_name": "customer_health",
            "domain": "customers",
            "graph": {
                "nodes": [
                    {
                        "id": "source",
                        "contribution_id": "dlt.rest-api-source",
                        "stage": "source",
                        "values": {"table_name": "orders"},
                    }
                ],
                "edges": [],
            },
        },
    ).json()
    body = {"action_id": proposal["actions"][0]["id"], "proposal_id": proposal["proposal_id"]}
    headers = {"Authorization": "Bearer project-token"}

    first = client.post("/api/observatory/workflow-wizard/actions", json=body, headers=headers)
    second = client.post("/api/observatory/workflow-wizard/actions", json=body, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == first.json()


def test_workflow_wizard_replay_detects_changed_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setenv(
        "PHLO_API_TOKENS",
        '{"project-token":{"subject":"operator","scopes":["project:write"]}}',
    )
    proposal = client.post(
        "/api/observatory/workflow-wizard/proposals",
        json={
            "workflow_name": "customer_health",
            "domain": "customers",
            "graph": {
                "nodes": [
                    {
                        "id": "source",
                        "contribution_id": "dlt.rest-api-source",
                        "stage": "source",
                        "values": {"table_name": "orders"},
                    }
                ],
                "edges": [],
            },
        },
    ).json()
    body = {"action_id": proposal["actions"][0]["id"], "proposal_id": proposal["proposal_id"]}
    headers = {"Authorization": "Bearer project-token"}
    first = client.post("/api/observatory/workflow-wizard/actions", json=body, headers=headers)
    changed = tmp_path / first.json()["files"][0]
    changed.unlink()

    replay = client.post("/api/observatory/workflow-wizard/actions", json=body, headers=headers)

    assert first.status_code == 200
    assert replay.status_code == 409
    assert "changed after completion" in replay.json()["detail"]


def test_workflow_wizard_rejects_absolute_traversal_and_symlink_paths(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-workflow-sentinel.py"
    cases = [
        "/tmp/absolute.py",
        "workflows/../outside.py",
        "workflows/../../outside.py",
    ]
    for path in cases:
        with pytest.raises(HTTPException) as error:
            wizard._validated_workflow_targets(
                tmp_path,
                WorkflowProposal(
                    workflow_name="unsafe",
                    domain="unsafe",
                    files=[WorkflowFilePreview(path=path, content="x")],
                ),
            )
        assert error.value.status_code == 400

    outside.mkdir(exist_ok=True)
    workflow_root = tmp_path / "workflows"
    workflow_root.mkdir()
    (workflow_root / "escape").symlink_to(outside, target_is_directory=True)
    with pytest.raises(HTTPException) as error:
        wizard._validated_workflow_targets(
            tmp_path,
            WorkflowProposal(
                workflow_name="unsafe",
                domain="unsafe",
                files=[WorkflowFilePreview(path="workflows/escape/file.py", content="x")],
            ),
        )
    assert error.value.status_code == 400


def test_workflow_wizard_integrity_key_is_stable_across_calls(tmp_path: Path) -> None:
    first = wizard._workflow_integrity_key(tmp_path)
    second = wizard._workflow_integrity_key(tmp_path)

    assert first == second


def test_workflow_wizard_apply_retries_after_completion_record_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proposal = wizard.build_workflow_proposal(
        tmp_path,
        wizard.ObservatoryWorkflowProposalRequest(
            workflow_name="customer_health",
            domain="customers",
            graph=wizard.ObservatoryWorkflowGraph(
                nodes=[
                    wizard.ObservatoryWorkflowGraphNode(
                        id="source",
                        contribution_id="dlt.rest-api-source",
                        stage="source",
                        values={"table_name": "orders"},
                    )
                ]
            ),
        ),
    )
    request = wizard.ObservatoryWorkflowActionRequest(
        action_id=proposal["actions"][0]["id"],
        proposal_id=proposal["proposal_id"],
    )
    original_write = wizard._write_json_atomically
    failed = False

    def fail_completion(path: Path, payload: dict[str, object]) -> None:
        nonlocal failed
        if path.parent.name == "applied" and payload.get("status") == "succeeded" and not failed:
            failed = True
            raise OSError("simulated completion-record failure")
        original_write(path, payload)

    monkeypatch.setattr(wizard, "_write_json_atomically", fail_completion)
    with pytest.raises(OSError):
        wizard.apply_workflow_action(tmp_path, request)

    monkeypatch.setattr(wizard, "_write_json_atomically", original_write)
    result = wizard.apply_workflow_action(tmp_path, request)

    assert result.status == "succeeded"
    assert len(result.files) == len(proposal["files"])


def test_workflow_wizard_integrity_key_rejects_symlink(tmp_path: Path) -> None:
    state_dir = tmp_path / ".phlo" / "workflow-wizard"
    state_dir.mkdir(parents=True)
    outside = tmp_path / "outside.key"
    outside.write_bytes(b"attacker-controlled")
    (state_dir / "integrity.key").symlink_to(outside)

    with pytest.raises(HTTPException) as error:
        wizard._workflow_integrity_key(tmp_path)

    assert error.value.status_code == 503


def test_workflow_wizard_state_directory_rejects_symlink(tmp_path: Path) -> None:
    phlo_dir = tmp_path / ".phlo"
    phlo_dir.mkdir()
    outside = tmp_path / "outside-state"
    outside.mkdir()
    (phlo_dir / "workflow-wizard").symlink_to(outside, target_is_directory=True)

    with pytest.raises(HTTPException) as error:
        wizard._proposal_state_dir(tmp_path)

    assert error.value.status_code == 503


def test_workflow_wizard_escapes_caller_values_in_generated_python(tmp_path: Path) -> None:
    marker = tmp_path / "injected-marker"
    payload = f'" or __import__("os").system("touch {marker}") or "'
    proposal = wizard.build_workflow_proposal(
        tmp_path,
        wizard.ObservatoryWorkflowProposalRequest(
            workflow_name="customer_health",
            domain="customers",
            graph=wizard.ObservatoryWorkflowGraph(
                nodes=[
                    wizard.ObservatoryWorkflowGraphNode(
                        id="source",
                        contribution_id="sling.replication-source",
                        stage="source",
                        values={
                            "table_name": "orders",
                            "source_stream": payload,
                            "source_name": payload,
                            "schedule": payload,
                        },
                    )
                ]
            ),
        ),
    )

    generated = next(
        item["content"] for item in proposal["files"] if item["path"].endswith("_sling.py")
    )
    compile(generated, "generated_sling.py", "exec")
    assert not marker.exists()

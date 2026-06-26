from __future__ import annotations

from importlib import import_module
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from phlo_api.main import app
from phlo_api.observatory_api import v2


client = TestClient(app)


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
        json={"action_id": proposal["actions"][0]["id"], "proposal": proposal},
    )

    assert apply_response.status_code == 409
    assert "File conflicts" in apply_response.json()["detail"]


def test_workflow_wizard_apply_records_operation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    v2._clear_read_model_cache()
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
        json={"action_id": proposal["actions"][0]["id"], "proposal": proposal},
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
    v2._clear_read_model_cache()
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
        json={"action_id": proposal["actions"][0]["id"], "proposal": proposal},
    )

    assert apply_response.status_code == 409
    operations = client.get("/api/observatory/operations").json()["items"]
    assert operations[0]["kind"] == "workflow.apply"
    assert operations[0]["status"] == "failed"
    assert "File conflicts" in operations[0]["health"]["message"]

from __future__ import annotations

from fastapi.testclient import TestClient

from phlo_api.main import app


client = TestClient(app)


def test_workflow_wizard_lists_package_contributions() -> None:
    response = client.get("/api/observatory/v2/workflow-wizard")

    assert response.status_code == 200
    payload = response.json()
    ids = [item["id"] for item in payload["contributions"]]
    assert "dlt.rest-api-source" in ids
    assert "dbt.initialize-project" in ids
    assert payload["stages"] == ["source", "transform", "quality", "publish"]


def test_workflow_wizard_proposal_requires_source() -> None:
    response = client.post(
        "/api/observatory/v2/workflow-wizard/proposals",
        json={
            "workflow_name": "customer_health",
            "domain": "customers",
            "selections": {},
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["source"] == ["Select a source contribution."]


def test_workflow_wizard_builds_dlt_dbt_proposal(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))

    response = client.post(
        "/api/observatory/v2/workflow-wizard/proposals",
        json={
            "workflow_name": "customer_health",
            "domain": "customers",
            "selections": {
                "source": {
                    "contribution_id": "dlt.rest-api-source",
                    "values": {
                        "domain": "customers",
                        "table_name": "orders",
                        "unique_key": "order_id",
                        "api_base_url": "https://api.example.test",
                        "fields": ["total:float", "created_at:datetime"],
                    },
                },
                "transform": {
                    "contribution_id": "dbt.basic-model",
                    "values": {"model_name": "stg_orders", "source_relation": "raw.orders"},
                },
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["planned_assets"] == ["dlt_orders"]
    assert payload["planned_models"] == ["stg_orders"]
    assert "workflows/ingestion/customers/orders.py" in [item["path"] for item in payload["files"]]
    assert payload["actions"][0]["enabled"] is True


def test_workflow_wizard_builds_composed_transform_proposal(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))

    response = client.post(
        "/api/observatory/v2/workflow-wizard/proposals",
        json={
            "workflow_name": "recipe_catalog",
            "domain": "recipes",
            "selections": {
                "source": [
                    {
                        "contribution_id": "dlt.rest-api-source",
                        "values": {
                            "domain": "recipes",
                            "table_name": "recipes",
                            "unique_key": "id",
                            "api_base_url": "https://dummyjson.com/recipes",
                            "response_path": "recipes",
                            "fields": ["name:str", "rating:float"],
                        },
                    }
                ],
                "transform": [
                    {
                        "contribution_id": "dbt.initialize-project",
                        "values": {"project_name": "recipe_catalog"},
                    },
                    {
                        "contribution_id": "dbt.source-yml",
                        "values": {"source_name": "raw", "table_name": "recipes"},
                    },
                    {
                        "contribution_id": "dbt.basic-model",
                        "values": {"model_name": "stg_recipes", "source_relation": "raw.recipes"},
                    },
                    {
                        "contribution_id": "dbt.schema-tests",
                        "values": {"model_name": "stg_recipes", "unique_key": "id"},
                    },
                ],
            },
        },
    )

    assert response.status_code == 200
    paths = [item["path"] for item in response.json()["files"]]
    assert "workflows/transforms/dbt/dbt_project.yml" in paths
    assert "workflows/transforms/dbt/models/sources/raw.yml" in paths
    assert "workflows/transforms/dbt/models/stg_recipes.sql" in paths
    assert "workflows/transforms/dbt/models/stg_recipes.yml" in paths


def test_workflow_wizard_apply_fails_on_conflict(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    existing = tmp_path / "workflows" / "ingestion" / "customers"
    existing.mkdir(parents=True)
    (existing / "orders.py").write_text("# existing\n", encoding="utf-8")

    response = client.post(
        "/api/observatory/v2/workflow-wizard/proposals",
        json={
            "workflow_name": "customer_health",
            "domain": "customers",
            "selections": {
                "source": {
                    "contribution_id": "dlt.rest-api-source",
                    "values": {
                        "domain": "customers",
                        "table_name": "orders",
                        "unique_key": "order_id",
                    },
                }
            },
        },
    )
    proposal = response.json()

    assert proposal["actions"][0]["enabled"] is False
    apply_response = client.post(
        "/api/observatory/v2/workflow-wizard/actions",
        json={"action_id": proposal["actions"][0]["id"], "proposal": proposal},
    )

    assert apply_response.status_code == 409
    assert "File conflicts" in apply_response.json()["detail"]

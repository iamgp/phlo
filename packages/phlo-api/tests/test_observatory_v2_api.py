"""Tests for the Observatory v2 provider-neutral API contract."""

from __future__ import annotations

import json
import subprocess

from fastapi.testclient import TestClient

from phlo_api.main import app
from phlo_api.observatory_api.v2 import (
    _fallback_services,
    _load_capabilities,
    _load_docker_service_statuses,
    _overview_health_from_services,
)
from phlo_api.observatory_api.v2_models import (
    V2Asset,
    V2Branch,
    V2CapabilityPage,
    V2ExternalLink,
    V2Health,
    V2Overview,
    V2QualityCheck,
    V2ResourceRef,
    V2Service,
    V2Settings,
)

_PROVIDER_URL_SETTING_NAMES = (
    "dagster_url",
    "trino_url",
    "nessie_url",
    "dagstergraphqlurl",
    "dagster_graphql_url",
    "trinourl",
    "nessieurl",
)


def _assert_no_provider_url_settings(payload: object) -> None:
    serialized = json.dumps(payload).lower()
    for setting_name in _PROVIDER_URL_SETTING_NAMES:
        assert setting_name not in serialized


def test_v2_service_serializes_provider_neutral_shape() -> None:
    service = V2Service(
        id="phlo-api",
        name="phlo-api",
        kind="api",
        status="running",
        health=V2Health(state="ok", message="healthy"),
        depends_on=["postgres"],
        impacts=["observatory"],
        links=[V2ExternalLink(label="Open", url="http://localhost:4000")],
    )

    payload = service.model_dump()

    assert payload == {
        "id": "phlo-api",
        "name": "phlo-api",
        "kind": "api",
        "status": "running",
        "health": {"state": "ok", "message": "healthy"},
        "depends_on": ["postgres"],
        "impacts": ["observatory"],
        "links": [{"label": "Open", "url": "http://localhost:4000", "kind": "external"}],
        "metadata": {},
    }
    _assert_no_provider_url_settings(payload)


def test_v2_overview_contains_resource_refs_not_provider_urls() -> None:
    overview = V2Overview(
        health=V2Health(state="warning", message="1 service needs attention"),
        counters={"services": 12, "incidents": 1},
        recent=[V2ResourceRef(kind="service", id="phlo-api", label="phlo-api")],
    )

    payload = overview.model_dump()

    assert payload["health"]["state"] == "warning"
    assert payload["recent"][0]["kind"] == "service"
    _assert_no_provider_url_settings(payload)


def test_v2_resource_models_serialize_provider_neutral_shapes() -> None:
    asset = V2Asset(
        id="raw.orders",
        name="raw.orders",
        group="raw",
        kinds=["table"],
        dependencies=["source.orders"],
        resources=["object-store"],
        checks=["not_null_order_id"],
    )
    check = V2QualityCheck(
        id="raw.orders:not_null_order_id",
        name="not_null_order_id",
        asset_id="raw.orders",
        status="unknown",
    )
    branch = V2Branch(id="main", name="main", current=True, protected=True)
    settings = V2Settings(defaults={"branch": "main"}, features={"assets": True})

    payload = {
        "asset": asset.model_dump(),
        "check": check.model_dump(),
        "branch": branch.model_dump(),
        "settings": settings.model_dump(),
    }

    assert payload["asset"]["id"] == "raw.orders"
    assert payload["check"]["asset_id"] == "raw.orders"
    assert payload["branch"]["current"] is True
    assert payload["settings"]["version"] == 2
    _assert_no_provider_url_settings(payload)


def test_v2_capability_page_serializes_provider_neutral_shape() -> None:
    page = V2CapabilityPage(
        id="branches",
        label="Changes",
        path="/v2/branches",
        available=False,
        nav=False,
        reason="Install a branching provider to compare catalog branches.",
        providers=[],
    )

    payload = page.model_dump()

    assert payload == {
        "id": "branches",
        "label": "Changes",
        "path": "/v2/branches",
        "available": False,
        "nav": False,
        "reason": "Install a branching provider to compare catalog branches.",
        "providers": [],
        "metadata": {},
    }
    _assert_no_provider_url_settings(payload)


def test_v2_fallback_services_are_deterministic_and_provider_neutral() -> None:
    payload = [service.model_dump() for service in _fallback_services()]

    assert [service["id"] for service in payload] == ["phlo-api", "observatory"]
    assert payload[1]["depends_on"] == ["phlo-api"]
    _assert_no_provider_url_settings(payload)


def test_v2_docker_statuses_match_services_without_provider_imports(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        assert args[0] == ["docker", "ps", "-a", "--format", "{{json .}}"]
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="\n".join(
                [
                    json.dumps(
                        {
                            "Names": "phlo-trino-1",
                            "State": "running",
                            "Status": "Up 3 minutes (healthy)",
                        }
                    ),
                    json.dumps(
                        {
                            "Names": "old-trino-1",
                            "State": "exited",
                            "Status": "Exited (0) yesterday",
                        }
                    ),
                    json.dumps(
                        {
                            "Names": "phlo-dagster-1",
                            "State": "created",
                            "Status": "Created",
                        }
                    ),
                ]
            ),
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    statuses = _load_docker_service_statuses({"trino", "dagster"})

    assert statuses["trino"][0] == "running"
    assert statuses["trino"][1].state == "ok"
    assert statuses["dagster"][0] == "starting"
    _assert_no_provider_url_settings(
        {
            service: {"status": status, "health": health.model_dump()}
            for service, (status, health) in statuses.items()
        }
    )


def test_v2_overview_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/v2/overview")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"health", "counters", "recent"}
    assert {
        "services",
        "operations",
        "assets",
        "tables",
        "quality",
        "incidents",
    } == set(payload["counters"])
    _assert_no_provider_url_settings(payload)


def test_v2_capabilities_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/v2/capabilities")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"version", "pages", "features", "providers"}
    pages = {page["id"]: page for page in payload["pages"]}
    assert pages["overview"]["available"] is True
    assert pages["services"]["available"] is True
    assert pages["settings"]["available"] is True
    assert pages["extensions"]["nav"] is False
    _assert_no_provider_url_settings(payload)


def test_v2_capabilities_gate_provider_pages_when_providers_are_absent(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_extensions", lambda: [])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_assets", lambda: [])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_tables", lambda: [])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_quality", lambda: [])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_logs", lambda: [])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_operations", lambda: [])

    payload = _load_capabilities().model_dump()

    pages = {page["id"]: page for page in payload["pages"]}
    assert pages["overview"]["available"] is True
    assert pages["services"]["available"] is True
    assert pages["settings"]["available"] is True
    assert pages["branches"]["available"] is False
    assert pages["branches"]["nav"] is False
    assert pages["quality"]["available"] is False
    assert pages["logs"]["available"] is False
    assert pages["extensions"]["nav"] is False
    _assert_no_provider_url_settings(payload)


def test_v2_overview_health_describes_missing_runtime_containers() -> None:
    health = _overview_health_from_services(_fallback_services())

    assert health.state == "unknown"
    assert health.message == "No runtime containers found"


def test_v2_services_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/v2/services")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items"}
    assert isinstance(payload["items"], list)
    assert payload["items"]
    assert {
        "id",
        "name",
        "kind",
        "status",
        "health",
        "depends_on",
        "impacts",
        "links",
        "metadata",
    } <= set(payload["items"][0])
    _assert_no_provider_url_settings(payload)


def test_v2_service_detail_endpoint_returns_provider_neutral_payload() -> None:
    client = TestClient(app)
    services = client.get("/api/observatory/v2/services").json()["items"]
    response = client.get(f"/api/observatory/v2/services/{services[0]['id']}")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "service",
        "dependencies",
        "dependents",
        "actions",
        "logs",
        "ports",
        "config",
    }
    assert payload["service"]["id"] == services[0]["id"]
    assert {"id", "label", "kind", "enabled", "requires_confirmation", "reason"} <= set(
        payload["actions"][0]
    )
    _assert_no_provider_url_settings(payload)


def test_v2_operations_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/v2/operations")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items"}
    assert isinstance(payload["items"], list)
    _assert_no_provider_url_settings(payload)


def test_v2_operation_detail_endpoint_returns_provider_neutral_payload() -> None:
    client = TestClient(app)
    operations = client.get("/api/observatory/v2/operations").json()["items"]
    if not operations:
        return

    response = client.get(f"/api/observatory/v2/operations/{operations[0]['id']}")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"operation", "related", "logs", "actions"}
    assert payload["operation"]["id"] == operations[0]["id"]
    _assert_no_provider_url_settings(payload)


def test_v2_assets_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/v2/assets")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items"}
    assert isinstance(payload["items"], list)
    _assert_no_provider_url_settings(payload)


def test_v2_asset_detail_endpoint_returns_related_provider_neutral_payload() -> None:
    client = TestClient(app)
    assets = client.get("/api/observatory/v2/assets").json()["items"]
    if not assets:
        return

    response = client.get(f"/api/observatory/v2/assets/{assets[0]['id']}")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "asset",
        "upstream",
        "downstream",
        "tables",
        "quality",
        "logs",
        "operations",
        "lineage",
        "materializations",
        "column_lineage",
    }
    assert payload["asset"]["id"] == assets[0]["id"]
    _assert_no_provider_url_settings(payload)


def test_v2_tables_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/v2/tables")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items"}
    assert isinstance(payload["items"], list)
    _assert_no_provider_url_settings(payload)


def test_v2_table_preview_endpoint_returns_provider_neutral_payload() -> None:
    client = TestClient(app)
    tables = client.get("/api/observatory/v2/tables").json()["items"]
    if not tables:
        return

    response = client.get(f"/api/observatory/v2/table-preview/{tables[0]['id']}")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "table",
        "columns",
        "rows",
        "row_count",
        "limit",
        "offset",
        "has_more",
    }
    assert payload["table"]["id"] == tables[0]["id"]
    _assert_no_provider_url_settings(payload)


def test_v2_query_endpoint_returns_provider_neutral_payload() -> None:
    client = TestClient(app)
    tables = client.get("/api/observatory/v2/tables").json()["items"]
    if not tables:
        return

    response = client.post(
        "/api/observatory/v2/query",
        json={"sql": f"select * from {tables[0]['name']} limit 5"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "columns",
        "rows",
        "row_count",
        "effective_sql",
        "limit",
        "offset",
        "warnings",
    }
    assert payload["limit"] == 5
    _assert_no_provider_url_settings(payload)


def test_v2_saved_queries_contract_persists_provider_neutral_payload(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    client = TestClient(app)

    create_response = client.post(
        "/api/observatory/v2/saved-queries",
        json={
            "name": "Recent orders",
            "sql": "select * from orders limit 10",
            "branch": "main",
        },
    )
    duplicate_response = client.post(
        "/api/observatory/v2/saved-queries",
        json={
            "name": "Recent orders",
            "sql": "select   *  from   orders   limit 10",
            "branch": "main",
        },
    )
    list_response = client.get("/api/observatory/v2/saved-queries")

    assert create_response.status_code == 200
    assert duplicate_response.status_code == 200
    assert list_response.status_code == 200
    created = duplicate_response.json()
    payload = list_response.json()
    assert {"id", "name", "sql", "branch", "created_at", "updated_at", "metadata"} <= set(created)
    assert any(item["id"] == created["id"] for item in payload["items"])
    assert len(payload["items"]) == 1
    _assert_no_provider_url_settings(payload)


def test_v2_stage_diff_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get(
        "/api/observatory/v2/stage-diff",
        params={"source_table_id": "orders", "target_table_id": "orders_clean"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "source",
        "target",
        "columns",
        "rows",
        "summary",
        "metadata",
    }
    assert {"added", "removed", "changed", "unchanged"} <= set(payload["summary"])
    _assert_no_provider_url_settings(payload)


def test_v2_row_journey_endpoint_returns_provider_neutral_payload() -> None:
    client = TestClient(app)
    tables = client.get("/api/observatory/v2/tables").json()["items"]
    if not tables:
        return

    response = client.get(f"/api/observatory/v2/row-journey/{tables[0]['id']}/{tables[0]['id']}:1")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "table",
        "row_id",
        "row",
        "upstream",
        "downstream",
        "stages",
        "logs",
        "diff",
    }
    _assert_no_provider_url_settings(payload)


def test_v2_branch_action_contract_returns_provider_neutral_payload(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    response = TestClient(app).post(
        "/api/observatory/v2/branches/actions",
        json={"action_id": "branch:create:review/demo"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"action", "status", "message", "operation"}
    assert payload["operation"]["target"]["kind"] == "branch"
    _assert_no_provider_url_settings(payload)


def test_v2_quality_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/v2/quality")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items"}
    assert isinstance(payload["items"], list)
    _assert_no_provider_url_settings(payload)


def test_v2_quality_detail_endpoint_returns_provider_neutral_payload() -> None:
    client = TestClient(app)
    checks = client.get("/api/observatory/v2/quality").json()["items"]
    if not checks:
        return

    response = client.get(f"/api/observatory/v2/quality/{checks[0]['id']}")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"check", "asset", "history", "logs", "actions"}
    assert payload["check"]["id"] == checks[0]["id"]
    _assert_no_provider_url_settings(payload)


def test_v2_logs_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/v2/logs")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items"}
    assert isinstance(payload["items"], list)
    _assert_no_provider_url_settings(payload)


def test_v2_log_facets_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/v2/logs/facets")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"sources", "levels", "resources"}
    _assert_no_provider_url_settings(payload)


def test_v2_branches_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/v2/branches")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items"}
    assert {
        "id": "main",
        "name": "main",
        "current": True,
        "protected": True,
        "metadata": {},
    } in payload["items"]
    _assert_no_provider_url_settings(payload)


def test_v2_branch_detail_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/v2/branches/main")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"branch", "contents", "commits", "compare", "tables"}
    assert payload["branch"]["name"] == "main"
    _assert_no_provider_url_settings(payload)


def test_v2_extensions_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/v2/extensions")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items"}
    assert isinstance(payload["items"], list)
    _assert_no_provider_url_settings(payload)


def test_v2_extension_detail_endpoint_returns_provider_neutral_payload() -> None:
    client = TestClient(app)
    extensions = client.get("/api/observatory/v2/extensions").json()["items"]
    if not extensions:
        return

    response = client.get(f"/api/observatory/v2/extensions/{extensions[0]['id']}")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"extension", "routes", "nav", "capabilities"}
    assert payload["extension"]["id"] == extensions[0]["id"]
    _assert_no_provider_url_settings(payload)


def test_v2_settings_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/v2/settings")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"version", "defaults", "features", "storage", "metadata"}
    assert payload["version"] == 2
    assert payload["defaults"]["branch"] == "main"
    _assert_no_provider_url_settings(payload)


def test_v2_search_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/v2/search", params={"q": "gold"})

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items"}
    assert isinstance(payload["items"], list)
    _assert_no_provider_url_settings(payload)


def test_v2_all_endpoints_do_not_leak_provider_url_setting_names() -> None:
    client = TestClient(app)

    for path in (
        "/api/observatory/v2/overview",
        "/api/observatory/v2/capabilities",
        "/api/observatory/v2/services",
        "/api/observatory/v2/services/phlo-api",
        "/api/observatory/v2/operations",
        "/api/observatory/v2/operations/compact:main:main",
        "/api/observatory/v2/assets",
        "/api/observatory/v2/assets/raw.orders",
        "/api/observatory/v2/tables",
        "/api/observatory/v2/table-preview/orders",
        "/api/observatory/v2/saved-queries",
        "/api/observatory/v2/stage-diff?source_table_id=orders&target_table_id=orders_clean",
        "/api/observatory/v2/row-journey/orders/orders:1",
        "/api/observatory/v2/quality",
        "/api/observatory/v2/quality/raw.orders:order_id_present",
        "/api/observatory/v2/logs",
        "/api/observatory/v2/logs/facets",
        "/api/observatory/v2/branches",
        "/api/observatory/v2/branches/main",
        "/api/observatory/v2/extensions",
        "/api/observatory/v2/settings",
        "/api/observatory/v2/search?q=gold",
    ):
        response = client.get(path)

        if response.status_code == 404:
            continue
        assert response.status_code == 200, path
        _assert_no_provider_url_settings(response.json())

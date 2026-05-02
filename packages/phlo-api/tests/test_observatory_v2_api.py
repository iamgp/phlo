"""Tests for the Observatory v2 provider-neutral API contract."""

from __future__ import annotations

import json
import subprocess

from fastapi.testclient import TestClient

from phlo_api.main import app
from phlo_api.observatory_api.v2 import (
    _execute_action,
    _fallback_services,
    _load_capabilities,
    _load_docker_service_statuses,
    _overview_health_from_services,
    _run_read_query,
    _safe_metadata,
)
from phlo_api.observatory_api.v2_models import (
    V2ActionRequest,
    V2Asset,
    V2Branch,
    V2Capabilities,
    V2CapabilityPage,
    V2Extension,
    V2ExternalLink,
    V2Health,
    V2Operation,
    V2Overview,
    V2QualityCheck,
    V2QueryRequest,
    V2ResourceRef,
    V2Service,
    V2Settings,
    V2Table,
    V2TablePreview,
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


def test_safe_metadata_removes_private_looking_values() -> None:
    metadata = _safe_metadata(
        {
            "location": "http://internal",
            "harmless_name": "postgres://user:pass@host/db",
            "nested": {
                "safe": "ok",
                "callback": "https://internal.example/callback",
                "details": ["visible", "token=secret", {"safe_nested": True, "uri": "http://gone"}],
            },
            "items": [
                {"label": "kept", "location": "http://internal"},
                "safe-item",
                "Bearer secret-token",
            ],
            "safe_name": "orders",
            "safe_count": 3,
            "safe_enabled": True,
        }
    )

    assert "location" not in metadata
    assert "harmless_name" not in metadata
    assert metadata["nested"] == {"safe": "ok", "details": ["visible", {"safe_nested": True}]}
    assert metadata["items"] == [{"label": "kept"}, "safe-item"]
    assert metadata["safe_name"] == "orders"
    assert metadata["safe_count"] == 3
    assert metadata["safe_enabled"] is True


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
        "definition_state": "available",
        "runtime_state": "unknown",
        "in_stack": False,
        "disabled": False,
        "profile": None,
        "backend": "unknown",
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


def test_v2_disabled_service_action_skips_without_subprocess(monkeypatch) -> None:
    service = V2Service(
        id="phlo-api",
        name="phlo-api",
        kind="api",
        status="running",
        health=V2Health(state="ok"),
        in_stack=True,
    )
    subprocess_calls: list[object] = []

    def fake_run(*args, **kwargs):
        subprocess_calls.append((args, kwargs))
        raise AssertionError("disabled actions must not spawn subprocesses")

    monkeypatch.setattr("phlo_api.observatory_api.v2._load_services", lambda: [service])
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = _execute_action(V2ActionRequest(action_id="phlo-api:start"))

    assert result.status == "skipped"
    assert result.action.id == "phlo-api:start"
    assert result.message == result.action.reason
    assert subprocess_calls == []
    assert result.operation is None


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
    assert set(pages) == {
        "overview",
        "data",
        "assets",
        "issues",
        "quality",
        "logs",
        "branches",
        "operations",
        "runs",
        "storage",
        "observability",
        "governance",
        "catalog",
        "apis",
        "bi",
        "extensions",
        "services",
        "settings",
    }
    assert pages["data"]["metadata"]["required_any"] == ["query_engine", "table_store"]
    assert pages["quality"]["nav"] is False
    assert pages["storage"]["nav"] is False
    assert pages["observability"]["nav"] is False
    assert pages["governance"]["nav"] is False
    assert pages["catalog"]["nav"] is False
    assert pages["apis"]["nav"] is False
    assert pages["bi"]["nav"] is False
    assert pages["extensions"]["nav"] is False
    _assert_no_provider_url_settings(payload)


def test_v2_capabilities_gate_provider_pages_when_providers_are_absent(
    monkeypatch,
) -> None:
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_capability_registry", lambda: None)

    payload = _load_capabilities().model_dump()

    pages = {page["id"]: page for page in payload["pages"]}
    assert pages["overview"]["available"] is True
    assert pages["services"]["available"] is True
    assert pages["settings"]["available"] is True
    assert pages["branches"]["available"] is False
    assert pages["branches"]["nav"] is False
    assert pages["issues"]["available"] is False
    assert pages["quality"]["available"] is False
    assert pages["quality"]["nav"] is False
    assert pages["logs"]["available"] is False
    assert pages["extensions"]["available"] is False
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


def test_v2_operation_detail_endpoint_returns_provider_neutral_payload(monkeypatch) -> None:
    client = TestClient(app)
    operation = V2Operation(
        id="compact:main:main",
        name="compact",
        kind="maintenance",
        status="succeeded",
        health=V2Health(state="ok"),
        target=V2ResourceRef(kind="branch", id="main", label="main"),
    )
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_operations", lambda: [operation])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_logs", lambda: [])

    response = client.get("/api/observatory/v2/operations/compact:main:main")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"operation", "related", "logs", "actions"}
    assert payload["operation"]["id"] == operation.id
    _assert_no_provider_url_settings(payload)


def test_v2_assets_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/v2/assets")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items"}
    assert isinstance(payload["items"], list)
    _assert_no_provider_url_settings(payload)


def test_v2_asset_detail_endpoint_returns_related_provider_neutral_payload(monkeypatch) -> None:
    client = TestClient(app)
    asset = V2Asset(id="raw.orders", name="raw.orders", group="raw", kinds=["table"])
    table = V2Table(
        id="orders",
        name="orders",
        namespace="raw",
        asset_id=asset.id,
        metadata={"columns": ["order_id", "customer_id"]},
    )
    check = V2QualityCheck(
        id="raw.orders:order_id_present",
        name="order_id_present",
        asset_id=asset.id,
        status="unknown",
    )
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_assets", lambda: [asset])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_tables", lambda: [table])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_quality", lambda: [check])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_logs", lambda: [])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_operations", lambda: [])

    response = client.get("/api/observatory/v2/assets/raw.orders")

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
    assert payload["asset"]["id"] == asset.id
    _assert_no_provider_url_settings(payload)


def test_v2_tables_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/v2/tables")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items"}
    assert isinstance(payload["items"], list)
    _assert_no_provider_url_settings(payload)


def test_v2_table_preview_endpoint_returns_provider_neutral_payload(monkeypatch) -> None:
    client = TestClient(app)
    table = V2Table(
        id="orders",
        name="orders",
        namespace="raw",
        metadata={"columns": ["order_id"], "column_types": {"order_id": "integer"}},
    )
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_tables", lambda: [table])
    monkeypatch.setattr(
        "phlo_api.observatory_api.v2._preview_from_query_engine",
        lambda *_args, **_kwargs: None,
    )

    response = client.get("/api/observatory/v2/table-preview/orders")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "table",
        "columns",
        "column_types",
        "rows",
        "row_count",
        "limit",
        "offset",
        "has_more",
    }
    assert payload["table"]["id"] == table.id
    assert len(payload["column_types"]) == len(payload["columns"])
    _assert_no_provider_url_settings(payload)


def test_v2_query_endpoint_returns_provider_neutral_payload(monkeypatch) -> None:
    client = TestClient(app)
    table = V2Table(
        id="orders",
        name="orders",
        namespace="raw",
        metadata={"columns": ["order_id"], "column_types": {"order_id": "integer"}},
    )
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_tables", lambda: [table])
    monkeypatch.setattr(
        "phlo_api.observatory_api.v2._preview_from_query_engine",
        lambda *_args, **_kwargs: None,
    )

    response = client.post(
        "/api/observatory/v2/query",
        json={"sql": "select * from orders limit 5"},
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


def test_v2_query_endpoint_rejects_unknown_tables(monkeypatch) -> None:
    client = TestClient(app)
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_tables", lambda: [])

    response = client.post(
        "/api/observatory/v2/query",
        json={"sql": "select * from arbitrary_table limit 5"},
    )

    assert response.status_code == 404
    assert "table not found" in response.json()["detail"].lower()


def test_v2_query_engine_preserves_known_table_request_offset(monkeypatch) -> None:
    async def fake_execute_trino_query(sql, *, schema=None, timeout_ms=None):
        return {
            "columns": ["order_id"],
            "rows": [{"order_id": 3}],
            "effective_query": sql,
        }

    table = V2Table(id="orders", name="orders", namespace="raw", schema_name="silver")
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_tables", lambda: [table])
    monkeypatch.setattr(
        "phlo_api.observatory_api.trino.execute_trino_query",
        fake_execute_trino_query,
    )

    result = _run_read_query(V2QueryRequest(sql="select * from orders limit 1", limit=1, offset=25))

    assert result.offset == 25


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


def test_v2_stage_diff_endpoint_returns_provider_neutral_payload(monkeypatch) -> None:
    source_table = V2Table(id="orders", name="orders", namespace="raw")
    target_table = V2Table(id="orders_clean", name="orders_clean", namespace="silver")
    previews = {
        source_table.id: V2TablePreview(
            table=source_table,
            columns=["order_id", "amount"],
            column_types=["integer", "number"],
            rows=[{"_phlo_row_id": "orders:1", "order_id": 1, "amount": 12.5}],
            row_count=1,
            limit=20,
            offset=0,
        ),
        target_table.id: V2TablePreview(
            table=target_table,
            columns=["order_id", "amount", "status"],
            column_types=["integer", "number", "string"],
            rows=[
                {
                    "_phlo_row_id": "orders_clean:1",
                    "order_id": 1,
                    "amount": 12.5,
                    "status": "clean",
                }
            ],
            row_count=1,
            limit=20,
            offset=0,
        ),
    }
    monkeypatch.setattr(
        "phlo_api.observatory_api.v2._load_table_preview",
        lambda table_id, *, limit, offset: previews[table_id],
    )

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


def test_v2_row_journey_endpoint_returns_provider_neutral_payload(monkeypatch) -> None:
    client = TestClient(app)
    table = V2Table(
        id="orders",
        name="orders",
        namespace="raw",
        asset_id="raw.orders",
        metadata={"columns": ["order_id"]},
    )
    asset = V2Asset(id="raw.orders", name="raw.orders", group="raw", kinds=["table"])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_tables", lambda: [table])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_assets", lambda: [asset])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_logs", lambda: [])
    monkeypatch.setattr(
        "phlo_api.observatory_api.v2._preview_from_query_engine",
        lambda *_args, **_kwargs: None,
    )

    response = client.get("/api/observatory/v2/row-journey/orders/orders:1")

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


def test_v2_branch_action_contract_skips_until_provider_write_contract_exists(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    response = TestClient(app).post(
        "/api/observatory/v2/branches/actions",
        json={"action_id": "branch:create:review/demo"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"action", "status", "message", "operation"}
    assert payload["status"] == "skipped"
    assert payload["action"]["enabled"] is False
    assert payload["operation"] is None
    _assert_no_provider_url_settings(payload)


def test_v2_branch_action_skips_when_branches_capability_is_unavailable(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setattr(
        "phlo_api.observatory_api.v2._load_capabilities",
        lambda: V2Capabilities(features={"branches": False}),
    )

    def fail_write(_branches):
        raise AssertionError("branch action must not write without a catalog provider")

    monkeypatch.setattr("phlo_api.observatory_api.v2._write_branches", fail_write)

    response = TestClient(app).post(
        "/api/observatory/v2/branches/actions",
        json={"action_id": "branch:create:review/demo"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "skipped"
    assert payload["action"]["kind"] == "branch.create"
    assert payload["action"]["enabled"] is False
    assert "catalog provider" in payload["message"]
    assert payload["operation"] is None


def test_v2_quality_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/v2/quality")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items"}
    assert isinstance(payload["items"], list)
    _assert_no_provider_url_settings(payload)


def test_v2_quality_detail_endpoint_returns_provider_neutral_payload(monkeypatch) -> None:
    client = TestClient(app)
    asset = V2Asset(id="raw.orders", name="raw.orders", group="raw", kinds=["table"])
    check = V2QualityCheck(
        id="raw.orders:order_id_present",
        name="order_id_present",
        asset_id=asset.id,
        status="unknown",
    )
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_assets", lambda: [asset])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_quality", lambda: [check])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_logs", lambda: [])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_operations", lambda: [])

    response = client.get("/api/observatory/v2/quality/raw.orders:order_id_present")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"check", "asset", "history", "logs", "actions"}
    assert payload["check"]["id"] == check.id
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


def test_v2_extension_detail_endpoint_returns_provider_neutral_payload(monkeypatch) -> None:
    client = TestClient(app)
    extension = V2Extension(
        id="observatory-demo",
        name="Observatory Demo",
        version="0.1.0",
        routes=["/v2/demo"],
        nav=["/v2/demo"],
    )
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_extensions", lambda: [extension])

    response = client.get("/api/observatory/v2/extensions/observatory-demo")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"extension", "routes", "nav", "capabilities"}
    assert payload["extension"]["id"] == extension.id
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

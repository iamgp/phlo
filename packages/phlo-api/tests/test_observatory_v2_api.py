"""Tests for the Observatory v2 provider-neutral API contract."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from fastapi.testclient import TestClient

from phlo.capabilities.registry import CapabilityRegistry
from phlo.capabilities.specs import CatalogSpec
from phlo_api.main import app
from phlo_api.observatory_api import v2
from phlo_api.observatory_api import v2_services
from phlo_api.observatory_api.v2 import (
    _execute_action,
    _fallback_services,
    _load_capabilities,
    _load_docker_service_statuses,
    _load_services,
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
from phlo_api.observatory_api.v2_operation_journal import append_operation

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
        assert args[0] == [
            "docker",
            "ps",
            "-a",
            "--filter",
            "label=com.docker.compose.project=phlo",
            "--format",
            "{{json .}}",
        ]
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
                            "Labels": "com.docker.compose.project=phlo,com.docker.compose.service=trino",
                        }
                    ),
                    json.dumps(
                        {
                            "Names": "old-trino-1",
                            "State": "exited",
                            "Status": "Exited (0) yesterday",
                            "Labels": "com.docker.compose.project=old,com.docker.compose.service=trino",
                        }
                    ),
                    json.dumps(
                        {
                            "Names": "phlo-dagster-1",
                            "State": "created",
                            "Status": "Created",
                            "Labels": "com.docker.compose.project=phlo,com.docker.compose.service=dagster",
                        }
                    ),
                ]
            ),
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setenv("PHLO_COMPOSE_PROJECT", "phlo")

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


def test_v2_docker_statuses_fall_back_to_socket_and_scope_project(monkeypatch, tmp_path) -> None:
    def fake_run(*args, **kwargs):
        raise OSError("docker cli missing")

    payload = [
        {
            "Id": "abc123",
            "Names": ["/phlo-postgres-1"],
            "State": "running",
            "Status": "Up 3 minutes (healthy)",
            "Labels": {
                "com.docker.compose.project": "phlo",
                "com.docker.compose.service": "postgres",
            },
        },
        {
            "Id": "def456",
            "Names": ["/other-postgres-1"],
            "State": "running",
            "Status": "Up 3 minutes (healthy)",
            "Labels": {
                "com.docker.compose.project": "other",
                "com.docker.compose.service": "postgres",
            },
        },
    ]

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("phlo_api.observatory_api.v2._DOCKER_SOCKET", str(tmp_path / "docker.sock"))
    monkeypatch.setattr("phlo_api.observatory_api.v2.Path.exists", lambda self: True)
    monkeypatch.setattr("phlo_api.observatory_api.v2._docker_socket_json", lambda path: payload)
    monkeypatch.setenv("PHLO_COMPOSE_PROJECT", "phlo")

    statuses = _load_docker_service_statuses({"postgres"})

    assert statuses["postgres"][0] == "running"
    assert statuses["postgres"][1].state == "ok"


def test_v2_load_services_includes_runtime_containers_missing_from_discovery(monkeypatch) -> None:
    containers = [
        {
            "ID": "abc123",
            "Names": "phlo-postgres-1",
            "State": "running",
            "Status": "Up 3 minutes (healthy)",
            "Labels": ("com.docker.compose.project=phlo,com.docker.compose.service=postgres"),
        }
    ]

    monkeypatch.setattr("phlo_api.observatory_api.v2._load_docker_containers", lambda: containers)
    monkeypatch.setenv("PHLO_COMPOSE_PROJECT", "phlo")

    services = _load_services()

    postgres = next(service for service in services if service.id == "postgres")
    assert postgres.in_stack is True
    assert postgres.backend == "docker"
    assert postgres.status == "running"


def test_v2_load_services_marks_registry_service_runtime_container_in_stack(
    monkeypatch,
    tmp_path: Path,
) -> None:
    containers = [
        {
            "ID": "abc123",
            "Names": "phlo-postgres-1",
            "State": "running",
            "Status": "Up 3 minutes (healthy)",
            "Labels": ("com.docker.compose.project=phlo,com.docker.compose.service=postgres"),
        }
    ]

    monkeypatch.setenv("PHLO_COMPOSE_PROJECT", "phlo")
    monkeypatch.setattr(v2_services, "load_docker_containers", lambda: containers)
    monkeypatch.setattr(
        v2_services, "load_project_docker_containers", lambda project_root: containers
    )
    monkeypatch.setattr(
        v2_services,
        "get_registry_data",
        lambda: {
            "plugins": {
                "postgres": {
                    "type": "service",
                    "package": "phlo-postgres",
                    "version": "0.1.0",
                    "description": "PostgreSQL database",
                    "tags": ["core", "database"],
                }
            }
        },
    )

    services = v2_services.load_services(tmp_path, containers=containers)

    postgres = next(service for service in services if service.id == "postgres")
    assert postgres.in_stack is True
    assert postgres.backend == "docker"
    assert postgres.status == "running"
    assert postgres.definition_state == "configured"


def test_v2_service_registry_metadata_matches_helper_services(monkeypatch) -> None:
    monkeypatch.setattr(
        v2_services,
        "get_registry_data",
        lambda: {
            "plugins": {
                "openmetadata": {
                    "type": "hooks",
                    "package": "phlo-openmetadata",
                    "version": "0.1.0",
                    "description": "OpenMetadata integration",
                    "verified": True,
                    "tags": ["metadata"],
                }
            }
        },
    )
    monkeypatch.setattr(v2_services, "_package_installed", lambda package: False)

    entries = v2_services._registry_package_entries()
    metadata = v2_services._registry_metadata("openmetadata-mysql", entries)

    assert metadata["registry_name"] == "openmetadata"
    assert metadata["package"] == "phlo-openmetadata"
    assert metadata["installable"] is True


def test_v2_docker_statuses_ignore_containers_without_project_scope(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(
                {
                    "Names": "pokehunt-postgres",
                    "State": "running",
                    "Status": "Up 3 minutes (healthy)",
                }
            ),
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.delenv("PHLO_COMPOSE_PROJECT", raising=False)
    monkeypatch.delenv("COMPOSE_PROJECT_NAME", raising=False)

    assert _load_docker_service_statuses({"postgres"}) == {}


def test_v2_capabilities_include_running_service_backed_providers(monkeypatch) -> None:
    trino = V2Service(
        id="trino",
        name="trino",
        kind="service",
        status="running",
        health=V2Health(state="ok", message="healthy"),
        in_stack=True,
    )
    loki = V2Service(
        id="loki",
        name="loki",
        kind="service",
        status="running",
        health=V2Health(state="ok", message="healthy"),
        in_stack=True,
    )

    monkeypatch.setattr("phlo_api.observatory_api.v2._load_capability_registry", lambda: None)
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_services", lambda: [trino, loki])

    capabilities = _load_capabilities()

    assert capabilities.features["data"] is True
    assert capabilities.features["logs"] is True
    assert "trino" in capabilities.providers["data"]
    assert "loki" in capabilities.providers["logs"]


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


def test_v2_available_installed_service_can_be_added_to_stack(monkeypatch) -> None:
    service = V2Service(
        id="alloy",
        name="alloy",
        kind="observability",
        status="unknown",
        health=V2Health(state="unknown"),
        in_stack=False,
        metadata={"package": "phlo-alloy", "package_installed": True},
    )
    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, returncode=0, stdout="Services added.")

    monkeypatch.setattr(v2, "_load_services", lambda: [service])
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = _execute_action(V2ActionRequest(action_id="alloy:add"))

    assert result.status == "succeeded"
    assert result.action.label == "Add to stack"
    assert commands == [["phlo", "services", "add", "alloy"]]


def test_v2_actions_endpoint_routes_add_service_action(monkeypatch, tmp_path: Path) -> None:
    service = V2Service(
        id="pgweb",
        name="pgweb",
        kind="admin",
        status="unknown",
        health=V2Health(state="unknown"),
        in_stack=False,
        metadata={"package": "phlo-pgweb", "package_installed": True},
    )
    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, returncode=0, stdout="Services added.")

    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setattr(v2, "_load_services", lambda: [service])
    monkeypatch.setattr(subprocess, "run", fake_run)
    v2._clear_read_model_cache()

    response = TestClient(app).post(
        "/api/observatory/v2/actions",
        json={"action_id": "pgweb:add"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["action"]["label"] == "Add to stack"
    assert payload["action"]["kind"] == "service.add"
    assert commands == [["phlo", "services", "add", "pgweb"]]


def test_v2_available_missing_package_service_add_is_disabled(monkeypatch) -> None:
    service = V2Service(
        id="plugin-example",
        name="plugin-example",
        kind="service",
        status="unknown",
        health=V2Health(state="unknown"),
        in_stack=False,
        metadata={"package": "phlo-plugin-example", "package_installed": False},
    )

    monkeypatch.setattr(v2, "_load_services", lambda: [service])

    result = _execute_action(V2ActionRequest(action_id="plugin-example:add"))

    assert result.status == "skipped"
    assert result.action.label == "Add to stack"
    assert result.action.enabled is False
    assert "Install phlo-plugin-example" in result.message


def test_v2_operations_endpoint_includes_journal_records(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setattr(v2, "_load_capability_registry", lambda: None)
    v2._clear_read_model_cache()
    append_operation(
        tmp_path,
        V2Operation(
            id="phlo-api:restart",
            name="Restart",
            kind="service.restart",
            status="succeeded",
            health=V2Health(state="ok", message="Restarted"),
            target=V2ResourceRef(kind="service", id="phlo-api", label="phlo-api"),
        ),
        record_id="op-restart",
        recorded_at="2026-05-16T12:00:00+00:00",
    )

    response = TestClient(app).get("/api/observatory/v2/operations")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["id"] == "op-restart"
    assert payload["items"][0]["kind"] == "service.restart"
    assert payload["items"][0]["target"]["id"] == "phlo-api"


def test_v2_generic_skipped_action_records_operation(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setattr(v2, "_load_services", lambda: [])
    monkeypatch.setattr(v2, "_load_capability_registry", lambda: None)
    v2._clear_read_model_cache()

    response = TestClient(app).post(
        "/api/observatory/v2/actions",
        json={"action_id": "quality:raw.orders:rerun"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "skipped"
    assert payload["operation"]["status"] == "skipped"
    assert payload["operation"]["kind"] == "quality.rerun"

    operations = TestClient(app).get("/api/observatory/v2/operations").json()["items"]
    assert operations[0]["id"] == payload["operation"]["id"]
    assert operations[0]["metadata"]["action_id"] == "quality:raw.orders:rerun"


def test_v2_service_action_records_subprocess_result(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setattr(v2, "_load_capability_registry", lambda: None)
    v2._clear_read_model_cache()
    service = V2Service(
        id="phlo-api",
        name="phlo-api",
        kind="api",
        status="stopped",
        health=V2Health(state="warning", message="stopped"),
        in_stack=True,
    )

    def fake_run(*args, **kwargs):
        assert args[0] == ["phlo", "services", "start", "--service", "phlo-api"]
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="phlo-api start requested\n",
        )

    monkeypatch.setattr(v2, "_load_services", lambda: [service])
    monkeypatch.setattr(subprocess, "run", fake_run)

    response = TestClient(app).post(
        "/api/observatory/v2/actions",
        json={"action_id": "phlo-api:start"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["operation"]["kind"] == "service.start"
    assert payload["operation"]["target"]["id"] == "phlo-api"

    operations = TestClient(app).get("/api/observatory/v2/operations").json()["items"]
    assert operations[0]["id"] == payload["operation"]["id"]
    assert operations[0]["status"] == "succeeded"


def test_v2_package_install_uses_trusted_registry_package(monkeypatch) -> None:
    monkeypatch.setattr(
        v2,
        "get_registry_data",
        lambda: {
            "plugins": {
                "openmetadata": {
                    "type": "service",
                    "package": "phlo-openmetadata",
                    "version": "0.1.0",
                }
            }
        },
    )
    installed: list[str] = []

    def fake_install(package_spec: str) -> tuple[bool, str]:
        installed.append(package_spec)
        return True, "installed"

    monkeypatch.setattr(v2, "_run_python_package_install", fake_install)
    monkeypatch.setattr(v2, "_load_services", lambda: [])

    response = TestClient(app).post(
        "/api/observatory/v2/packages/install",
        json={"package_name": "openmetadata"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["package_name"] == "phlo-openmetadata"
    assert installed == ["phlo-openmetadata==0.1.0"]


def test_v2_package_install_rejects_unknown_package(monkeypatch) -> None:
    monkeypatch.setattr(v2, "get_registry_data", lambda: {"plugins": {}})

    response = TestClient(app).post(
        "/api/observatory/v2/packages/install",
        json={"package_name": "not-a-phlo-package"},
    )

    assert response.status_code == 400


def test_v2_package_install_prefers_uv_add_for_uv_projects(
    monkeypatch,
    tmp_path: Path,
) -> None:
    commands: list[tuple[list[str], Path | None]] = []

    def fake_run(command, **kwargs):
        commands.append((command, kwargs.get("cwd")))
        return subprocess.CompletedProcess(command, returncode=0, stdout="ok")

    monkeypatch.setattr(v2.shutil, "which", lambda name: "/usr/bin/uv")
    monkeypatch.setattr(v2, "_uv_project_root", lambda: tmp_path)
    monkeypatch.setattr(subprocess, "run", fake_run)

    succeeded, message = v2._run_python_package_install("phlo-openmetadata==0.1.0")

    assert succeeded is True
    assert message == "ok"
    assert commands == [(["/usr/bin/uv", "add", "--active", "phlo-openmetadata==0.1.0"], tmp_path)]


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
        "workflows",
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
    assert pages["workflows"]["available"] is True
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


def test_v2_capabilities_endpoint_reloads_project_capabilities(monkeypatch) -> None:
    """Route gating must reflect package/service inventory changes immediately."""
    calls = 0

    def load_capabilities() -> V2Capabilities:
        nonlocal calls
        calls += 1
        return V2Capabilities(features={"data": calls == 2})

    monkeypatch.setattr(v2, "_load_capabilities", load_capabilities)

    first = TestClient(app).get("/api/observatory/v2/capabilities")
    second = TestClient(app).get("/api/observatory/v2/capabilities")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["features"] == {"data": False}
    assert second.json()["features"] == {"data": True}


def test_v2_capabilities_gate_provider_pages_when_providers_are_absent(
    monkeypatch,
) -> None:
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_capability_registry", lambda: None)
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_services", lambda: [])

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
    assert pages["logs"]["available"] is True
    assert pages["logs"]["nav"] is True
    assert pages["extensions"]["available"] is False
    assert pages["extensions"]["nav"] is False
    _assert_no_provider_url_settings(payload)


def test_v2_logs_include_project_phlo_logs(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    v2._clear_read_model_cache()
    log_dir = tmp_path / ".phlo" / "logs"
    log_dir.mkdir(parents=True)
    (log_dir / "20260517.log").write_text(
        json.dumps(
            {
                "timestamp": "2026-05-17T10:00:00Z",
                "level": "warning",
                "logger": "phlo.test",
                "event": "project_log_seen",
                "path": "/api/observatory/v2/logs",
            }
        )
        + "\n"
    )

    response = TestClient(app).get("/api/observatory/v2/logs")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["message"] == "project_log_seen"
    assert payload["items"][0]["source"] == "phlo.test"
    assert payload["items"][0]["level"] == "warning"


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
    monkeypatch.setattr(v2, "_load_capability_registry", lambda: None)
    v2._clear_read_model_cache()
    response = TestClient(app).post(
        "/api/observatory/v2/branches/actions",
        json={"action_id": "branch:create:review/demo"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"action", "status", "message", "operation"}
    assert payload["status"] == "skipped"
    assert payload["action"]["enabled"] is False
    assert payload["operation"]["status"] == "skipped"
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
    assert payload["operation"]["status"] == "skipped"


def test_v2_branch_action_skip_is_recorded(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setattr(v2, "_load_capability_registry", lambda: None)
    v2._clear_read_model_cache()

    response = TestClient(app).post(
        "/api/observatory/v2/branches/actions",
        json={"action_id": "branch:create:experiment"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "skipped"
    assert payload["operation"]["status"] == "skipped"
    assert payload["operation"]["kind"] == "branch.create"

    operations = TestClient(app).get("/api/observatory/v2/operations").json()["items"]
    assert operations[0]["id"] == payload["operation"]["id"]
    assert operations[0]["metadata"]["action_id"] == "branch:create:experiment"


def test_v2_branch_actions_use_registered_catalog_provider(
    monkeypatch,
    tmp_path: Path,
) -> None:
    class CatalogProvider:
        def __init__(self) -> None:
            self.branches: dict[str, str] = {}
            self.promoted: list[tuple[str, str]] = []

        def list_branches(self):
            return [
                {"name": name, "hash": hash_value} for name, hash_value in self.branches.items()
            ]

        def create_branch(self, name: str, from_ref: str = "main") -> str | None:
            self.branches[name] = f"{from_ref}-hash"
            return self.branches[name]

        def merge_branch(self, source: str, target: str = "main") -> bool:
            self.promoted.append((source, target))
            return source in self.branches

        def delete_branch(self, name: str) -> bool:
            return self.branches.pop(name, None) is not None

    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    provider = CatalogProvider()
    registry = CapabilityRegistry()
    registry.register("catalog", CatalogSpec(name="catalog", provider=provider))
    monkeypatch.setattr(v2, "_load_capability_registry", lambda: registry)
    v2._clear_read_model_cache()

    client = TestClient(app)
    create_response = client.post(
        "/api/observatory/v2/branches/actions",
        json={"action_id": "branch:create:experiment"},
    )
    promote_response = client.post(
        "/api/observatory/v2/branches/actions",
        json={"action_id": "branch:promote:experiment"},
    )
    delete_response = client.post(
        "/api/observatory/v2/branches/actions",
        json={"action_id": "branch:delete:experiment"},
    )

    assert create_response.status_code == 200
    assert create_response.json()["status"] == "succeeded"
    assert create_response.json()["operation"]["status"] == "succeeded"
    assert promote_response.status_code == 200
    assert promote_response.json()["status"] == "succeeded"
    assert provider.promoted == [("experiment", "main")]
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "succeeded"
    assert provider.branches == {}


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


def test_v2_search_endpoint_url_encodes_resource_href_segments(monkeypatch) -> None:
    client = TestClient(app)
    asset = V2Asset(id="silver/demo", name="silver/demo", group="silver", kinds=["table"])
    table = V2Table(id="analytics/demo", name="demo", namespace="analytics")
    extension = V2Extension(id="demo/ext", name="Demo Extension", version="0.1.0")
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_services", lambda: [])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_assets", lambda: [asset])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_tables", lambda: [table])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_quality", lambda: [])
    monkeypatch.setattr("phlo_api.observatory_api.v2._load_extensions", lambda: [extension])

    response = client.get("/api/observatory/v2/search", params={"q": "demo"})

    assert response.status_code == 200
    hrefs = {item["kind"]: item["href"] for item in response.json()["items"]}
    assert hrefs["asset"] == "/asset/silver%2Fdemo"
    assert hrefs["table"] == "/table/analytics%2Fdemo"
    assert hrefs["extension"] == "/extension/demo%2Fext"


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

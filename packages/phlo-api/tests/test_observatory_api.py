"""Tests for the Observatory provider-neutral API contract."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from phlo.capabilities.registry import CapabilityRegistry
from phlo.capabilities.specs import CatalogSpec
from phlo_api.main import app
from phlo_api.observatory_api import observatory
from phlo_api.observatory_api import observatory_services
from phlo_api.observatory_api.observatory import (
    _execute_action,
    _load_capabilities,
    _load_services,
    _overview_health_from_services,
    _run_read_query,
    _safe_metadata,
)
from phlo_api.observatory_api.observatory_models import (
    ObservatoryActionRequest,
    ObservatoryAsset,
    ObservatoryAssetDetail,
    ObservatoryBranch,
    ObservatoryCapabilities,
    ObservatoryCapabilityPage,
    ObservatoryExtension,
    ObservatoryExternalLink,
    ObservatoryHealth,
    ObservatoryOperation,
    ObservatoryOverview,
    ObservatoryQualityCheck,
    ObservatoryQueryRequest,
    ObservatoryResourceRef,
    ObservatoryService,
    ObservatorySettings,
    ObservatoryTable,
    ObservatoryTablePreview,
)
from phlo_api.observatory_api.observatory_operation_journal import append_operation
from phlo_api.observatory_api.observatory_services import fallback_services as _fallback_services
from phlo_api.observatory_api.observatory_services import (
    load_docker_service_statuses as _load_docker_service_statuses,
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


class _FakeOrchestratorOperations:
    def __init__(self, **handlers: Any) -> None:
        self._handlers = handlers

    async def get_run_status(self, run_id: str) -> Any:
        return await self._handlers["get_run_status"](run_id)

    async def retry_run(self, run_id: str, request: dict[str, Any]) -> Any:
        return await self._handlers["retry_run"](run_id, SimpleNamespace(**request))

    async def cancel_run(self, run_id: str, request: dict[str, Any]) -> Any:
        return await self._handlers["cancel_run"](run_id, SimpleNamespace(**request))

    async def get_materialization_history(self, asset_key_path: str, *, limit: int = 10) -> Any:
        return await self._handlers["get_materialization_history"](asset_key_path, limit)

    async def materialize_asset(self, asset_key_path: str, request: dict[str, Any]) -> Any:
        return await self._handlers["materialize_asset"](asset_key_path, SimpleNamespace(**request))

    async def backfill_asset(self, asset_key_path: str, request: dict[str, Any]) -> Any:
        return await self._handlers["backfill_asset"](asset_key_path, SimpleNamespace(**request))

    async def list_partitions(self, asset_key_path: str) -> Any:
        return await self._handlers["list_partitions"](asset_key_path)


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


def test_observatory_service_serializes_provider_neutral_shape() -> None:
    service = ObservatoryService(
        id="phlo-api",
        name="phlo-api",
        kind="api",
        status="running",
        health=ObservatoryHealth(state="ok", message="healthy"),
        depends_on=["postgres"],
        impacts=["observatory"],
        links=[ObservatoryExternalLink(label="Open", url="http://localhost:4000")],
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


def test_observatory_overview_contains_resource_refs_not_provider_urls() -> None:
    overview = ObservatoryOverview(
        health=ObservatoryHealth(state="warning", message="1 service needs attention"),
        counters={"services": 12, "incidents": 1},
        recent=[ObservatoryResourceRef(kind="service", id="phlo-api", label="phlo-api")],
    )

    payload = overview.model_dump()

    assert payload["health"]["state"] == "warning"
    assert payload["recent"][0]["kind"] == "service"
    _assert_no_provider_url_settings(payload)


def test_observatory_resource_models_serialize_provider_neutral_shapes() -> None:
    asset = ObservatoryAsset(
        id="raw.orders",
        name="raw.orders",
        group="raw",
        kinds=["table"],
        dependencies=["source.orders"],
        resources=["object-store"],
        checks=["not_null_order_id"],
    )
    check = ObservatoryQualityCheck(
        id="raw.orders:not_null_order_id",
        name="not_null_order_id",
        asset_id="raw.orders",
        status="unknown",
    )
    branch = ObservatoryBranch(id="main", name="main", current=True, protected=True)
    settings = ObservatorySettings(defaults={"branch": "main"}, features={"assets": True})

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


def test_observatory_data_products_endpoint_returns_profile_summaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observatory._clear_read_model_cache()
    monkeypatch.setattr(
        observatory,
        "_load_assets",
        lambda: [
            ObservatoryAsset(
                id="gold.orders",
                name="gold.orders",
                group="gold",
                description="Curated orders",
                kinds=["table"],
                metadata={
                    "owner": "analytics",
                    "classification": "internal",
                    "published": True,
                },
            )
        ],
    )
    monkeypatch.setattr(
        observatory,
        "_load_tables_without_catalog",
        lambda: [
            ObservatoryTable(
                id="orders",
                name="orders",
                namespace="gold",
                asset_id="gold.orders",
            )
        ],
    )
    monkeypatch.setattr(
        observatory,
        "_load_quality",
        lambda: [
            ObservatoryQualityCheck(
                id="gold.orders:not_null_order_id",
                name="not_null_order_id",
                asset_id="gold.orders",
                status="passing",
            )
        ],
    )

    response = TestClient(app).get("/api/observatory/data-products")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["id"] == "gold.orders"
    assert payload["items"][0]["owner"] == "analytics"
    assert payload["items"][0]["classifications"] == ["internal"]
    assert payload["items"][0]["publication_state"] == "published"
    assert payload["items"][0]["readiness_state"] == "ok"
    assert payload["items"][0]["candidate"] is False


def test_observatory_data_products_endpoint_returns_table_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observatory._clear_read_model_cache()
    monkeypatch.setattr(observatory, "_load_assets", lambda: [])
    monkeypatch.setattr(
        observatory,
        "_load_tables_without_catalog",
        lambda: [
            ObservatoryTable(
                id="raw_orders",
                name="raw_orders",
                namespace="raw",
                format="iceberg",
            )
        ],
    )
    monkeypatch.setattr(observatory, "_load_quality", lambda: [])

    response = TestClient(app).get("/api/observatory/data-products")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["id"] == "candidate:raw_orders"
    assert payload["items"][0]["name"] == "raw_orders"
    assert payload["items"][0]["candidate"] is True
    assert payload["items"][0]["source_refs"] == [
        {"kind": "table", "id": "raw_orders", "label": "raw_orders"}
    ]


def test_observatory_data_product_profile_collects_related_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observatory._clear_read_model_cache()
    monkeypatch.setattr(
        observatory,
        "_load_assets",
        lambda: [
            ObservatoryAsset(
                id="silver.orders",
                name="silver.orders",
                group="silver",
            ),
            ObservatoryAsset(
                id="gold.orders",
                name="gold.orders",
                group="gold",
                dependencies=["silver.orders"],
                metadata={"owner": "analytics"},
            ),
        ],
    )
    monkeypatch.setattr(
        observatory,
        "_load_tables_without_catalog",
        lambda: [
            ObservatoryTable(
                id="orders",
                name="orders",
                namespace="gold",
                asset_id="gold.orders",
            )
        ],
    )
    monkeypatch.setattr(
        observatory,
        "_load_quality",
        lambda: [
            ObservatoryQualityCheck(
                id="gold.orders:not_null_order_id",
                name="not_null_order_id",
                asset_id="gold.orders",
                status="warning",
            )
        ],
    )
    monkeypatch.setattr(observatory, "_load_logs", lambda: [])
    monkeypatch.setattr(observatory, "_load_operations", lambda: [])

    response = TestClient(app).get("/api/observatory/data-products/gold.orders")

    assert response.status_code == 200
    payload = response.json()
    assert payload["product"]["id"] == "gold.orders"
    assert payload["product"]["owner"] == "analytics"
    assert payload["product"]["readiness_state"] == "warning"
    assert payload["tables"][0]["id"] == "orders"
    assert payload["quality"][0]["name"] == "not_null_order_id"
    assert payload["upstream"][0] == {
        "kind": "asset",
        "id": "silver.orders",
        "label": "silver.orders",
    }
    assert payload["sections"]["overview"] is True
    assert payload["sections"]["quality"] is True


def test_observatory_capability_page_serializes_provider_neutral_shape() -> None:
    page = ObservatoryCapabilityPage(
        id="branches",
        label="Changes",
        path="/branches",
        available=False,
        nav=False,
        reason="Install a branching provider to compare catalog branches.",
        providers=[],
    )

    payload = page.model_dump()

    assert payload == {
        "id": "branches",
        "label": "Changes",
        "path": "/branches",
        "available": False,
        "nav": False,
        "reason": "Install a branching provider to compare catalog branches.",
        "providers": [],
        "metadata": {},
    }
    _assert_no_provider_url_settings(payload)


def test_observatory_fallback_services_are_deterministic_and_provider_neutral() -> None:
    payload = [service.model_dump() for service in _fallback_services()]

    assert [service["id"] for service in payload] == ["phlo-api", "observatory"]
    assert payload[1]["depends_on"] == ["phlo-api"]
    _assert_no_provider_url_settings(payload)


def test_observatory_docker_statuses_match_services_without_provider_imports(monkeypatch) -> None:
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


def test_observatory_docker_statuses_fall_back_to_socket_and_scope_project(
    monkeypatch, tmp_path
) -> None:
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
    monkeypatch.setattr(
        "phlo_api.observatory_api.observatory_services.DOCKER_SOCKET",
        str(tmp_path / "docker.sock"),
    )
    monkeypatch.setattr(
        "phlo_api.observatory_api.observatory_services.Path.exists", lambda self: True
    )
    monkeypatch.setattr(
        "phlo_api.observatory_api.observatory_services.docker_socket_json",
        lambda path, socket_path=str(tmp_path / "docker.sock"): payload,
    )
    monkeypatch.setenv("PHLO_COMPOSE_PROJECT", "phlo")

    statuses = _load_docker_service_statuses({"postgres"})

    assert statuses["postgres"][0] == "running"
    assert statuses["postgres"][1].state == "ok"


def test_observatory_load_services_includes_runtime_containers_missing_from_discovery(
    monkeypatch,
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

    monkeypatch.setattr(
        "phlo_api.observatory_api.observatory.load_project_docker_containers",
        lambda _project_root: containers,
    )
    monkeypatch.setenv("PHLO_COMPOSE_PROJECT", "phlo")

    services = _load_services()

    postgres = next(service for service in services if service.id == "postgres")
    assert postgres.in_stack is True
    assert postgres.backend == "docker"
    assert postgres.status == "running"


def test_observatory_load_services_uses_project_scoped_container_loader(
    monkeypatch, tmp_path
) -> None:
    containers = [{"Names": "phlo-postgres-1"}]
    observed: dict[str, object] = {}

    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))

    def fake_project_containers(project_root: Path) -> list[dict[str, str]]:
        observed["project_root"] = project_root
        return containers

    monkeypatch.setattr(
        "phlo_api.observatory_api.observatory.load_project_docker_containers",
        fake_project_containers,
    )
    monkeypatch.setattr(
        "phlo_api.observatory_api.observatory._load_services_impl",
        lambda project_root, containers: (
            observed.update(
                loader_project_root=project_root,
                containers=containers,
            )
            or []
        ),
    )

    assert _load_services() == []
    assert observed["project_root"] == tmp_path.resolve()
    assert observed["loader_project_root"] == tmp_path.resolve()
    assert observed["containers"] is containers


def test_observatory_load_services_marks_registry_service_runtime_container_in_stack(
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
    monkeypatch.setattr(observatory_services, "load_docker_containers", lambda: containers)
    monkeypatch.setattr(
        observatory_services, "load_project_docker_containers", lambda project_root: containers
    )
    monkeypatch.setattr(
        observatory_services,
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

    services = observatory_services.load_services(tmp_path, containers=containers)

    postgres = next(service for service in services if service.id == "postgres")
    assert postgres.in_stack is True
    assert postgres.backend == "docker"
    assert postgres.status == "running"
    assert postgres.definition_state == "configured"


def test_observatory_service_registry_metadata_matches_helper_services(monkeypatch) -> None:
    monkeypatch.setattr(
        observatory_services,
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
    monkeypatch.setattr(observatory_services, "_package_installed", lambda package: False)

    entries = observatory_services._registry_package_entries()
    metadata = observatory_services._registry_metadata("openmetadata-mysql", entries)

    assert metadata["registry_name"] == "openmetadata"
    assert metadata["package"] == "phlo-openmetadata"
    assert metadata["installable"] is True


def test_observatory_docker_statuses_ignore_containers_without_project_scope(monkeypatch) -> None:
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


def test_observatory_capabilities_include_running_service_backed_providers(monkeypatch) -> None:
    trino = ObservatoryService(
        id="trino",
        name="trino",
        kind="service",
        status="running",
        health=ObservatoryHealth(state="ok", message="healthy"),
        in_stack=True,
    )
    loki = ObservatoryService(
        id="loki",
        name="loki",
        kind="service",
        status="running",
        health=ObservatoryHealth(state="ok", message="healthy"),
        in_stack=True,
    )

    monkeypatch.setattr(
        "phlo_api.observatory_api.observatory._load_capability_registry", lambda: None
    )
    monkeypatch.setattr(
        "phlo_api.observatory_api.observatory._load_services", lambda: [trino, loki]
    )

    capabilities = _load_capabilities()

    assert capabilities.features["data"] is True
    assert capabilities.features["logs"] is True
    assert "trino" in capabilities.providers["data"]
    assert "loki" in capabilities.providers["logs"]


def test_observatory_disabled_service_action_skips_without_subprocess(monkeypatch) -> None:
    service = ObservatoryService(
        id="phlo-api",
        name="phlo-api",
        kind="api",
        status="running",
        health=ObservatoryHealth(state="ok"),
        in_stack=True,
    )
    subprocess_calls: list[object] = []

    def fake_run(*args, **kwargs):
        subprocess_calls.append((args, kwargs))
        raise AssertionError("disabled actions must not spawn subprocesses")

    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_services", lambda: [service])
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = _execute_action(ObservatoryActionRequest(action_id="phlo-api:start"))

    assert result.status == "skipped"
    assert result.action.id == "phlo-api:start"
    assert result.message == result.action.reason
    assert subprocess_calls == []
    assert result.operation is None


def test_observatory_available_installed_service_can_be_added_to_stack(monkeypatch) -> None:
    service = ObservatoryService(
        id="alloy",
        name="alloy",
        kind="observability",
        status="unknown",
        health=ObservatoryHealth(state="unknown"),
        in_stack=False,
        metadata={"package": "phlo-alloy", "package_installed": True},
    )
    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, returncode=0, stdout="Services added.")

    monkeypatch.setattr(observatory, "_load_services", lambda: [service])
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = _execute_action(ObservatoryActionRequest(action_id="alloy:add"))

    assert result.status == "succeeded"
    assert result.action.label == "Add to stack"
    assert commands == [["phlo", "services", "add", "alloy"]]


def test_observatory_actions_endpoint_routes_add_service_action(
    monkeypatch, tmp_path: Path
) -> None:
    service = ObservatoryService(
        id="pgweb",
        name="pgweb",
        kind="admin",
        status="unknown",
        health=ObservatoryHealth(state="unknown"),
        in_stack=False,
        metadata={"package": "phlo-pgweb", "package_installed": True},
    )
    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, returncode=0, stdout="Services added.")

    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setattr(observatory, "_load_services", lambda: [service])
    monkeypatch.setattr(subprocess, "run", fake_run)
    observatory._clear_read_model_cache()

    response = TestClient(app).post(
        "/api/observatory/actions",
        json={"action_id": "pgweb:add"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["action"]["label"] == "Add to stack"
    assert payload["action"]["kind"] == "service.add"
    assert commands == [["phlo", "services", "add", "pgweb"]]


def test_observatory_asset_operational_routes_use_observatory_paths(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setenv(
        "PHLO_API_TOKENS",
        '{"operate-token":{"subject":"agent","scopes":["lakehouse:operate"]}}',
    )
    calls: list[tuple[str, str, object]] = []

    async def fake_history(asset_id: str, limit: int = 10, dagster_url: str | None = None):
        calls.append(("history", asset_id, limit))
        return [{"run_id": "run-123", "timestamp": "2026-01-01T00:00:00Z"}]

    async def fake_materialize(asset_id: str, payload, dagster_url: str | None = None):
        calls.append(("materialize", asset_id, payload.partition_key))
        return {
            "operation": "materialize_asset",
            "dry_run": payload.dry_run,
            "accepted": True,
            "asset_key_path": asset_id,
            "partition_key": payload.partition_key,
            "status": "DRY_RUN",
            "message": "Materialization request is valid.",
            "details": {},
        }

    async def fake_backfill(asset_id: str, payload, dagster_url: str | None = None):
        calls.append(("backfill", asset_id, payload.partitions))
        return {
            "operation": "backfill_asset",
            "dry_run": payload.dry_run,
            "accepted": True,
            "asset_key_path": asset_id,
            "status": "DRY_RUN",
            "message": "Backfill request is valid.",
            "details": {"partitions": payload.partitions},
        }

    async def fake_partitions(asset_id: str, dagster_url: str | None = None):
        calls.append(("partitions", asset_id, None))
        return [{"partition_key": "2026-04-26", "status": "UNKNOWN"}]

    provider = _FakeOrchestratorOperations(
        get_materialization_history=fake_history,
        materialize_asset=fake_materialize,
        backfill_asset=fake_backfill,
        list_partitions=fake_partitions,
    )
    monkeypatch.setattr(observatory, "resolve_orchestrator_operations", lambda: provider)

    client = TestClient(app)
    headers = {"Authorization": "Bearer operate-token"}
    history = client.get("/api/observatory/assets/silver/orders/materializations?limit=3")
    materialize = client.post(
        "/api/observatory/assets/silver/orders/materialize",
        json={"dry_run": True, "partition": "2026-04-26"},
        headers=headers,
    )
    backfill = client.post(
        "/api/observatory/assets/silver/orders/backfill",
        json={"dry_run": True, "partitions": ["2026-04-26"]},
        headers=headers,
    )
    partitions = client.get("/api/observatory/assets/silver/orders/partitions")

    assert history.status_code == 200
    assert history.json()[0]["run_id"] == "run-123"
    assert materialize.status_code == 200
    assert materialize.json()["asset_key_path"] == "silver/orders"
    assert backfill.status_code == 200
    assert backfill.json()["operation"] == "backfill_asset"
    assert partitions.status_code == 200
    assert partitions.json()[0]["partition_key"] == "2026-04-26"
    assert calls == [
        ("history", "silver/orders", 3),
        ("materialize", "silver/orders", "2026-04-26"),
        ("backfill", "silver/orders", ["2026-04-26"]),
        ("partitions", "silver/orders", None),
    ]


def test_observatory_asset_materializations_clamps_limit(monkeypatch) -> None:
    calls: list[int] = []

    async def fake_history(asset_id: str, limit: int = 10, dagster_url: str | None = None):
        calls.append(limit)
        return []

    provider = _FakeOrchestratorOperations(get_materialization_history=fake_history)
    monkeypatch.setattr(observatory, "resolve_orchestrator_operations", lambda: provider)

    client = TestClient(app)
    too_low = client.get("/api/observatory/assets/silver/orders/materializations?limit=0")
    too_high = client.get("/api/observatory/assets/silver/orders/materializations?limit=999")

    assert too_low.status_code == 200
    assert too_high.status_code == 200
    assert calls == [1, 200]


def test_observatory_run_operational_routes_use_observatory_paths(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setenv(
        "PHLO_API_TOKENS",
        '{"operate-token":{"subject":"agent","scopes":["lakehouse:operate"]}}',
    )
    calls: list[tuple[str, str, object]] = []

    async def fake_status(run_id: str, dagster_url: str | None = None):
        calls.append(("status", run_id, None))
        return {"run_id": run_id, "status": "FAILURE"}

    async def fake_retry(run_id: str, payload, dagster_url: str | None = None):
        calls.append(("retry", run_id, payload.dry_run))
        return {
            "operation": "retry_failed_run",
            "dry_run": payload.dry_run,
            "accepted": True,
            "run_id": run_id,
            "status": "DRY_RUN",
            "message": "Run retry request is valid.",
            "details": {"run_status": "FAILURE"},
        }

    async def fake_cancel(run_id: str, payload, dagster_url: str | None = None):
        calls.append(("cancel", run_id, payload.reason, payload.idempotency_key))
        return {
            "operation": "cancel_run",
            "dry_run": False,
            "accepted": True,
            "run_id": run_id,
            "status": "CANCELING",
            "message": "Dagster accepted run cancellation.",
            "details": {},
        }

    provider = _FakeOrchestratorOperations(
        get_run_status=fake_status,
        retry_run=fake_retry,
        cancel_run=fake_cancel,
    )
    monkeypatch.setattr(observatory, "resolve_orchestrator_operations", lambda: provider)

    client = TestClient(app)
    headers = {"Authorization": "Bearer operate-token"}
    status = client.get("/api/observatory/runs/run-123/status")
    retry = client.post(
        "/api/observatory/runs/run-123/retry", json={"dry_run": False}, headers=headers
    )
    cancel = client.post(
        "/api/observatory/runs/run-123/cancel",
        json={"reason": "stuck", "idempotency_key": "cancel-key"},
        headers=headers,
    )

    assert status.status_code == 200
    assert status.json()["status"] == "FAILURE"
    assert retry.status_code == 200
    assert retry.json()["run_id"] == "run-123"
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "CANCELING"
    assert calls == [
        ("status", "run-123", None),
        ("retry", "run-123", False),
        ("cancel", "run-123", "stuck", "cancel-key"),
    ]


def test_observatory_operation_routes_enforce_scope_idempotency_audit_and_rate_limit(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setenv("PHLO_API_RATE_LIMIT_MATERIALIZE", "2")
    monkeypatch.setenv(
        "PHLO_API_TOKENS",
        json.dumps(
            {
                "read-token": {"subject": "reader", "scopes": ["lakehouse:read"]},
                "operate-token": {"subject": "operator-idem", "scopes": ["lakehouse:operate"]},
                "limited-token": {"subject": "operator-limited", "scopes": ["lakehouse:operate"]},
            }
        ),
    )
    calls: list[str] = []

    async def fake_materialize(asset_id: str, payload, dagster_url: str | None = None):
        calls.append(asset_id)
        return {
            "operation": "materialize_asset",
            "dry_run": payload.dry_run,
            "accepted": True,
            "run_id": f"run-{len(calls)}",
            "asset_key_path": asset_id,
            "partition_key": payload.partition_key,
            "status": "STARTED",
            "message": "Dagster accepted materialize_asset.",
            "details": {},
        }

    provider = _FakeOrchestratorOperations(materialize_asset=fake_materialize)
    monkeypatch.setattr(observatory, "resolve_orchestrator_operations", lambda: provider)
    client = TestClient(app)

    missing = client.post(
        "/api/observatory/assets/silver/orders/materialize",
        json={"dry_run": False},
    )
    forbidden = client.post(
        "/api/observatory/assets/silver/orders/materialize",
        json={"dry_run": False},
        headers={"Authorization": "Bearer read-token"},
    )
    first = client.post(
        "/api/observatory/assets/silver/orders/materialize",
        json={"dry_run": False, "idempotency_key": "same-key"},
        headers={"Authorization": "Bearer operate-token"},
    )
    replay = client.post(
        "/api/observatory/assets/silver/orders/materialize",
        json={"dry_run": False, "idempotency_key": "same-key"},
        headers={"Authorization": "Bearer operate-token"},
    )
    limited_first = client.post(
        "/api/observatory/assets/silver/orders/materialize",
        json={"dry_run": True},
        headers={"Authorization": "Bearer limited-token"},
    )
    limited_second = client.post(
        "/api/observatory/assets/silver/orders/materialize",
        json={"dry_run": True},
        headers={"Authorization": "Bearer limited-token"},
    )
    limited_third = client.post(
        "/api/observatory/assets/silver/orders/materialize",
        json={"dry_run": True},
        headers={"Authorization": "Bearer limited-token"},
    )

    assert missing.status_code == 401
    assert forbidden.status_code == 403
    assert first.status_code == 200
    assert replay.status_code == 200
    assert first.json()["run_id"] == "run-1"
    assert replay.json()["run_id"] == "run-1"
    assert limited_first.status_code == 200
    assert limited_second.status_code == 200
    assert limited_third.status_code == 429
    assert calls == ["silver/orders", "silver/orders", "silver/orders"]

    audit_path = tmp_path / ".phlo" / "audit" / "operations.jsonl"
    assert audit_path.exists()
    records = [json.loads(line) for line in audit_path.read_text().splitlines()]
    assert any(record["operation"] == "materialize_asset" for record in records)
    assert all(record["subject"] != "read-token" for record in records)


def test_observatory_available_missing_package_service_add_is_disabled(monkeypatch) -> None:
    service = ObservatoryService(
        id="plugin-example",
        name="plugin-example",
        kind="service",
        status="unknown",
        health=ObservatoryHealth(state="unknown"),
        in_stack=False,
        metadata={"package": "phlo-plugin-example", "package_installed": False},
    )

    monkeypatch.setattr(observatory, "_load_services", lambda: [service])

    result = _execute_action(ObservatoryActionRequest(action_id="plugin-example:add"))

    assert result.status == "skipped"
    assert result.action.label == "Add to stack"
    assert result.action.enabled is False
    assert "Install phlo-plugin-example" in result.message


def test_observatory_operations_endpoint_includes_journal_records(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setattr(observatory, "_load_capability_registry", lambda: None)
    observatory._clear_read_model_cache()
    append_operation(
        tmp_path,
        ObservatoryOperation(
            id="phlo-api:restart",
            name="Restart",
            kind="service.restart",
            status="succeeded",
            health=ObservatoryHealth(state="ok", message="Restarted"),
            target=ObservatoryResourceRef(kind="service", id="phlo-api", label="phlo-api"),
        ),
        record_id="op-restart",
        recorded_at="2026-05-16T12:00:00+00:00",
    )

    response = TestClient(app).get("/api/observatory/operations")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["id"] == "op-restart"
    assert payload["items"][0]["kind"] == "service.restart"
    assert payload["items"][0]["target"]["id"] == "phlo-api"


def test_observatory_manifest_records_enrich_lakehouse_surfaces(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setattr(observatory, "_load_capability_registry", lambda: None)
    state_dir = tmp_path / ".phlo" / "observatory"
    state_dir.mkdir(parents=True)
    (state_dir / "lakehouse_manifest.json").write_text(
        json.dumps(
            {
                "assets": [
                    {
                        "id": "gold/keystone_release_metrics",
                        "name": "gold/keystone_release_metrics",
                        "group": "gold",
                        "description": "Release analytics generated from Keystone runs.",
                        "kinds": ["table", "analytics"],
                    }
                ],
                "tables": [
                    {
                        "id": "gold.keystone_release_metrics",
                        "name": "keystone_release_metrics",
                        "namespace": "gold",
                        "asset_id": "gold/keystone_release_metrics",
                        "format": "duckdb",
                        "metadata": {
                            "records": 2,
                            "columns": [
                                {"name": "experiment_id", "type": "varchar"},
                                {"name": "package_size_mb", "type": "double"},
                            ],
                            "preview_rows": [
                                {
                                    "experiment_id": "EXP-0041",
                                    "package_size_mb": 2.35,
                                },
                                {
                                    "experiment_id": "EXP-0048",
                                    "package_size_mb": 3.03,
                                },
                            ],
                        },
                    }
                ],
                "quality": [
                    {
                        "id": "gold/keystone_release_metrics:freshness",
                        "name": "freshness",
                        "asset_id": "gold/keystone_release_metrics",
                        "status": "passing",
                        "blocking": True,
                    }
                ],
                "operations": [
                    {
                        "id": "keystone:package:EXP-0041",
                        "name": "Package EXP-0041",
                        "kind": "pipeline.package",
                        "status": "succeeded",
                        "health": {"state": "ok"},
                        "target": {
                            "kind": "asset",
                            "id": "gold/keystone_release_metrics",
                            "label": "gold/keystone_release_metrics",
                        },
                    }
                ],
                "runs": [
                    {
                        "id": "keystone-run-0041",
                        "name": "Keystone export catalog",
                        "status": "succeeded",
                        "started_at": "2026-05-17T20:00:25+01:00",
                        "completed_at": "2026-05-17T20:03:02+01:00",
                        "duration_seconds": 157,
                        "assets": [
                            {
                                "kind": "asset",
                                "id": "gold/keystone_release_metrics",
                                "label": "gold/keystone_release_metrics",
                            }
                        ],
                    }
                ],
                "logs": [
                    {
                        "id": "keystone-log-1",
                        "timestamp": "2026-05-17T20:03:02+01:00",
                        "level": "info",
                        "message": "Experiment package created",
                        "source": "keystone_pipeline",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    observatory._clear_read_model_cache()

    client = TestClient(app)
    assets = client.get("/api/observatory/assets").json()["items"]
    tables = client.get("/api/observatory/tables").json()["items"]
    quality = client.get("/api/observatory/quality").json()["items"]
    operations = client.get("/api/observatory/operations").json()["items"]
    runs = client.get("/api/observatory/runs").json()["items"]
    logs = client.get("/api/observatory/logs").json()["items"]
    preview = client.get("/api/observatory/table-preview/gold.keystone_release_metrics").json()
    capabilities = client.get("/api/observatory/capabilities").json()

    assert assets[0]["id"] == "gold/keystone_release_metrics"
    assert tables[0]["metadata"]["records"] == 2
    assert quality[0]["status"] == "passing"
    assert operations[0]["kind"] == "pipeline.package"
    assert runs[0]["id"] == "keystone-run-0041"
    assert logs[0]["source"] == "keystone_pipeline"
    assert preview["rows"][0]["experiment_id"] == "EXP-0041"
    assert capabilities["features"]["data"] is True
    assert capabilities["features"]["assets"] is True
    assert capabilities["features"]["issues"] is True
    assert capabilities["features"]["runs"] is True


def test_observatory_generic_skipped_action_records_operation(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setattr(observatory, "_load_services", lambda: [])
    monkeypatch.setattr(observatory, "_load_capability_registry", lambda: None)
    observatory._clear_read_model_cache()

    response = TestClient(app).post(
        "/api/observatory/actions",
        json={"action_id": "quality:raw.orders:rerun"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "skipped"
    assert payload["operation"]["status"] == "skipped"
    assert payload["operation"]["kind"] == "quality.rerun"

    operations = TestClient(app).get("/api/observatory/operations").json()["items"]
    assert operations[0]["id"] == payload["operation"]["id"]
    assert operations[0]["metadata"]["action_id"] == "quality:raw.orders:rerun"


def test_observatory_service_action_records_subprocess_result(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setattr(observatory, "_load_capability_registry", lambda: None)
    observatory._clear_read_model_cache()
    service = ObservatoryService(
        id="phlo-api",
        name="phlo-api",
        kind="api",
        status="stopped",
        health=ObservatoryHealth(state="warning", message="stopped"),
        in_stack=True,
    )

    def fake_run(*args, **kwargs):
        assert args[0] == ["phlo", "services", "start", "--service", "phlo-api"]
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="phlo-api start requested\n",
        )

    monkeypatch.setattr(observatory, "_load_services", lambda: [service])
    monkeypatch.setattr(subprocess, "run", fake_run)

    response = TestClient(app).post(
        "/api/observatory/actions",
        json={"action_id": "phlo-api:start"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["operation"]["kind"] == "service.start"
    assert payload["operation"]["target"]["id"] == "phlo-api"

    operations = TestClient(app).get("/api/observatory/operations").json()["items"]
    assert operations[0]["id"] == payload["operation"]["id"]
    assert operations[0]["status"] == "succeeded"


def test_observatory_package_install_uses_trusted_registry_package(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setenv(
        "PHLO_API_TOKENS",
        '{"admin-token":{"subject":"admin","scopes":["admin"]}}',
    )
    monkeypatch.setattr(
        observatory,
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

    monkeypatch.setattr(observatory, "_run_python_package_install", fake_install)
    monkeypatch.setattr(observatory, "_load_services", lambda: [])

    response = TestClient(app).post(
        "/api/observatory/packages/install",
        json={"package_name": "openmetadata"},
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["package_name"] == "phlo-openmetadata"
    assert installed == ["phlo-openmetadata==0.1.0"]


def test_observatory_package_install_rejects_unknown_package(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setenv(
        "PHLO_API_TOKENS",
        '{"admin-token":{"subject":"admin","scopes":["admin"]}}',
    )
    monkeypatch.setattr(observatory, "get_registry_data", lambda: {"plugins": {}})

    response = TestClient(app).post(
        "/api/observatory/packages/install",
        json={"package_name": "not-a-phlo-package"},
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 400


def test_observatory_package_install_prefers_uv_add_for_uv_projects(
    monkeypatch,
    tmp_path: Path,
) -> None:
    commands: list[tuple[list[str], Path | None]] = []

    def fake_run(command, **kwargs):
        commands.append((command, kwargs.get("cwd")))
        return subprocess.CompletedProcess(command, returncode=0, stdout="ok")

    monkeypatch.setattr(observatory.shutil, "which", lambda name: "/usr/bin/uv")
    monkeypatch.setattr(observatory, "_uv_project_root", lambda: tmp_path)
    monkeypatch.setattr(subprocess, "run", fake_run)

    succeeded, message = observatory._run_python_package_install("phlo-openmetadata==0.1.0")

    assert succeeded is True
    assert message == "ok"
    assert commands == [(["/usr/bin/uv", "add", "--active", "phlo-openmetadata==0.1.0"], tmp_path)]


def test_observatory_overview_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/overview")

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


def test_observatory_capabilities_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/capabilities")

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


def test_observatory_capabilities_endpoint_reloads_project_capabilities(monkeypatch) -> None:
    """Route gating must reflect package/service inventory changes immediately."""
    calls = 0

    def load_capabilities() -> ObservatoryCapabilities:
        nonlocal calls
        calls += 1
        return ObservatoryCapabilities(features={"data": calls == 2})

    monkeypatch.setattr(observatory, "_load_capabilities", load_capabilities)

    first = TestClient(app).get("/api/observatory/capabilities")
    second = TestClient(app).get("/api/observatory/capabilities")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["features"] == {"data": False}
    assert second.json()["features"] == {"data": True}


def test_observatory_capabilities_gate_provider_pages_when_providers_are_absent(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "phlo_api.observatory_api.observatory._load_capability_registry", lambda: None
    )
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_services", lambda: [])

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


def test_observatory_logs_include_project_phlo_logs(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    observatory._clear_read_model_cache()
    log_dir = tmp_path / ".phlo" / "logs"
    log_dir.mkdir(parents=True)
    (log_dir / "20260517.log").write_text(
        json.dumps(
            {
                "timestamp": "2026-05-17T10:00:00Z",
                "level": "warning",
                "logger": "phlo.test",
                "event": "project_log_seen",
                "path": "/api/observatory/logs",
            }
        )
        + "\n"
    )

    response = TestClient(app).get("/api/observatory/logs")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["message"] == "project_log_seen"
    assert payload["items"][0]["source"] == "phlo.test"
    assert payload["items"][0]["level"] == "warning"


def test_observatory_overview_health_describes_missing_runtime_containers() -> None:
    health = _overview_health_from_services(_fallback_services())

    assert health.state == "unknown"
    assert health.message == "No runtime containers found"


def test_observatory_services_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/services")

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


def test_observatory_service_detail_endpoint_returns_provider_neutral_payload() -> None:
    client = TestClient(app)
    services = client.get("/api/observatory/services").json()["items"]
    response = client.get(f"/api/observatory/services/{services[0]['id']}")

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


def test_observatory_operations_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/operations")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items"}
    assert isinstance(payload["items"], list)
    _assert_no_provider_url_settings(payload)


def test_observatory_operations_endpoint_filters_before_returning_context_candidates(
    monkeypatch,
) -> None:
    operations = [
        ObservatoryOperation(
            id="op-orders-failed",
            name="Apply orders workflow",
            kind="workflow.apply",
            status="failed",
            health=ObservatoryHealth(state="error", message="Validation failed"),
            target=ObservatoryResourceRef(kind="workflow", id="orders", label="orders"),
        ),
        ObservatoryOperation(
            id="op-customers-failed",
            name="Apply customers workflow",
            kind="workflow.apply",
            status="failed",
            health=ObservatoryHealth(state="error", message="Validation failed"),
            target=ObservatoryResourceRef(kind="workflow", id="customers", label="customers"),
        ),
        ObservatoryOperation(
            id="op-orders-restart",
            name="Restart API",
            kind="service.restart",
            status="succeeded",
            health=ObservatoryHealth(state="ok"),
            target=ObservatoryResourceRef(kind="service", id="phlo-api", label="phlo-api"),
        ),
    ]
    monkeypatch.setattr(observatory, "_load_operations", lambda: operations)
    observatory._clear_read_model_cache()

    response = TestClient(app).get(
        "/api/observatory/operations",
        params={"status": "failed", "kind": "workflow.apply", "q": "orders", "limit": 1},
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["items"]] == ["op-orders-failed"]
    _assert_no_provider_url_settings(payload)


def test_observatory_operation_detail_endpoint_returns_provider_neutral_payload(
    monkeypatch,
) -> None:
    client = TestClient(app)
    operation = ObservatoryOperation(
        id="compact:main:main",
        name="compact",
        kind="maintenance",
        status="succeeded",
        health=ObservatoryHealth(state="ok"),
        target=ObservatoryResourceRef(kind="branch", id="main", label="main"),
    )
    monkeypatch.setattr(
        "phlo_api.observatory_api.observatory._load_operations", lambda: [operation]
    )
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_logs", lambda: [])

    response = client.get("/api/observatory/operations/compact:main:main")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"operation", "related", "logs", "actions"}
    assert payload["operation"]["id"] == operation.id
    _assert_no_provider_url_settings(payload)


def test_observatory_operation_agent_context_endpoint_returns_stable_contract(monkeypatch) -> None:
    client = TestClient(app)
    operation = ObservatoryOperation(
        id="op-recorded",
        name="Apply workflow proposal",
        kind="workflow.apply",
        status="failed",
        health=ObservatoryHealth(state="error", message="Validation failed"),
        metadata={
            "observability_contract": {
                "operation_id": "op-recorded",
                "trace_ids": ["trace-123"],
                "log_ids": ["log-456"],
                "metric_ids": ["metric-789"],
                "incident_ids": ["incident-001"],
            }
        },
    )
    monkeypatch.setattr(
        "phlo_api.observatory_api.observatory._load_operations", lambda: [operation]
    )
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_logs", lambda: [])

    response = client.get("/api/observatory/operations/op-recorded/agent-context")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "phlo.operation_observability.v1"
    assert payload["operation"]["id"] == "op-recorded"
    assert payload["identifiers"]["trace_ids"] == ["trace-123"]
    assert payload["incident"]["incident_ids"] == ["incident-001"]
    assert payload["retention"]["history_limit"] == 200
    _assert_no_provider_url_settings(payload)


def test_observatory_assets_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/assets")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items"}
    assert isinstance(payload["items"], list)
    _assert_no_provider_url_settings(payload)


def test_observatory_asset_detail_endpoint_returns_related_provider_neutral_payload(
    monkeypatch,
) -> None:
    client = TestClient(app)
    asset = ObservatoryAsset(id="raw.orders", name="raw.orders", group="raw", kinds=["table"])
    table = ObservatoryTable(
        id="orders",
        name="orders",
        namespace="raw",
        asset_id=asset.id,
        metadata={"columns": ["order_id", "customer_id"]},
    )
    check = ObservatoryQualityCheck(
        id="raw.orders:order_id_present",
        name="order_id_present",
        asset_id=asset.id,
        status="unknown",
    )
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_assets", lambda: [asset])
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_tables", lambda: [table])
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_quality", lambda: [check])
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_logs", lambda: [])
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_operations", lambda: [])

    response = client.get("/api/observatory/assets/raw.orders")

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


def test_observatory_asset_graph_and_impact_are_first_class(monkeypatch) -> None:
    monkeypatch.setattr(
        observatory,
        "_load_assets",
        lambda: [
            ObservatoryAsset(id="silver.stg_orders", name="stg_orders", group="silver"),
            ObservatoryAsset(
                id="gold.fct_orders",
                name="fct_orders",
                group="gold",
                dependencies=["silver.stg_orders"],
            ),
        ],
    )

    client = TestClient(app)
    graph_response = client.get("/api/observatory/asset-graph")
    impact_response = client.get(
        "/api/observatory/asset-graph/impact",
        params={"asset_key": "silver.stg_orders", "max_depth": 2},
    )

    assert graph_response.status_code == 200
    graph = graph_response.json()
    assert [node["key_path"] for node in graph["nodes"]] == [
        "silver.stg_orders",
        "gold.fct_orders",
    ]
    assert graph["edges"] == [{"source": "silver.stg_orders", "target": "gold.fct_orders"}]

    assert impact_response.status_code == 200
    assert impact_response.json() == [
        {
            "key_path": "gold.fct_orders",
            "label": "fct_orders",
            "layer": "gold",
            "depth": 1,
        }
    ]


def test_observatory_tables_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/tables")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items"}
    assert isinstance(payload["items"], list)
    _assert_no_provider_url_settings(payload)


def test_observatory_table_preview_endpoint_returns_provider_neutral_payload(monkeypatch) -> None:
    client = TestClient(app)
    table = ObservatoryTable(
        id="orders",
        name="orders",
        namespace="raw",
        metadata={
            "records": 12,
            "columns": ["order_id"],
            "column_types": {"order_id": "integer"},
        },
    )
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_tables", lambda: [table])
    monkeypatch.setattr(
        "phlo_api.observatory_api.observatory._preview_from_query_engine",
        lambda *_args, **_kwargs: None,
    )

    response = client.get("/api/observatory/table-preview/orders?limit=5")

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
    assert payload["rows"] == [
        {"_phlo_row_id": "orders:1", "order_id": "order-0001"},
        {"_phlo_row_id": "orders:2", "order_id": "order-0002"},
        {"_phlo_row_id": "orders:3", "order_id": "order-0003"},
        {"_phlo_row_id": "orders:4", "order_id": "order-0004"},
        {"_phlo_row_id": "orders:5", "order_id": "order-0005"},
    ]
    assert payload["row_count"] == 12
    assert payload["has_more"] is True
    assert len(payload["column_types"]) == len(payload["columns"])
    _assert_no_provider_url_settings(payload)


def test_observatory_query_endpoint_returns_provider_neutral_payload(monkeypatch) -> None:
    client = TestClient(app)
    table = ObservatoryTable(
        id="orders",
        name="orders",
        namespace="raw",
        metadata={"columns": ["order_id"], "column_types": {"order_id": "integer"}},
    )
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_tables", lambda: [table])
    monkeypatch.setattr(
        "phlo_api.observatory_api.observatory._preview_from_query_engine",
        lambda *_args, **_kwargs: None,
    )

    response = client.post(
        "/api/observatory/query",
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


def test_observatory_query_endpoint_rejects_unknown_tables(monkeypatch) -> None:
    client = TestClient(app)
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_tables", lambda: [])

    response = client.post(
        "/api/observatory/query",
        json={"sql": "select * from arbitrary_table limit 5"},
    )

    assert response.status_code == 404
    assert "table not found" in response.json()["detail"].lower()


def test_observatory_query_engine_preserves_known_table_request_offset(monkeypatch) -> None:
    async def fake_execute_trino_query(sql, *, schema=None, timeout_ms=None):
        return {
            "columns": ["order_id"],
            "rows": [{"order_id": 3}],
            "effective_query": sql,
        }

    table = ObservatoryTable(id="orders", name="orders", namespace="raw", schema_name="silver")
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_tables", lambda: [table])
    monkeypatch.setattr(
        "phlo_api.observatory_api.trino.execute_trino_query",
        fake_execute_trino_query,
    )

    result = _run_read_query(
        ObservatoryQueryRequest(sql="select * from orders limit 1", limit=1, offset=25)
    )

    assert result.offset == 25


def test_observatory_saved_queries_contract_persists_provider_neutral_payload(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    client = TestClient(app)

    create_response = client.post(
        "/api/observatory/saved-queries",
        json={
            "name": "Recent orders",
            "sql": "select * from orders limit 10",
            "branch": "main",
        },
    )
    duplicate_response = client.post(
        "/api/observatory/saved-queries",
        json={
            "name": "Recent orders",
            "sql": "select   *  from   orders   limit 10",
            "branch": "main",
        },
    )
    list_response = client.get("/api/observatory/saved-queries")

    assert create_response.status_code == 200
    assert duplicate_response.status_code == 200
    assert list_response.status_code == 200
    created = duplicate_response.json()
    payload = list_response.json()
    assert {"id", "name", "sql", "branch", "created_at", "updated_at", "metadata"} <= set(created)
    assert any(item["id"] == created["id"] for item in payload["items"])
    assert len(payload["items"]) == 1
    _assert_no_provider_url_settings(payload)


def test_observatory_stage_diff_endpoint_returns_provider_neutral_payload(monkeypatch) -> None:
    source_table = ObservatoryTable(id="orders", name="orders", namespace="raw")
    target_table = ObservatoryTable(id="orders_clean", name="orders_clean", namespace="silver")
    previews = {
        source_table.id: ObservatoryTablePreview(
            table=source_table,
            columns=["order_id", "amount"],
            column_types=["integer", "number"],
            rows=[{"_phlo_row_id": "orders:1", "order_id": 1, "amount": 12.5}],
            row_count=1,
            limit=20,
            offset=0,
        ),
        target_table.id: ObservatoryTablePreview(
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
        "phlo_api.observatory_api.observatory._load_table_preview",
        lambda table_id, *, limit, offset: previews[table_id],
    )

    response = TestClient(app).get(
        "/api/observatory/stage-diff",
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


def test_observatory_row_journey_endpoint_returns_provider_neutral_payload(monkeypatch) -> None:
    client = TestClient(app)
    table = ObservatoryTable(
        id="orders",
        name="orders",
        namespace="raw",
        asset_id="raw.orders",
        metadata={"columns": ["order_id"]},
    )
    asset = ObservatoryAsset(id="raw.orders", name="raw.orders", group="raw", kinds=["table"])
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_tables", lambda: [table])
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_assets", lambda: [asset])
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_logs", lambda: [])
    monkeypatch.setattr(
        "phlo_api.observatory_api.observatory._preview_from_query_engine",
        lambda *_args, **_kwargs: None,
    )

    response = client.get("/api/observatory/row-journey/orders/orders:1")

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


def test_observatory_contributing_rows_query_and_page(monkeypatch) -> None:
    async def fake_execute_trino_query(
        query: str,
        catalog: str | None = None,
        schema: str | None = None,
        trino_url: str | None = None,
        timeout_ms: int | None = None,
    ):
        del catalog, schema, trino_url, timeout_ms
        if "information_schema.tables" in query:
            return {
                "columns": ["table_schema"],
                "column_types": ["varchar"],
                "rows": [{"table_schema": "silver"}],
            }
        if "information_schema.columns" in query:
            return {
                "columns": ["column_name", "data_type"],
                "column_types": ["varchar", "varchar"],
                "rows": [{"column_name": "_phlo_row_id", "data_type": "varchar"}],
            }
        return {
            "columns": ["_phlo_row_id"],
            "column_types": ["varchar"],
            "rows": [{"_phlo_row_id": "abc123"}],
        }

    monkeypatch.setattr(
        "phlo_api.observatory_api.contributing.execute_trino_query",
        fake_execute_trino_query,
    )
    monkeypatch.setattr(
        "phlo_api.observatory_api.contributing.resolve_default_catalog",
        lambda: "iceberg",
    )
    monkeypatch.setattr(
        "phlo_api.observatory_api.contributing.resolve_default_ref",
        lambda: "main",
    )

    client = TestClient(app)
    payload = {
        "downstream_asset_key": "gold/fct_orders",
        "upstream_asset_key": "silver/stg_orders",
        "row_data": {"_phlo_row_id": "abc123"},
    }

    query_response = client.post(
        "/api/observatory/contributing-rows/query",
        json={**payload, "limit": 25},
    )
    page_response = client.post(
        "/api/observatory/contributing-rows/page",
        json={**payload, "page": 0, "page_size": 25},
    )

    assert query_response.status_code == 200
    assert query_response.json() == {
        "query": 'SELECT * FROM "iceberg"."silver"."stg_orders" WHERE "_phlo_row_id" = \'abc123\' ORDER BY "_phlo_row_id" LIMIT 25',
        "upstream": {"schema": "silver", "table": "stg_orders"},
    }

    assert page_response.status_code == 200
    assert page_response.json() == {
        "mode": "entity",
        "page": 0,
        "page_size": 25,
        "has_more": False,
        "query": 'SELECT * FROM "iceberg"."silver"."stg_orders" WHERE "_phlo_row_id" = \'abc123\' ORDER BY "_phlo_row_id" OFFSET 0 LIMIT 26',
        "upstream": {"schema": "silver", "table": "stg_orders"},
        "columns": ["_phlo_row_id"],
        "column_types": ["varchar"],
        "rows": [{"_phlo_row_id": "abc123"}],
    }


def test_observatory_branch_action_contract_skips_until_provider_write_contract_exists(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setattr(observatory, "_load_capability_registry", lambda: None)
    observatory._clear_read_model_cache()
    response = TestClient(app).post(
        "/api/observatory/branches/actions",
        json={"action_id": "branch:create:review/demo"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"action", "status", "message", "operation"}
    assert payload["status"] == "skipped"
    assert payload["action"]["enabled"] is False
    assert payload["operation"]["status"] == "skipped"
    _assert_no_provider_url_settings(payload)


def test_observatory_branch_action_skips_when_branches_capability_is_unavailable(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setattr(
        "phlo_api.observatory_api.observatory._load_capabilities",
        lambda: ObservatoryCapabilities(features={"branches": False}),
    )

    def fail_write(_branches):
        raise AssertionError("branch action must not write without a catalog provider")

    monkeypatch.setattr("phlo_api.observatory_api.observatory._write_branches", fail_write)

    response = TestClient(app).post(
        "/api/observatory/branches/actions",
        json={"action_id": "branch:create:review/demo"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "skipped"
    assert payload["action"]["kind"] == "branch.create"
    assert payload["action"]["enabled"] is False
    assert "catalog provider" in payload["message"]
    assert payload["operation"]["status"] == "skipped"


def test_observatory_branch_action_skip_is_recorded(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setattr(observatory, "_load_capability_registry", lambda: None)
    observatory._clear_read_model_cache()

    response = TestClient(app).post(
        "/api/observatory/branches/actions",
        json={"action_id": "branch:create:experiment"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "skipped"
    assert payload["operation"]["status"] == "skipped"
    assert payload["operation"]["kind"] == "branch.create"

    operations = TestClient(app).get("/api/observatory/operations").json()["items"]
    assert operations[0]["id"] == payload["operation"]["id"]
    assert operations[0]["metadata"]["action_id"] == "branch:create:experiment"


def test_observatory_operations_include_wap_reports(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    reports_dir = tmp_path / ".phlo" / "wap-reports"
    reports_dir.mkdir(parents=True)
    (reports_dir / "run-1.json").write_text(
        json.dumps(
            {
                "schema_version": "phlo.wap_report.v1",
                "run_id": "run-1",
                "status": "promoted",
                "branch": "pipeline-run-1",
                "source_hash": "source",
                "target_branch": "main",
                "target_hash_before": "before",
                "target_hash_after": "after",
                "updated_at": "2026-06-17T10:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    observatory._clear_read_model_cache()

    payload = TestClient(app).get("/api/observatory/operations").json()

    wap = next(item for item in payload["items"] if item["id"] == "wap:run-1")
    assert wap["status"] == "succeeded"
    assert wap["target"]["id"] == "pipeline-run-1"
    assert wap["metadata"]["target_hash_after"] == "after"


def test_observatory_branch_detail_uses_wap_report_tables_when_catalog_tables_missing(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    reports_dir = tmp_path / ".phlo" / "wap-reports"
    reports_dir.mkdir(parents=True)
    (reports_dir / "run-1.json").write_text(
        json.dumps(
            {
                "run_id": "run-1",
                "status": "promoted",
                "branch": "pipeline-run-1",
                "tables": [
                    {
                        "id": "analytics.orders",
                        "name": "orders",
                        "namespace": "analytics",
                        "format": "iceberg",
                        "records": 128,
                    }
                ],
                "updated_at": "2026-06-17T10:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "phlo_api.observatory_api.observatory._load_branches",
        lambda: [
            ObservatoryBranch(
                id="pipeline-run-1",
                name="pipeline-run-1",
                metadata={"changed": 1, "tables": 1},
            )
        ],
    )
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_tables", lambda: [])
    observatory._clear_read_model_cache()

    payload = TestClient(app).get("/api/observatory/branches/pipeline-run-1").json()

    assert payload["tables"][0]["id"] == "analytics.orders"
    assert payload["contents"][0]["label"] == "orders"


def test_observatory_branch_actions_use_registered_catalog_provider(
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
    monkeypatch.setattr(observatory, "_load_capability_registry", lambda: registry)
    observatory._clear_read_model_cache()

    client = TestClient(app)
    create_response = client.post(
        "/api/observatory/branches/actions",
        json={"action_id": "branch:create:experiment"},
    )
    promote_response = client.post(
        "/api/observatory/branches/actions",
        json={"action_id": "branch:promote:experiment"},
    )
    delete_response = client.post(
        "/api/observatory/branches/actions",
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


def test_observatory_quality_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/quality")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items"}
    assert isinstance(payload["items"], list)
    _assert_no_provider_url_settings(payload)


def test_observatory_quality_detail_endpoint_returns_provider_neutral_payload(monkeypatch) -> None:
    client = TestClient(app)
    asset = ObservatoryAsset(id="raw.orders", name="raw.orders", group="raw", kinds=["table"])
    check = ObservatoryQualityCheck(
        id="raw.orders:order_id_present",
        name="order_id_present",
        asset_id=asset.id,
        status="unknown",
    )
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_assets", lambda: [asset])
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_quality", lambda: [check])
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_logs", lambda: [])
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_operations", lambda: [])

    response = client.get("/api/observatory/quality/raw.orders:order_id_present")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"check", "asset", "history", "logs", "actions"}
    assert payload["check"]["id"] == check.id
    _assert_no_provider_url_settings(payload)


def test_observatory_logs_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/logs")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items"}
    assert isinstance(payload["items"], list)
    _assert_no_provider_url_settings(payload)


def test_observatory_log_facets_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/logs/facets")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"sources", "levels", "resources"}
    _assert_no_provider_url_settings(payload)


def test_observatory_branches_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/branches")

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


def test_observatory_branch_detail_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/branches/main")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"branch", "contents", "commits", "compare", "tables"}
    assert payload["branch"]["name"] == "main"
    _assert_no_provider_url_settings(payload)


def test_observatory_extensions_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/extensions")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items"}
    assert isinstance(payload["items"], list)
    _assert_no_provider_url_settings(payload)


def test_observatory_extension_detail_endpoint_returns_provider_neutral_payload(
    monkeypatch,
) -> None:
    client = TestClient(app)
    extension = ObservatoryExtension(
        id="observatory-demo",
        name="Observatory Demo",
        version="0.1.0",
        routes=["/demo"],
        nav=["/demo"],
    )
    monkeypatch.setattr(
        "phlo_api.observatory_api.observatory._load_extensions", lambda: [extension]
    )

    response = client.get("/api/observatory/extensions/observatory-demo")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"extension", "routes", "nav", "capabilities"}
    assert payload["extension"]["id"] == extension.id
    _assert_no_provider_url_settings(payload)


def test_observatory_extension_settings_put_reads_json_body() -> None:
    response = TestClient(app).put(
        "/api/observatory/extensions/not-installed/settings",
        json={"settings": {"theme": "dark"}},
    )
    invalid = TestClient(app).put(
        "/api/observatory/extensions/not-installed/settings",
        json={"theme": "dark"},
    )

    assert response.status_code == 404
    assert invalid.status_code == 422


def test_observatory_settings_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/settings")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"version", "defaults", "features", "storage", "metadata"}
    assert payload["version"] == 2
    assert payload["defaults"]["branch"] == "main"
    _assert_no_provider_url_settings(payload)


def test_observatory_search_endpoint_returns_provider_neutral_payload() -> None:
    response = TestClient(app).get("/api/observatory/search", params={"q": "gold"})

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items"}
    assert isinstance(payload["items"], list)
    _assert_no_provider_url_settings(payload)


def test_observatory_search_endpoint_url_encodes_resource_href_segments(monkeypatch) -> None:
    client = TestClient(app)
    asset = ObservatoryAsset(id="silver/demo", name="silver/demo", group="silver", kinds=["table"])
    table = ObservatoryTable(id="analytics/demo", name="demo", namespace="analytics")
    extension = ObservatoryExtension(id="demo/ext", name="Demo Extension", version="0.1.0")
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_services", lambda: [])
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_assets", lambda: [asset])
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_tables", lambda: [table])
    monkeypatch.setattr("phlo_api.observatory_api.observatory._load_quality", lambda: [])
    monkeypatch.setattr(
        "phlo_api.observatory_api.observatory._load_extensions", lambda: [extension]
    )

    response = client.get("/api/observatory/search", params={"q": "demo"})

    assert response.status_code == 200
    hrefs = {item["kind"]: item["href"] for item in response.json()["items"]}
    assert hrefs["asset"] == "/assets/silver%2Fdemo"
    assert hrefs["table"] == "/data/analytics%2Fdemo"
    assert hrefs["extension"] == "/extensions/demo%2Fext"


def test_observatory_schema_diff_returns_stable_agent_envelope(monkeypatch) -> None:
    detail = ObservatoryAssetDetail(
        asset=ObservatoryAsset(id="raw.orders", name="raw.orders"),
        tables=[
            ObservatoryTable(id="orders", name="orders", metadata={"columns": ["id", "amount"]})
        ],
    )
    monkeypatch.setattr(observatory, "_load_asset_detail", lambda asset_key: detail)

    response = TestClient(app).post(
        "/api/observatory/schemas/diff",
        json={"asset_key": "raw.orders", "from_run": "run-a", "to_run": "run-b"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["asset_key"] == "raw.orders"
    assert payload["from_run"] == "run-a"
    assert payload["to_run"] == "run-b"
    assert payload["changes"] == []
    assert payload["snapshot_available"] is False
    assert payload["current_columns"] == ["id", "amount"]


def test_observatory_all_endpoints_do_not_leak_provider_url_setting_names() -> None:
    client = TestClient(app)

    for path in (
        "/api/observatory/overview",
        "/api/observatory/capabilities",
        "/api/observatory/services",
        "/api/observatory/services/phlo-api",
        "/api/observatory/operations",
        "/api/observatory/operations/compact:main:main",
        "/api/observatory/assets",
        "/api/observatory/assets/raw.orders",
        "/api/observatory/tables",
        "/api/observatory/table-preview/orders",
        "/api/observatory/saved-queries",
        "/api/observatory/stage-diff?source_table_id=orders&target_table_id=orders_clean",
        "/api/observatory/row-journey/orders/orders:1",
        "/api/observatory/quality",
        "/api/observatory/quality/raw.orders:order_id_present",
        "/api/observatory/logs",
        "/api/observatory/logs/facets",
        "/api/observatory/branches",
        "/api/observatory/branches/main",
        "/api/observatory/extensions",
        "/api/observatory/settings",
        "/api/observatory/search?q=gold",
    ):
        response = client.get(path)

        if response.status_code == 404:
            continue
        assert response.status_code == 200, path
        _assert_no_provider_url_settings(response.json())

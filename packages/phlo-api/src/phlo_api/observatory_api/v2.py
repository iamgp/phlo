"""Observatory v2 provider-neutral API resources."""

from __future__ import annotations

import asyncio
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, is_dataclass
import importlib
import importlib.util
import http.client
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
from typing import Any

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from phlo_api.observatory_api.v2_actions import execute_v2_action
from phlo_api.observatory_api.v2_cache import ReadModelCache
from phlo_api.observatory_api.v2_capabilities import build_capability_inventory
from phlo_api.observatory_api.v2_catalog import load_catalog_items
from phlo_api.observatory_api.v2_governance import load_governance_items
from phlo_api.observatory_api.v2_models import (
    HealthState,
    ServiceStatus,
    V2Action,
    V2ActionRequest,
    V2ActionResult,
    V2Asset,
    V2AssetDetail,
    V2Branch,
    V2BranchDetail,
    V2Capabilities,
    V2CapabilityInventory,
    V2CapabilityPage,
    V2CapabilityProvider,
    V2Extension,
    V2ExtensionDetail,
    V2ExternalLink,
    V2Health,
    V2LogEvent,
    V2LogFacets,
    V2Operation,
    V2OperationDetail,
    V2Overview,
    V2PackageInstallRequest,
    V2PackageInstallResult,
    V2QualityCheck,
    V2QualityDetail,
    V2QueryRequest,
    V2QueryResult,
    V2ResourceRef,
    V2RouteRequirement,
    V2RowJourney,
    V2Run,
    V2SavedQuery,
    V2SavedQueryRequest,
    V2SearchResult,
    V2Service,
    V2ServiceConfigEntry,
    V2ServiceDetail,
    V2ServicePort,
    V2Settings,
    V2StageDiff,
    V2SurfaceItem,
    V2Table,
    V2TablePreview,
)
from phlo_api.observatory_api.v2_metadata import safe_metadata as _safe_metadata
from phlo_api.observatory_api.v2_observability import load_observability_items
from phlo_api.observatory_api.v2_operation_journal import (
    append_operation,
    load_operation_journal,
    operation_from_workflow_action,
    record_action_result,
    sort_operations,
)
from phlo_api.observatory_api.v2_products import load_api_items, load_bi_items
from phlo_api.observatory_api.v2_runs import load_runs
from phlo_api.observatory_api.v2_saved_queries import (
    dedupe_saved_queries as _dedupe_saved_queries_impl,
    load_saved_queries as _load_saved_queries_impl,
    save_query as _save_query_impl,
    validate_saved_query_sql as _validate_saved_query_sql_impl,
    write_saved_queries as _write_saved_queries_impl,
)
from phlo_api.observatory_api.v2_search import search_results as _search_results_impl
from phlo_api.observatory_api.v2_services import load_services as _load_services_impl
from phlo_api.observatory_api.v2_services import project_compose_name as _project_compose_name
from phlo_api.observatory_api.v2_storage import load_storage_items
from phlo_api.observatory_api.v2_workflow_wizard import (
    V2WorkflowActionRequest,
    V2WorkflowActionResult,
    V2WorkflowProposalRequest,
    apply_workflow_action,
    build_workflow_proposal,
    build_workflow_wizard_payload,
)
from phlo.cli.commands.plugin.install import resolve_install_target
from phlo.plugins.registry_client import get_registry_data

router = APIRouter(tags=["observatory-v2"])

_DOCKER_SERVICE_STATUS_RANK: dict[ServiceStatus, int] = {
    "running": 4,
    "unhealthy": 3,
    "starting": 2,
    "stopped": 1,
    "unknown": 0,
}

_READ_QUERY_RE = re.compile(
    r"^\s*select\s+\*\s+from\s+(?P<table>[A-Za-z0-9_.:-]+)(?:\s+limit\s+(?P<limit>\d+))?\s*;?\s*$",
    re.IGNORECASE,
)
_ENV_DEFAULT_RE = re.compile(r"^\$\{[^}:]+:-(?P<default>[^}]+)\}$")
_TABLE_LIST_METADATA_PREFIX_DENYLIST = ("phlo/compiled_sql",)
_TABLE_LIST_METADATA_DENYLIST = {"preview_rows"}
_FAST_READ_MODEL_TTL_SECONDS = 30
_EXPENSIVE_READ_MODEL_TTL_SECONDS = 120
_READ_MODEL_CACHE = ReadModelCache(project_key=lambda: str(_project_root()))
_DOCKER_SOCKET = "/var/run/docker.sock"


def _cached_read_model(name: str, ttl_seconds: float, loader: Any) -> Any:
    return _READ_MODEL_CACHE.cached(name, ttl_seconds, loader)


def _clear_read_model_cache() -> None:
    _READ_MODEL_CACHE.clear()


class V2ServiceList(BaseModel):
    """List envelope for v2 services."""

    items: list[V2Service]


class V2OperationList(BaseModel):
    """List envelope for v2 operations."""

    items: list[V2Operation]


class V2RunList(BaseModel):
    """List envelope for v2 orchestrator runs."""

    items: list[V2Run]


class V2AssetList(BaseModel):
    """List envelope for v2 assets."""

    items: list[V2Asset]


class V2TableList(BaseModel):
    """List envelope for v2 tables."""

    items: list[V2Table]


class V2QualityList(BaseModel):
    """List envelope for v2 quality checks."""

    items: list[V2QualityCheck]


class V2LogList(BaseModel):
    """List envelope for v2 log events."""

    items: list[V2LogEvent]


class V2BranchList(BaseModel):
    """List envelope for v2 branches."""

    items: list[V2Branch]


class V2ExtensionList(BaseModel):
    """List envelope for v2 extensions."""

    items: list[V2Extension]


class V2SearchList(BaseModel):
    """List envelope for v2 search results."""

    items: list[V2SearchResult]


class V2SavedQueryList(BaseModel):
    """List envelope for saved queries."""

    items: list[V2SavedQuery]


class V2SurfaceList(BaseModel):
    """List envelope for top-level v2 surfaces."""

    items: list[V2SurfaceItem]


def _not_found(kind: str, resource_id: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f"{kind} not found: {resource_id}")


def _coerce_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _coerce_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _dataclass_dict(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    return {}


def _project_root() -> Path:
    return Path(os.environ.get("PHLO_PROJECT_PATH", Path.cwd())).resolve()


def _v2_state_dir() -> Path:
    state_dir = _project_root() / ".phlo" / "observatory-v2"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def _saved_queries_path() -> Path:
    return _v2_state_dir() / "saved_queries.json"


def _branches_path() -> Path:
    return _v2_state_dir() / "branches.json"


def _lakehouse_manifest_path() -> Path:
    return _v2_state_dir() / "lakehouse_manifest.json"


def _load_lakehouse_manifest() -> Mapping[str, Any]:
    path = _lakehouse_manifest_path()
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _manifest_records(key: str, model: type[BaseModel]) -> list[Any]:
    payload = _load_lakehouse_manifest()
    raw_items = payload.get(key)
    if not isinstance(raw_items, list):
        return []

    records: list[Any] = []
    for item in raw_items:
        if not isinstance(item, Mapping):
            continue
        try:
            records.append(model.model_validate(item))
        except Exception:
            continue
    return records


def _merge_by_id(records: Iterable[Any]) -> list[Any]:
    merged: dict[str, Any] = {}
    for record in records:
        record_id = getattr(record, "id", None)
        if not isinstance(record_id, str) or not record_id:
            continue
        merged[record_id] = record
    return list(merged.values())


def _import_project_workflows(project_root: Path) -> None:
    """Import project workflow files so Phlo-native specs enter the registry."""
    workflows_path = project_root / "workflows"
    if not workflows_path.is_dir():
        return

    parent_dir = workflows_path.parent.resolve()
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

    for py_file in sorted(workflows_path.rglob("*.py")):
        if py_file.name == "__init__.py" or py_file.name.startswith("_"):
            continue
        module_name = "phlo_observatory_v2_workflow_" + "_".join(
            py_file.relative_to(workflows_path).with_suffix("").parts
        )
        spec = importlib.util.spec_from_file_location(module_name, py_file)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(module_name, None)
            continue


def _load_capability_registry_uncached() -> Any | None:
    """Load the core capability registry if available."""
    try:
        from phlo.capabilities import clear_all_capabilities
        from phlo.capabilities import get_capability_registry
        from phlo.capabilities.discovery import discover_capabilities

        clear_all_capabilities()
        _import_project_workflows(_project_root())
        discover_capabilities()
        return get_capability_registry()
    except Exception:
        return None


def _load_capability_registry() -> Any | None:
    return _cached_read_model(
        "capability-registry",
        30,
        _load_capability_registry_uncached,
    )


def _sorted_strings(values: Iterable[Any]) -> list[str]:
    return sorted(str(value) for value in values if value is not None)


def _fallback_services() -> list[V2Service]:
    """Return deterministic service data without package-specific imports."""
    return [
        V2Service(
            id="phlo-api",
            name="phlo-api",
            kind="api",
            status="unknown",
            health=V2Health(state="unknown", message="Runtime status unavailable"),
            definition_state="configured",
            runtime_state="unknown",
            in_stack=True,
            backend="native",
            impacts=["observatory"],
            metadata={"source": "fallback", "core": True},
        ),
        V2Service(
            id="observatory",
            name="observatory",
            kind="ui",
            status="unknown",
            health=V2Health(state="unknown", message="Runtime status unavailable"),
            definition_state="configured",
            runtime_state="unknown",
            in_stack=True,
            backend="native",
            depends_on=["phlo-api"],
            metadata={"source": "fallback", "core": True},
        ),
    ]


def _docker_status_from_container(container: Mapping[str, Any]) -> tuple[ServiceStatus, V2Health]:
    state = _coerce_str(container.get("State"), "unknown").lower()
    status_text = _coerce_str(container.get("Status"), "")
    status_lower = status_text.lower()

    if state == "running" and "(unhealthy)" in status_lower:
        return "unhealthy", V2Health(state="error", message=status_text)
    if state == "running" and "starting" in status_lower:
        return "starting", V2Health(state="warning", message=status_text)
    if state == "running":
        health: HealthState = "ok" if "(healthy)" in status_lower else "unknown"
        return "running", V2Health(state=health, message=status_text or None)
    if state in {"created", "restarting"}:
        return "starting", V2Health(state="warning", message=status_text or state)
    if state == "exited" and "exited (0)" in status_lower:
        return "stopped", V2Health(state="ok", message=status_text or "Completed")
    if state in {"exited", "dead", "removing"}:
        return "stopped", V2Health(state="warning", message=status_text or state)
    return "unknown", V2Health(state="unknown", message=status_text or None)


def _container_labels(container: Mapping[str, Any]) -> dict[str, str]:
    labels = container.get("Labels")
    if isinstance(labels, Mapping):
        return {str(key): str(value) for key, value in labels.items()}
    if not isinstance(labels, str) or not labels:
        return {}
    parsed: dict[str, str] = {}
    for item in labels.split(","):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        parsed[key] = value
    return parsed


class _UnixSocketHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path: str):
        super().__init__("localhost")
        self.socket_path = socket_path

    def connect(self) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.socket_path)
        self.sock = sock


def _docker_socket_json(path: str) -> Any:
    connection = _UnixSocketHTTPConnection(_DOCKER_SOCKET)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        if response.status >= 400:
            return None
        body = response.read().decode()
        return json.loads(body) if body else None
    except (OSError, json.JSONDecodeError, http.client.HTTPException):
        return None
    finally:
        connection.close()


def _normalize_docker_api_container(container: Mapping[str, Any]) -> dict[str, Any]:
    names = container.get("Names")
    if isinstance(names, list) and names:
        name = str(names[0]).lstrip("/")
    else:
        name = _coerce_str(container.get("Names") or container.get("Name"), "").lstrip("/")
    return {
        "ID": _coerce_str(container.get("Id") or container.get("ID"), ""),
        "Names": name,
        "State": _coerce_str(container.get("State"), ""),
        "Status": _coerce_str(container.get("Status"), ""),
        "Labels": container.get("Labels") if isinstance(container.get("Labels"), Mapping) else {},
    }


def _load_docker_containers() -> list[dict[str, Any]]:
    command = ["docker", "ps", "-a"]
    compose_project = os.environ.get("PHLO_COMPOSE_PROJECT") or os.environ.get(
        "COMPOSE_PROJECT_NAME"
    )
    if compose_project is None:
        compose_project = _project_compose_name(_project_root())
    if compose_project:
        command.extend(["--filter", f"label=com.docker.compose.project={compose_project}"])
    else:
        return []
    command.extend(["--format", "{{json .}}"])
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        result = None

    if result is not None and result.returncode == 0:
        containers: list[dict[str, Any]] = []
        for line in result.stdout.splitlines():
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, Mapping):
                containers.append(dict(parsed))
        return containers

    if not Path(_DOCKER_SOCKET).exists():
        return []
    payload = _docker_socket_json("/containers/json?all=1")
    if not isinstance(payload, list):
        return []
    return [
        _normalize_docker_api_container(container)
        for container in payload
        if isinstance(container, Mapping)
    ]


def _current_compose_project(containers: Sequence[Mapping[str, Any]]) -> str | None:
    configured = os.environ.get("PHLO_COMPOSE_PROJECT") or os.environ.get("COMPOSE_PROJECT_NAME")
    if configured:
        return configured
    configured_project = _project_compose_name(_project_root())
    if configured_project:
        return configured_project

    hostname = os.environ.get("HOSTNAME", "")
    if not hostname:
        return None

    for container in containers:
        container_id = _coerce_str(container.get("ID") or container.get("Id"), "")
        if container_id and container_id.startswith(hostname):
            labels = _container_labels(container)
            project = labels.get("com.docker.compose.project")
            if project:
                return project

    inspected = _docker_socket_json(f"/containers/{hostname}/json")
    if isinstance(inspected, Mapping):
        config = inspected.get("Config")
        labels = config.get("Labels") if isinstance(config, Mapping) else None
        if isinstance(labels, Mapping):
            project = labels.get("com.docker.compose.project")
            if project:
                return str(project)
    return None


def _compose_service_name(container: Mapping[str, Any]) -> str | None:
    labels = _container_labels(container)
    service_name = labels.get("com.docker.compose.service")
    if service_name:
        return service_name
    name = _coerce_str(container.get("Names"), "")
    if name.endswith("-1") and "-" in name:
        return name.rsplit("-", 2)[-2]
    return None


def _service_name_from_container(name: str, service_ids: set[str]) -> str | None:
    ordered_service_ids = list(service_ids)
    ordered_service_ids.sort(key=lambda value: len(value), reverse=True)
    for service_id in ordered_service_ids:
        if name == service_id or name.endswith(f"-{service_id}-1"):
            return service_id
    return None


def _load_docker_service_statuses(
    service_ids: set[str],
) -> dict[str, tuple[ServiceStatus, V2Health]]:
    if not service_ids:
        return {}

    statuses: dict[str, tuple[ServiceStatus, V2Health]] = {}
    containers = _load_docker_containers()
    compose_project = _current_compose_project(containers)
    if not compose_project:
        return statuses

    for container in containers:
        labels = _container_labels(container)
        if labels.get("com.docker.compose.project") != compose_project:
            continue
        name = _coerce_str(container.get("Names"), "")
        service_id = _compose_service_name(container) or _service_name_from_container(
            name, service_ids
        )
        if service_id not in service_ids:
            service_id = _service_name_from_container(name, service_ids)
        if service_id is None:
            continue
        status, health = _docker_status_from_container(container)
        current = statuses.get(service_id)
        if (
            current is None
            or _DOCKER_SERVICE_STATUS_RANK[status] > _DOCKER_SERVICE_STATUS_RANK[current[0]]
        ):
            statuses[service_id] = (status, health)
    return statuses


def _runtime_services_from_containers(
    containers: Sequence[Mapping[str, Any]],
    known_ids: set[str],
) -> list[V2Service]:
    compose_project = _current_compose_project(containers)
    services: list[V2Service] = []
    if not compose_project:
        return services

    for container in containers:
        labels = _container_labels(container)
        if labels.get("com.docker.compose.project") != compose_project:
            continue
        service_id = _compose_service_name(container)
        if not service_id or service_id in known_ids:
            continue
        status, health = _docker_status_from_container(container)
        services.append(
            V2Service(
                id=service_id,
                name=service_id,
                kind=labels.get("phlo.service.category", "service"),
                status=status,
                health=health,
                definition_state="configured",
                runtime_state=status,
                in_stack=True,
                backend="docker",
                metadata=_safe_metadata({"source": "docker", "compose_project": compose_project}),
            )
        )
        known_ids.add(service_id)
    return services


def _service_links_from_definition(service: Any) -> list[V2ExternalLink]:
    compose = getattr(service, "compose", {}) if service is not None else {}
    labels = compose.get("labels") if isinstance(compose, Mapping) else {}
    ports = compose.get("ports") if isinstance(compose, Mapping) else []
    links: list[V2ExternalLink] = []

    if isinstance(labels, Mapping):
        for key, value in labels.items():
            if str(key).endswith(".rule") and "Host(`" in str(value):
                host = str(value).split("Host(`", 1)[1].split("`)", 1)[0]
                if host and "$" not in host:
                    links.append(V2ExternalLink(label="Open", url=f"http://{host}", kind="app"))

    for port in ports if isinstance(ports, list) else []:
        if not isinstance(port, str) or ":" not in port:
            continue
        published = _resolve_env_default(port.split(":", 1)[0])
        target = port.rsplit(":", 1)[-1]
        if published.isdigit():
            links.append(
                V2ExternalLink(
                    label=f":{target}",
                    url=f"http://localhost:{published}",
                    kind="port",
                )
            )

    return links[:4]


def _service_ports_from_definition(service: Any) -> list[V2ServicePort]:
    compose = getattr(service, "compose", {}) if service is not None else {}
    ports = compose.get("ports") if isinstance(compose, Mapping) else []
    exposed: list[V2ServicePort] = []
    for index, port in enumerate(ports if isinstance(ports, list) else []):
        if not isinstance(port, str):
            continue
        if ":" in port:
            published, target = port.rsplit(":", 1)
        else:
            published, target = None, port
        exposed.append(
            V2ServicePort(
                name=f"port-{index + 1}",
                published=_resolve_env_default(published) if published else None,
                target=target,
            )
        )
    return exposed


def _resolve_env_default(value: str) -> str:
    match = _ENV_DEFAULT_RE.match(value)
    if match is not None:
        return match.group("default")
    return value


def _service_config_from_definition(service: Any) -> list[V2ServiceConfigEntry]:
    env_vars = getattr(service, "env_vars", {}) if service is not None else {}
    if not isinstance(env_vars, Mapping):
        return []

    entries: list[V2ServiceConfigEntry] = []
    for name, config in sorted(env_vars.items()):
        if not isinstance(config, Mapping):
            continue
        secret = bool(config.get("secret"))
        entries.append(
            V2ServiceConfigEntry(
                name=str(name),
                value=None if secret else _coerce_str(config.get("default"), "") or None,
                description=_coerce_str(config.get("description"), "") or None,
                secret=secret,
            )
        )
    return entries[:12]


def _load_services() -> list[V2Service]:
    return _load_services_impl(_project_root(), containers=_load_docker_containers())


def _overview_health_from_services(services: Sequence[V2Service]) -> V2Health:
    if not services:
        return V2Health(state="unknown", message="No services discovered")

    runtime_services = _runtime_services(services)
    if not runtime_services:
        return V2Health(state="unknown", message="No runtime containers found")

    status_counts = Counter(service.status for service in runtime_services)
    attention = sum(
        1
        for service in runtime_services
        if service.status in {"unhealthy", "starting"}
        or service.health.state in {"error", "warning"}
        or (service.status == "stopped" and service.health.state != "ok")
    )

    if attention:
        return V2Health(
            state="warning",
            message=f"{attention} services need attention",
        )

    running = status_counts["running"]
    if running:
        return V2Health(state="ok", message=f"{running} services running")

    unknown = status_counts["unknown"]
    if unknown == len(runtime_services):
        return V2Health(state="unknown", message="No runtime containers found")

    return V2Health(state="unknown", message="Runtime status incomplete")


def _runtime_services(services: Sequence[V2Service]) -> list[V2Service]:
    return [
        service
        for service in services
        if service.status != "unknown"
        or service.health.state != "unknown"
        or service.health.message != "Runtime status unavailable"
    ]


def _load_assets() -> list[V2Asset]:
    registry = _load_capability_registry()
    if registry is None:
        return sorted(_manifest_records("assets", V2Asset), key=lambda item: item.id)

    checks_by_asset: dict[str, list[str]] = {}
    for check in registry.list("check"):
        checks_by_asset.setdefault(check.asset_key, []).append(check.name)

    assets: list[V2Asset] = list(_manifest_records("assets", V2Asset))
    for asset in registry.list("asset"):
        assets.append(
            V2Asset(
                id=asset.key,
                name=asset.key,
                group=asset.group,
                description=asset.description,
                kinds=_sorted_strings(asset.kinds),
                dependencies=_sorted_strings(asset.deps),
                resources=_sorted_strings(asset.resources),
                checks=_sorted_strings(checks_by_asset.get(asset.key, [])),
                metadata=_safe_metadata(asset.metadata),
            )
        )
    return sorted(_merge_by_id(assets), key=lambda item: item.id)


def _table_name_from_asset(asset: Any) -> str | None:
    metadata = asset.metadata if isinstance(asset.metadata, Mapping) else {}
    for key in ("table", "table_name", "relation", "name"):
        value = metadata.get(key)
        if isinstance(value, str) and value:
            return value
    if "table" in asset.kinds or "dataset" in asset.kinds:
        return asset.key
    return None


def _load_tables(*, enrich_catalog: bool = True) -> list[V2Table]:
    registry = _load_capability_registry()
    if registry is None:
        return sorted(_manifest_records("tables", V2Table), key=lambda item: item.id)

    catalog_tables = _catalog_tables() if enrich_catalog else None
    tables: list[V2Table] = list(_manifest_records("tables", V2Table))
    for asset in registry.list("asset"):
        table_name = _table_name_from_asset(asset)
        if not table_name:
            continue
        metadata = asset.metadata if isinstance(asset.metadata, Mapping) else {}
        namespace = metadata.get("namespace")
        table_metadata = _safe_metadata(metadata)
        namespace_name = str(namespace) if namespace else asset.group
        schema_name = _coerce_str(metadata.get("schema"), "") or None
        if catalog_tables is not None:
            present = (schema_name or namespace_name, str(table_name)) in catalog_tables
            table_metadata["catalog_present"] = present
            table_metadata["catalog_state"] = "queryable" if present else "model_only"
        tables.append(
            V2Table(
                id=str(table_name),
                name=str(table_name),
                namespace=namespace_name,
                asset_id=asset.key,
                format=_coerce_str(metadata.get("format"), "") or None,
                branch=_coerce_str(metadata.get("branch"), "") or None,
                schema_name=schema_name,
                metadata=table_metadata,
            )
        )
    return sorted(_merge_by_id(tables), key=lambda item: item.id)


def _compact_table(table: V2Table) -> V2Table:
    """Return a table payload suitable for frequently refreshed UI surfaces."""
    metadata = {
        key: value
        for key, value in table.metadata.items()
        if key not in _TABLE_LIST_METADATA_DENYLIST
        and not any(key.startswith(prefix) for prefix in _TABLE_LIST_METADATA_PREFIX_DENYLIST)
    }
    return table.model_copy(update={"metadata": metadata})


def _compact_tables(tables: Iterable[V2Table]) -> list[V2Table]:
    return [_compact_table(table) for table in tables]


def _load_tables_without_catalog() -> list[V2Table]:
    try:
        return _load_tables(enrich_catalog=False)
    except TypeError:
        # Tests and local tools sometimes monkeypatch _load_tables with the
        # historical no-argument shape.
        return _load_tables()


def _catalog_tables() -> set[tuple[str, str]] | None:
    """Return queryable table identifiers from the active query catalog, when available."""
    try:
        from phlo_api.observatory_api.trino import resolve_default_catalog
    except Exception:
        return None

    try:
        catalog = resolve_default_catalog()
    except Exception:
        return None

    schema_result = _run_query_engine(f"SHOW SCHEMAS FROM {catalog}", limit=200)
    if schema_result is None:
        return None

    tables: set[tuple[str, str]] = set()
    for row in schema_result["rows"]:
        schema = row.get("Schema") or row.get("schema")
        if not isinstance(schema, str) or schema == "information_schema":
            continue
        table_result = _run_query_engine(f'SHOW TABLES FROM "{catalog}"."{schema}"', limit=500)
        if table_result is None:
            continue
        for table_row in table_result["rows"]:
            table_name = table_row.get("Table") or table_row.get("table")
            if isinstance(table_name, str) and table_name:
                tables.add((schema, table_name))
    return tables


def _load_quality() -> list[V2QualityCheck]:
    registry = _load_capability_registry()
    if registry is None:
        return sorted(_manifest_records("quality", V2QualityCheck), key=lambda item: item.id)

    checks: list[V2QualityCheck] = list(_manifest_records("quality", V2QualityCheck))
    for check in registry.list("check"):
        check_id = f"{check.asset_key}:{check.name}"
        checks.append(
            V2QualityCheck(
                id=check_id,
                name=check.name,
                asset_id=check.asset_key,
                status="unknown",
                severity=check.severity,
                blocking=bool(check.blocking),
                description=check.description,
                metadata=_safe_metadata(check.tags),
            )
        )
    return sorted(_merge_by_id(checks), key=lambda item: item.id)


def _operation_from_maintenance_status(status: Any) -> V2Operation:
    payload = _dataclass_dict(status)
    operation = _coerce_str(payload.get("operation"), "operation")
    namespace = _coerce_str(payload.get("namespace"), "default")
    ref = _coerce_str(payload.get("ref"), "main")
    completed_at = payload.get("completed_at")
    state = "ok" if payload.get("status") == "succeeded" else "unknown"
    return V2Operation(
        id=":".join([operation, namespace, ref]),
        name=operation,
        kind="maintenance",
        status="succeeded" if payload.get("status") == "succeeded" else "unknown",
        health=V2Health(state=state),
        target=V2ResourceRef(kind="branch", id=ref, label=ref),
        completed_at=completed_at.isoformat() if hasattr(completed_at, "isoformat") else None,
        duration_seconds=payload.get("duration_seconds"),
        metadata=_safe_metadata(payload),
    )


def _load_operations() -> list[V2Operation]:
    operations = [
        *list(load_operation_journal(_project_root())),
        *_manifest_records("operations", V2Operation),
    ]
    registry = _load_capability_registry()
    if registry is None:
        return sort_operations(operations)

    for spec in registry.list("maintenance_read_model"):
        provider = getattr(spec, "provider", None)
        loader = getattr(provider, "load_maintenance_status", None)
        if not callable(loader):
            continue
        try:
            snapshot = loader()
        except Exception:
            continue
        for status in getattr(snapshot, "operations", []):
            operations.append(_operation_from_maintenance_status(status))
    return sort_operations(operations)


def _load_runs() -> list[V2Run]:
    manifest_runs = list(_manifest_records("runs", V2Run))
    provider_runs = load_runs()
    return sorted(
        _merge_by_id([*manifest_runs, *provider_runs]),
        key=lambda item: item.completed_at or item.started_at or item.id,
        reverse=True,
    )


def _load_logs() -> list[V2LogEvent]:
    project_root = _project_root()
    events = [
        *_manifest_records("logs", V2LogEvent),
        *_load_project_log_events(project_root),
    ]
    try:
        from phlo.capabilities.telemetry import iter_telemetry_events
    except Exception:
        return events

    try:
        telemetry_path = project_root / ".phlo" / "telemetry" / "events.jsonl"
        raw_events = list(iter_telemetry_events(telemetry_path))[-50:]
    except Exception:
        return events

    for index, event in enumerate(reversed(raw_events)):
        timestamp = event.get("timestamp")
        name = _coerce_str(event.get("name") or event.get("event_type"), "event")
        level = _coerce_str(event.get("level"), "info").lower()
        events.append(
            V2LogEvent(
                id=_coerce_str(event.get("id"), f"log-{index}"),
                timestamp=_coerce_str(timestamp, "") or None,
                level=level,
                message=name,
                source=_coerce_str(event.get("source"), "") or None,
                metadata=_safe_metadata(event),
            )
        )
    return events[:100]


def _load_project_log_events(project_root: Path) -> list[V2LogEvent]:
    """Load structured Phlo project logs from `.phlo/logs/*.log`."""
    logs_dir = project_root / ".phlo" / "logs"
    if not logs_dir.exists():
        return []

    events: list[V2LogEvent] = []
    for log_path in sorted(logs_dir.glob("*.log"), reverse=True):
        try:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_number, line in enumerate(lines[-100:], start=max(len(lines) - 99, 1)):
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                if not line.strip():
                    continue
                payload = {"message": line.strip(), "level": "info"}
            if not isinstance(payload, Mapping):
                continue
            message = _coerce_str(
                payload.get("message") or payload.get("event") or payload.get("logger"),
                "log event",
            )
            events.append(
                V2LogEvent(
                    id=f"phlo:{log_path.name}:{line_number}",
                    timestamp=_coerce_str(payload.get("timestamp"), "") or None,
                    level=_coerce_str(payload.get("level"), "info").lower(),
                    message=message,
                    source=_coerce_str(payload.get("logger") or payload.get("service"), "")
                    or "phlo",
                    metadata=_safe_metadata(payload),
                )
            )
    return sorted(events, key=lambda event: event.timestamp or "", reverse=True)[:50]


def _asset_related_logs(asset_id: str, logs: list[V2LogEvent]) -> list[V2LogEvent]:
    return [
        event
        for event in logs
        if event.resource is not None
        and event.resource.kind == "asset"
        and event.resource.id == asset_id
    ]


def _asset_related_operations(asset_id: str, operations: list[V2Operation]) -> list[V2Operation]:
    return [
        operation
        for operation in operations
        if operation.target is not None
        and operation.target.kind in {"asset", "table"}
        and operation.target.id == asset_id
    ]


def _service_actions(service: V2Service) -> list[V2Action]:
    if not service.in_stack:
        package_installed = service.metadata.get("package_installed") is not False
        package_name = _coerce_str(service.metadata.get("package"), service.name)
        return [
            V2Action(
                id=f"{service.id}:add",
                label="Add to stack",
                kind="service.add",
                enabled=package_installed,
                reason=None
                if package_installed
                else f"Install {package_name} before adding this service to the stack.",
                equivalent_cli_command=f"phlo services add {service.id}",
                expected_evidence=[
                    f"{service.id} appears in .phlo/docker-compose.yml",
                    f"{service.id} is present in phlo services status",
                ],
            )
        ]

    return [
        V2Action(
            id=f"{service.id}:start",
            label="Start",
            kind="service.start",
            enabled=service.status == "stopped",
            reason=None
            if service.status == "stopped"
            else "Service is already running, starting, or its runtime state is unknown.",
        ),
        V2Action(
            id=f"{service.id}:stop",
            label="Stop",
            kind="service.stop",
            enabled=service.status in {"running", "unhealthy", "starting"},
            reason=None
            if service.status in {"running", "unhealthy", "starting"}
            else "Service is not running.",
        ),
        V2Action(
            id=f"{service.id}:restart",
            label="Restart",
            kind="service.restart",
            enabled=service.status in {"running", "unhealthy", "starting"},
            reason=None
            if service.status in {"running", "unhealthy", "starting"}
            else "Service must be running or starting before restart.",
        ),
    ]


def _quality_actions(check: V2QualityCheck) -> list[V2Action]:
    registry = _load_capability_registry()
    executable = False
    if registry is not None:
        try:
            executable = any(
                f"{item.asset_key}:{item.name}" == check.id and callable(getattr(item, "fn", None))
                for item in registry.list("check")
            )
        except Exception:
            executable = False
    return [
        V2Action(
            id=f"{check.id}:rerun",
            label="Re-run",
            kind="quality.rerun",
            enabled=executable,
            reason=None if executable else "This quality check has no executable function.",
        ),
    ]


def _operation_actions(operation: V2Operation) -> list[V2Action]:
    actions = []
    if operation.target is not None:
        actions.append(
            V2Action(
                id=f"{operation.id}:open-target",
                label="Open Target",
                kind="operation.open_target",
                enabled=True,
                requires_confirmation=False,
            )
        )
    return actions


def _table_columns_from_metadata(table: V2Table) -> list[str]:
    columns = table.metadata.get("columns")
    if isinstance(columns, list):
        names: list[str] = []
        for column in columns:
            if isinstance(column, Mapping):
                name = column.get("name") or column.get("column_name")
                if name is not None:
                    names.append(str(name))
            elif column is not None:
                names.append(str(column))
        return names

    schema = table.metadata.get("schema")
    if isinstance(schema, Mapping):
        return [str(key) for key in schema.keys()]

    return []


def _table_column_types_from_metadata(table: V2Table, columns: list[str]) -> list[str]:
    by_name: dict[str, str] = {}
    metadata_columns = table.metadata.get("columns")
    if isinstance(metadata_columns, list):
        for column in metadata_columns:
            if not isinstance(column, Mapping):
                continue
            name = column.get("name") or column.get("column_name")
            column_type = column.get("type") or column.get("data_type")
            if name is not None and column_type is not None:
                by_name[str(name)] = str(column_type)

    schema = table.metadata.get("schema")
    if isinstance(schema, Mapping):
        for name, value in schema.items():
            if isinstance(value, str):
                by_name[str(name)] = value
            elif isinstance(value, Mapping):
                column_type = value.get("type") or value.get("data_type")
                if column_type is not None:
                    by_name[str(name)] = str(column_type)

    return [by_name.get(column, "unknown") for column in columns]


def _sample_value(table: V2Table, column: str, row_index: int) -> Any:
    column_l = column.lower()
    table_prefix = table.name.replace(".", "_").replace("-", "_")
    if column_l.endswith("_id") or column_l == "id":
        return f"{column_l.replace('_id', '')}-{row_index + 1:04d}"
    if "date" in column_l:
        return f"2026-04-{(row_index % 28) + 1:02d}"
    if column_l.endswith("_at") or "time" in column_l:
        return f"2026-04-{(row_index % 28) + 1:02d}T12:{row_index % 60:02d}:00Z"
    if "amount" in column_l or "revenue" in column_l or "total" in column_l:
        return round(100 + row_index * 7.35, 2)
    if "score" in column_l:
        return max(0, 92 - row_index)
    if "currency" in column_l:
        return "USD"
    if "region" in column_l:
        return ["us-east", "eu-west", "ap-south"][row_index % 3]
    if "tier" in column_l:
        return ["free", "growth", "enterprise"][row_index % 3]
    if "risk" in column_l:
        return ["low", "medium", "high"][row_index % 3]
    return f"{table_prefix}_{column}_{row_index + 1}"


def _table_rows(
    table: V2Table, columns: list[str], limit: int, offset: int
) -> list[dict[str, Any]]:
    preview_rows = table.metadata.get("preview_rows")
    if isinstance(preview_rows, list):
        rows = [dict(row) for row in preview_rows if isinstance(row, Mapping)]
        return rows[offset : offset + max(0, min(limit, 500))]

    row_count_raw = table.metadata.get("records")
    row_count = row_count_raw if isinstance(row_count_raw, int) else 0
    effective_limit = max(0, min(limit, 500))
    available = max(0, min(effective_limit, row_count - offset if row_count else effective_limit))
    rows: list[dict[str, Any]] = []
    for index in range(available):
        absolute_index = offset + index
        row = {column: _sample_value(table, column, absolute_index) for column in columns}
        row.setdefault("_phlo_row_id", f"{table.id}:{absolute_index + 1}")
        rows.append(row)
    return rows


def _run_query_engine(
    sql: str, *, schema: str | None = None, limit: int = 500
) -> Mapping[str, Any] | None:
    try:
        from phlo_api.observatory_api.trino import QueryExecutionError, execute_trino_query
    except Exception:
        return None

    async def _execute() -> Any:
        return await execute_trino_query(sql, schema=schema, timeout_ms=12000)

    try:
        result = asyncio.run(_execute())
    except Exception:
        return None

    if isinstance(result, QueryExecutionError) or not isinstance(result, Mapping):
        return None
    rows = result.get("rows")
    columns = result.get("columns")
    if not isinstance(rows, list) or not isinstance(columns, list):
        return None
    clean_rows = [row for row in rows[:limit] if isinstance(row, Mapping)]
    return {
        "columns": [str(column) for column in columns],
        "rows": [dict(row) for row in clean_rows],
        "column_types": result.get("column_types")
        if isinstance(result.get("column_types"), list)
        else [],
    }


def _relation_from_metadata(table: V2Table) -> str | None:
    relation = table.metadata.get("relation")
    if isinstance(relation, str) and relation.strip():
        return relation.strip()

    catalog = table.metadata.get("catalog") or table.metadata.get("database")
    schema = table.metadata.get("schema") or table.schema_name or table.namespace
    name = table.metadata.get("table_name") or table.metadata.get("table") or table.name
    if all(isinstance(value, str) and value.strip() for value in (catalog, schema, name)):
        return ".".join(
            f'"{str(value).strip().strip(chr(34))}"' for value in (catalog, schema, name)
        )
    return None


def _discovered_relation(table: V2Table) -> str | None:
    try:
        from phlo_api.observatory_api.trino import resolve_default_catalog
    except Exception:
        return None

    try:
        catalog = resolve_default_catalog()
    except Exception:
        return None

    schema_result = _run_query_engine(f"SHOW SCHEMAS FROM {catalog}", limit=200)
    if schema_result is None:
        return None

    names = {
        str(value)
        for value in (
            table.name,
            table.metadata.get("table"),
            table.metadata.get("table_name"),
        )
        if value
    }
    for row in schema_result["rows"]:
        schema = row.get("Schema") or row.get("schema")
        if not isinstance(schema, str) or schema == "information_schema":
            continue
        table_result = _run_query_engine(f'SHOW TABLES FROM "{catalog}"."{schema}"', limit=500)
        if table_result is None:
            continue
        for table_row in table_result["rows"]:
            table_name = table_row.get("Table") or table_row.get("table")
            if isinstance(table_name, str) and table_name in names:
                return f'"{catalog}"."{schema}"."{table_name}"'
    return None


def _query_relation_for_table(table: V2Table) -> str | None:
    return _relation_from_metadata(table) or _discovered_relation(table)


def _select_sql_for_table(table: V2Table, *, limit: int, offset: int = 0) -> str | None:
    relation = _query_relation_for_table(table)
    if relation is None:
        return None
    sql = f"select * from {relation}"
    if offset > 0:
        sql = f"{sql} offset {max(0, offset)}"
    sql = f"{sql} limit {max(1, min(limit, 500))}"
    return sql


def _count_sql_for_table(table: V2Table) -> str | None:
    relation = _query_relation_for_table(table)
    if relation is None:
        return None
    return f"select count(*) as row_count from {relation}"


def _preview_from_query_engine(table: V2Table, limit: int, offset: int) -> V2TablePreview | None:
    effective_limit = max(1, min(limit, 500))
    sql = _select_sql_for_table(table, limit=effective_limit, offset=offset)
    if sql is None:
        return None

    result = _run_query_engine(
        sql, schema=table.schema_name or table.namespace, limit=effective_limit
    )
    if result is None:
        return None

    row_count: int | None = None
    count_sql = _count_sql_for_table(table)
    if count_sql is not None:
        count_result = _run_query_engine(
            count_sql, schema=table.schema_name or table.namespace, limit=1
        )
        if count_result and count_result["rows"]:
            raw_count = count_result["rows"][0].get("row_count")
            if isinstance(raw_count, int):
                row_count = raw_count

    columns = [str(column) for column in result["columns"]]
    raw_column_types = result.get("column_types")
    column_types: list[str] = (
        [
            str(column_type) if column_type is not None else "unknown"
            for column_type in raw_column_types[: len(columns)]
        ]
        if isinstance(raw_column_types, list)
        else []
    )
    if len(column_types) < len(columns):
        column_types.extend(["unknown"] * (len(columns) - len(column_types)))
    rows = [dict(row) for row in result["rows"]]
    metadata = dict(table.metadata)
    if row_count is not None:
        metadata["records"] = row_count
    if table.metadata != metadata:
        table = table.model_copy(update={"metadata": metadata})

    return V2TablePreview(
        table=_compact_table(table),
        columns=columns,
        column_types=column_types,
        rows=rows,
        row_count=row_count,
        limit=effective_limit,
        offset=offset,
        has_more=row_count is not None and offset + len(rows) < row_count,
    )


def _find_table(table_id: str, tables: list[V2Table] | None = None) -> V2Table | None:
    available = tables if tables is not None else _load_tables()
    return next(
        (
            item
            for item in available
            if item.id == table_id
            or item.name == table_id
            or f"{item.namespace}.{item.name}" == table_id
        ),
        None,
    )


def _catalog_branch_provider() -> Any | None:
    registry = _load_capability_registry()
    if registry is None:
        return None
    try:
        catalog_specs = registry.list("catalog")
    except Exception:
        return None
    for spec in catalog_specs:
        provider = getattr(spec, "provider", None)
        if any(
            callable(getattr(provider, method_name, None))
            for method_name in ("list_branches", "create_branch", "merge_branch", "delete_branch")
        ):
            return provider
    return None


def _provider_branch_name(branch: Any) -> str | None:
    if isinstance(branch, Mapping):
        value = branch.get("name") or branch.get("id")
    else:
        value = getattr(branch, "name", None) or getattr(branch, "id", None)
    return str(value) if value else None


def _provider_branch_metadata(branch: Any) -> dict[str, Any]:
    if isinstance(branch, Mapping):
        raw = dict(branch)
    else:
        raw = {
            key: getattr(branch, key)
            for key in ("hash", "commit_hash", "created_at", "metadata")
            if hasattr(branch, key)
        }
    metadata = dict(raw.get("metadata") or {}) if isinstance(raw.get("metadata"), Mapping) else {}
    return _safe_metadata(
        {
            "source": "catalog-provider",
            **metadata,
            "hash": raw.get("hash") or raw.get("commit_hash"),
            "created_at": raw.get("created_at"),
        }
    )


def _load_provider_branches() -> list[V2Branch]:
    provider = _catalog_branch_provider()
    list_branches = getattr(provider, "list_branches", None)
    if not callable(list_branches):
        return []
    try:
        raw_branches = list_branches()
    except Exception:
        return []

    branches: list[V2Branch] = []
    for raw_branch in raw_branches or []:
        name = _provider_branch_name(raw_branch)
        if not name or name == "main":
            continue
        branches.append(
            V2Branch(
                id=name,
                name=name,
                current=False,
                protected=False,
                metadata=_provider_branch_metadata(raw_branch),
            )
        )
    return branches


def _load_branches() -> list[V2Branch]:
    """Return neutral branch data; core-only fallback is the main branch."""
    branches_by_id = {
        "main": V2Branch(id="main", name="main", current=True, protected=True),
    }
    for branch in _manifest_records("branches", V2Branch):
        if branch.id != "main":
            branches_by_id[branch.id] = branch
    for branch in _load_provider_branches():
        branches_by_id.setdefault(branch.id, branch)
    path = _branches_path()
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
        items = payload.get("items") if isinstance(payload, Mapping) else None
        if isinstance(items, list):
            for item in items:
                if isinstance(item, Mapping):
                    try:
                        branch = V2Branch.model_validate(item)
                    except Exception:
                        continue
                    if branch.id != "main":
                        branches_by_id[branch.id] = branch
    return sorted(branches_by_id.values(), key=lambda item: (not item.current, item.name))


def _write_branches(branches: list[V2Branch]) -> None:
    stored = [branch for branch in branches if branch.id != "main"]
    _branches_path().write_text(
        json.dumps({"items": [branch.model_dump() for branch in stored]}, indent=2),
        encoding="utf-8",
    )


def _load_extensions() -> list[V2Extension]:
    try:
        from phlo.plugins.observatory import discover_observatory_extensions
    except Exception:
        return []

    extensions: list[V2Extension] = []
    try:
        discovered = discover_observatory_extensions()
    except Exception:
        return []

    for plugin in discovered:
        try:
            manifest = plugin.get_manifest()
        except Exception:
            continue
        routes = [route.path for route in manifest.ui.routes]
        nav = [item.to for item in manifest.ui.nav]
        extensions.append(
            V2Extension(
                id=plugin.metadata.name,
                name=manifest.name,
                version=manifest.version,
                enabled=True,
                routes=sorted(routes),
                nav=sorted(nav),
                settings_scope=manifest.settings.scope if manifest.settings else None,
                metadata=_safe_metadata(
                    {
                        "plugin": plugin.metadata.name,
                    }
                ),
            )
        )
    return sorted(extensions, key=lambda item: item.id)


def _load_asset_detail(asset_id: str) -> V2AssetDetail:
    assets = _load_assets()
    asset = next((item for item in assets if item.id == asset_id), None)
    if asset is None:
        raise _not_found("asset", asset_id)

    upstream_ids = set(asset.dependencies)
    downstream = [item for item in assets if asset.id in item.dependencies]
    upstream = [item for item in assets if item.id in upstream_ids]
    quality = [check for check in _load_quality() if check.asset_id == asset.id]
    tables = [table for table in _load_tables() if table.asset_id == asset.id]
    operations = _load_operations()
    logs = _load_logs()
    lineage = [
        *(V2ResourceRef(kind="asset", id=item.id, label=item.name) for item in upstream),
        V2ResourceRef(kind="asset", id=asset.id, label=asset.name),
        *(V2ResourceRef(kind="asset", id=item.id, label=item.name) for item in downstream),
    ]
    columns = _table_columns_from_metadata(tables[0]) if tables else []
    upstream_columns = [
        f"{dependency}.{column}" for dependency in asset.dependencies for column in columns[:3]
    ]
    return V2AssetDetail(
        asset=asset,
        upstream=upstream,
        downstream=downstream,
        tables=tables,
        quality=quality,
        logs=_asset_related_logs(asset.id, logs),
        operations=_asset_related_operations(asset.id, operations),
        lineage=lineage,
        materializations=_asset_related_operations(asset.id, operations),
        column_lineage={column: upstream_columns for column in columns[:6]},
    )


def _load_service_detail(service_id: str) -> V2ServiceDetail:
    services = _load_services()
    service = next((item for item in services if item.id == service_id), None)
    if service is None:
        raise _not_found("service", service_id)

    raw_service = None
    try:
        from phlo.plugins.discovery import ServiceDiscovery

        raw_service = ServiceDiscovery().discover().get(service.id)
    except Exception:
        raw_service = None

    dependencies = [item for item in services if item.id in set(service.depends_on)]
    dependents = [item for item in services if service.id in set(item.depends_on)]
    logs = [
        event
        for event in _load_logs()
        if event.resource is not None
        and event.resource.kind == "service"
        and event.resource.id == service.id
    ]
    return V2ServiceDetail(
        service=service,
        dependencies=dependencies,
        dependents=dependents,
        actions=_service_actions(service),
        logs=logs,
        ports=_service_ports_from_definition(raw_service),
        config=_service_config_from_definition(raw_service),
    )


def _load_operation_detail(operation_id: str) -> V2OperationDetail:
    operations = _load_operations()
    operation = next((item for item in operations if item.id == operation_id), None)
    if operation is None:
        raise _not_found("operation", operation_id)

    related = [operation.target] if operation.target is not None else []
    logs = [
        event
        for event in _load_logs()
        if event.resource is not None
        and (
            event.resource.id == operation.id
            or (operation.target is not None and event.resource.id == operation.target.id)
        )
    ]
    return V2OperationDetail(
        operation=operation,
        related=related,
        logs=logs,
        actions=_operation_actions(operation),
    )


def _load_table_preview(table_id: str, limit: int, offset: int) -> V2TablePreview:
    tables = _load_tables_without_catalog()
    table = _find_table(table_id, tables)
    if table is None:
        raise _not_found("table", table_id)

    query_preview = _preview_from_query_engine(table, limit=limit, offset=max(0, offset))
    if query_preview is not None:
        return query_preview

    row_count_raw = table.metadata.get("records")
    preview_rows = table.metadata.get("preview_rows")
    row_count = row_count_raw if isinstance(row_count_raw, int) else None
    if row_count is None and isinstance(preview_rows, list):
        row_count = len(preview_rows)
    columns = _table_columns_from_metadata(table)
    column_types = _table_column_types_from_metadata(table, columns)
    rows = _table_rows(table, columns, limit, max(0, offset))
    if not columns and rows:
        columns = [str(key) for key in rows[0]]
        column_types = ["unknown"] * len(columns)
    return V2TablePreview(
        table=_compact_table(table),
        columns=columns,
        column_types=column_types,
        rows=rows,
        row_count=row_count,
        limit=limit,
        offset=offset,
        has_more=row_count is not None and max(0, offset) + len(rows) < row_count,
    )


def _run_read_query(request: V2QueryRequest) -> V2QueryResult:
    match = _READ_QUERY_RE.match(request.sql)
    if match is None:
        raise HTTPException(
            status_code=400,
            detail="Only read-only SELECT * FROM <known_table> [LIMIT n] queries are supported.",
        )

    table_id = match.group("table")
    requested_limit = int(match.group("limit") or request.limit)
    limit = max(1, min(requested_limit, 500))
    table = _find_table(table_id)
    if table is None:
        raise _not_found("table", table_id)

    sql = _select_sql_for_table(table, limit=limit, offset=max(0, request.offset))
    if sql is not None:
        trino_result = _try_run_query_engine(
            sql,
            branch=table.schema_name or table.namespace or request.branch,
            limit=limit,
            offset=max(0, request.offset),
        )
        if trino_result is not None:
            warnings = list(trino_result.warnings)
            if requested_limit > limit:
                warnings.append("Limit capped at 500 rows.")
            return trino_result.model_copy(update={"warnings": warnings})

    preview = _load_table_preview(table_id, limit=limit, offset=max(0, request.offset))
    effective_sql = f"select * from {preview.table.name} limit {limit}"
    warnings = []
    if requested_limit > limit:
        warnings.append("Limit capped at 500 rows.")
    return V2QueryResult(
        columns=preview.columns,
        rows=preview.rows,
        row_count=preview.row_count,
        effective_sql=effective_sql,
        limit=limit,
        offset=preview.offset,
        warnings=warnings,
    )


def _try_run_query_engine(
    sql: str,
    *,
    branch: str | None,
    limit: int,
    offset: int,
) -> V2QueryResult | None:
    try:
        from phlo_api.observatory_api.trino import QueryExecutionError, execute_trino_query
    except Exception:
        return None

    async def _execute() -> Any:
        return await execute_trino_query(sql, schema=branch, timeout_ms=12000)

    try:
        result = asyncio.run(_execute())
    except Exception:
        return None

    if isinstance(result, QueryExecutionError):
        return None
    if not isinstance(result, Mapping):
        return None

    rows = result.get("rows")
    columns = result.get("columns")
    if not isinstance(rows, list) or not isinstance(columns, list):
        return None
    clean_rows = [row for row in rows if isinstance(row, Mapping)]
    return V2QueryResult(
        columns=[str(column) for column in columns],
        rows=[dict(row) for row in clean_rows[:limit]],
        row_count=len(clean_rows),
        effective_sql=_coerce_str(result.get("effective_query"), sql),
        limit=limit,
        offset=offset,
        warnings=[],
    )


def _load_row_journey(table_id: str, row_id: str) -> V2RowJourney:
    preview = _load_table_preview(table_id, limit=1, offset=max(0, _row_offset(row_id)))
    table = preview.table
    row = preview.rows[0] if preview.rows else {}
    asset = next((item for item in _load_assets() if item.id == table.asset_id), None)
    upstream: list[V2ResourceRef] = []
    downstream: list[V2ResourceRef] = []
    stages: list[V2ResourceRef] = []
    if asset is not None:
        stages.append(V2ResourceRef(kind="asset", id=asset.id, label=asset.name))
        upstream = [
            V2ResourceRef(kind="asset", id=item.id, label=item.name)
            for item in _load_assets()
            if item.id in set(asset.dependencies)
        ]
        downstream = [
            V2ResourceRef(kind="asset", id=item.id, label=item.name)
            for item in _load_assets()
            if asset.id in item.dependencies
        ]
    return V2RowJourney(
        table=table,
        row_id=row_id,
        row=row,
        upstream=upstream,
        downstream=downstream,
        stages=stages,
        logs=_asset_related_logs(table.asset_id or table.id, _load_logs()),
        diff={
            "columns": preview.columns,
            "changed": [],
            "source": "preview",
        },
    )


def _row_offset(row_id: str) -> int:
    tail = row_id.rsplit(":", 1)[-1]
    if tail.isdigit():
        return max(0, int(tail) - 1)
    return 0


def _load_saved_queries() -> list[V2SavedQuery]:
    return _load_saved_queries_impl(_project_root())


def _dedupe_saved_queries(queries: list[V2SavedQuery]) -> list[V2SavedQuery]:
    return _dedupe_saved_queries_impl(queries)


def _write_saved_queries(queries: list[V2SavedQuery]) -> None:
    _write_saved_queries_impl(_project_root(), queries)


def _save_query(request: V2SavedQueryRequest) -> V2SavedQuery:
    return _save_query_impl(_project_root(), request)


def _validate_saved_query_sql(sql: str) -> str | None:
    return _validate_saved_query_sql_impl(sql)


def _load_stage_diff(source_table_id: str, target_table_id: str) -> V2StageDiff:
    source_preview = _load_table_preview(source_table_id, limit=20, offset=0)
    target_preview = _load_table_preview(target_table_id, limit=20, offset=0)
    source_columns = set(source_preview.columns)
    target_columns = set(target_preview.columns)
    common_columns = sorted(source_columns & target_columns)
    added_columns = sorted(target_columns - source_columns)
    removed_columns = sorted(source_columns - target_columns)
    changed_rows: list[dict[str, Any]] = []

    for index, target_row in enumerate(target_preview.rows[:10]):
        source_row = source_preview.rows[index] if index < len(source_preview.rows) else {}
        changed = [
            column for column in common_columns if source_row.get(column) != target_row.get(column)
        ]
        changed_rows.append(
            {
                "row": index + 1,
                "changed": changed,
                "source_id": source_row.get("_phlo_row_id"),
                "target_id": target_row.get("_phlo_row_id"),
            }
        )

    return V2StageDiff(
        source=source_preview.table,
        target=target_preview.table,
        columns={
            "added": added_columns,
            "removed": removed_columns,
            "common": common_columns,
        },
        rows=changed_rows,
        summary={
            "added": len(added_columns),
            "removed": len(removed_columns),
            "changed": sum(1 for row in changed_rows if row["changed"]),
            "unchanged": sum(1 for row in changed_rows if not row["changed"]),
        },
        metadata={"source": "preview"},
    )


def _load_quality_detail(check_id: str) -> V2QualityDetail:
    checks = _load_quality()
    check = next((item for item in checks if item.id == check_id), None)
    if check is None:
        raise _not_found("quality check", check_id)

    assets = _load_assets()
    asset = next((item for item in assets if item.id == check.asset_id), None)
    operations = [
        operation
        for operation in _load_operations()
        if operation.target is not None and operation.target.id in {check.id, check.asset_id}
    ]
    logs = [
        event
        for event in _load_logs()
        if event.resource is not None and event.resource.id in {check.id, check.asset_id}
    ]
    return V2QualityDetail(
        check=check,
        asset=asset,
        history=operations,
        logs=logs,
        actions=_quality_actions(check),
    )


def _load_log_facets(logs: list[V2LogEvent]) -> V2LogFacets:
    resources: dict[str, V2ResourceRef] = {}
    for event in logs:
        if event.resource is not None:
            resources[f"{event.resource.kind}:{event.resource.id}"] = event.resource
    return V2LogFacets(
        sources=sorted({event.source or "platform" for event in logs}),
        levels=sorted({event.level for event in logs}),
        resources=sorted(resources.values(), key=lambda item: (item.kind, item.label)),
    )


def _load_branch_detail(branch_name: str) -> V2BranchDetail:
    branches = _load_branches()
    branch = next(
        (item for item in branches if item.id == branch_name or item.name == branch_name), None
    )
    if branch is None:
        raise _not_found("branch", branch_name)

    tables = [table for table in _load_tables() if table.branch in {None, "", branch.name}]
    contents = [V2ResourceRef(kind="table", id=table.id, label=table.name) for table in tables]
    commits = [
        operation
        for operation in _load_operations()
        if operation.target is not None
        and operation.target.kind == "branch"
        and operation.target.id == branch.name
    ]
    compare = {
        "added": _coerce_int(branch.metadata.get("added", branch.metadata.get("compare_added")), 0),
        "changed": _coerce_int(
            branch.metadata.get("changed", branch.metadata.get("compare_changed")),
            len(tables),
        ),
        "removed": _coerce_int(
            branch.metadata.get("removed", branch.metadata.get("compare_removed")),
            0,
        ),
    }
    if "ahead" in branch.metadata:
        compare["ahead"] = _coerce_int(branch.metadata.get("ahead"), 0)
    if "behind" in branch.metadata:
        compare["behind"] = _coerce_int(branch.metadata.get("behind"), 0)

    if not commits:
        table_asset_ids = {table.asset_id for table in tables if table.asset_id}
        commits = [
            operation
            for operation in _load_operations()
            if operation.target is not None and operation.target.id in table_asset_ids
        ][:8]

    return V2BranchDetail(
        branch=branch,
        contents=contents,
        commits=commits,
        compare=compare,
        tables=tables,
    )


def _search_results(query: str) -> list[V2SearchResult]:
    return _search_results_impl(
        query=query,
        services=_load_services(),
        assets=_load_assets(),
        tables=_load_tables_without_catalog(),
        operations=_load_operations(),
        quality=_load_quality(),
        extensions=_load_extensions(),
    )


def _load_extension_detail(extension_id: str) -> V2ExtensionDetail:
    extensions = _load_extensions()
    extension = next(
        (item for item in extensions if item.id == extension_id or item.name == extension_id),
        None,
    )
    if extension is None:
        raise _not_found("extension", extension_id)

    capabilities = [
        V2ResourceRef(kind="route", id=route, label=route) for route in extension.routes
    ]
    return V2ExtensionDetail(
        extension=extension,
        routes=extension.routes,
        nav=extension.nav,
        capabilities=capabilities,
    )


def _providers_for_path(extensions: Sequence[V2Extension], path: str) -> list[str]:
    providers: list[str] = []
    for extension in extensions:
        paths = {*extension.nav, *extension.routes}
        if path in paths or any(item == path or item.startswith(f"{path}/") for item in paths):
            providers.append(extension.id)
    return sorted(providers)


def _providers_matching(extensions: Sequence[V2Extension], *needles: str) -> list[str]:
    matches: list[str] = []
    lowered_needles = tuple(needle.lower() for needle in needles)
    for extension in extensions:
        haystack = " ".join(
            [extension.id, extension.name, *extension.nav, *extension.routes]
        ).lower()
        if any(needle in haystack for needle in lowered_needles):
            matches.append(extension.id)
    return sorted(set(matches))


def _load_capabilities() -> V2Capabilities:
    inventory = build_capability_inventory(_load_capability_registry())
    _add_orchestrator_plugin_providers(inventory)
    services = _load_services()
    _filter_capabilities_to_project_services(inventory, services)
    _add_runtime_capability_providers(inventory, services)
    pages = _pages_from_inventory(inventory)
    pages = _apply_manifest_capability_overrides(pages)
    features = {page.id: page.available for page in pages}
    providers = {page.id: page.providers for page in pages if page.providers}

    return V2Capabilities(
        pages=pages,
        features=features,
        providers=providers,
    )


def _load_surface_capabilities() -> V2Capabilities:
    """Build route-gating capabilities without dynamic package discovery."""
    inventory = build_capability_inventory(None)
    services = _load_services()
    _filter_capabilities_to_project_services(inventory, services)
    _add_runtime_capability_providers(inventory, services)
    pages = _apply_manifest_capability_overrides(_pages_from_inventory(inventory))
    features = {page.id: page.available for page in pages}
    providers = {page.id: page.providers for page in pages if page.providers}
    return V2Capabilities(pages=pages, features=features, providers=providers)


def _apply_manifest_capability_overrides(
    pages: list[V2CapabilityPage],
) -> list[V2CapabilityPage]:
    manifest = _load_lakehouse_manifest()
    if not manifest:
        return pages

    route_providers: dict[str, str] = {}
    if manifest.get("tables"):
        route_providers["data"] = "lakehouse-manifest"
        route_providers["assets"] = "lakehouse-manifest"
    if manifest.get("assets"):
        route_providers["assets"] = "lakehouse-manifest"
    if manifest.get("quality"):
        route_providers["issues"] = "lakehouse-manifest"
        route_providers["quality"] = "lakehouse-manifest"
    if manifest.get("branches"):
        route_providers["branches"] = "lakehouse-manifest"
    if manifest.get("runs"):
        route_providers["runs"] = "lakehouse-manifest"
    if any(
        str(asset.get("metadata", {}).get("stage", "")).lower() == "serving"
        or str(asset.get("group", "")).lower() == "serving"
        for asset in manifest.get("assets", [])
        if isinstance(asset, Mapping)
    ):
        route_providers["apis"] = "lakehouse-manifest"

    overridden: list[V2CapabilityPage] = []
    for page in pages:
        provider = route_providers.get(page.id)
        if provider is None:
            overridden.append(page)
            continue
        providers = [*page.providers]
        if provider not in providers:
            providers.append(provider)
        overridden.append(
            page.model_copy(
                update={
                    "available": True,
                    "nav": bool(page.metadata.get("nav", page.nav)),
                    "reason": None,
                    "providers": providers,
                }
            )
        )
    return overridden


_RUNTIME_SERVICE_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "dagster": ("orchestrator",),
    "trino": ("query_engine",),
    "nessie": ("catalog", "catalog_scanner"),
    "minio": ("object_store", "table_store"),
    "rustfs": ("object_store", "table_store"),
    "loki": ("observability_backend",),
    "prometheus": ("observability_backend",),
    "grafana": ("observability_backend",),
    "clickstack": ("observability_backend",),
    "alloy": ("observability_backend",),
    "phlo-api": ("api_backend", "maintenance_read_model"),
    "postgrest": ("api_backend",),
    "hasura": ("api_backend",),
    "superset": ("publish_target",),
}


_PROVIDER_SERVICE_DEPENDENCIES: dict[tuple[str, str], tuple[str, ...]] = {
    ("api_backend", "hasura"): ("hasura",),
    ("api_backend", "postgrest"): ("postgrest",),
    ("alert_sink", "alerting"): ("prometheus",),
    ("catalog", "nessie"): ("nessie",),
    ("catalog_scanner", "nessie"): ("nessie",),
    ("governance_backend", "trino"): ("trino",),
    ("lineage_sink", "phlo-lineage"): ("trino", "minio", "nessie"),
    ("maintenance_read_model", "default"): ("phlo-api",),
    ("metadata_catalog", "openmetadata"): ("openmetadata",),
    ("object_store", "minio"): ("minio",),
    ("object_store", "rustfs"): ("rustfs",),
    ("observability_backend", "default"): ("clickstack",),
    ("observability_backend", "clickstack"): ("clickstack",),
    ("observability_backend", "grafana"): ("grafana",),
    ("observability_backend", "loki"): ("loki",),
    ("observability_backend", "prometheus"): ("prometheus",),
    ("orchestrator", "dagster"): ("dagster", "dagster-daemon"),
    ("publish_target", "clickhouse"): ("clickhouse",),
    ("publish_target", "postgres"): ("postgres",),
    ("publish_target", "trino"): ("trino",),
    ("query_engine", "clickhouse"): ("clickhouse",),
    ("query_engine", "trino"): ("trino",),
    ("table_store", "clickhouse"): ("clickhouse",),
    ("table_store", "delta"): ("trino", "minio"),
    ("table_store", "iceberg"): ("trino", "minio", "nessie"),
}


def _add_orchestrator_plugin_providers(inventory: V2CapabilityInventory) -> None:
    """Expose installed orchestrator plugins as route-gating capabilities."""
    try:
        from phlo.plugins.discovery import discover_plugins, list_plugins

        discover_plugins(plugin_type="orchestrators", auto_register=True)
        orchestrators = list_plugins("orchestrators").get("orchestrators", [])
    except Exception:
        orchestrators = []

    providers = inventory.providers.setdefault("orchestrator", [])
    for orchestrator in orchestrators:
        if any(provider.name == orchestrator for provider in providers):
            continue
        providers.append(
            V2CapabilityProvider(
                capability_type="orchestrator",
                name=orchestrator,
                display_name=orchestrator,
                metadata=_safe_metadata(
                    {
                        "source": "plugin",
                        "service": orchestrator,
                    }
                ),
            )
        )


def _filter_capabilities_to_project_services(
    inventory: V2CapabilityInventory,
    services: Sequence[V2Service],
) -> None:
    """Keep service-backed providers aligned with the current project stack."""
    project_service_ids = {
        service.id
        for service in services
        if service.in_stack or service.definition_state == "configured"
    }

    for capability_type, providers in list(inventory.providers.items()):
        filtered: list[V2CapabilityProvider] = []
        for provider in providers:
            dependencies = _provider_service_dependencies(capability_type, provider)
            if not dependencies or any(
                service_id in project_service_ids for service_id in dependencies
            ):
                filtered.append(provider)
        inventory.providers[capability_type] = filtered


def _provider_service_dependencies(
    capability_type: str,
    provider: V2CapabilityProvider,
) -> tuple[str, ...]:
    metadata = provider.metadata
    service_name = metadata.get("service_name") or metadata.get("service")
    if isinstance(service_name, str) and service_name:
        return (service_name,)

    dependencies = metadata.get("service_dependencies") or metadata.get("default_stack")
    if isinstance(dependencies, list):
        return tuple(str(item) for item in dependencies if str(item))

    return _PROVIDER_SERVICE_DEPENDENCIES.get((capability_type, provider.name), ())


def _add_runtime_capability_providers(
    inventory: V2CapabilityInventory, services: Sequence[V2Service]
) -> None:
    """Expose running service-backed capabilities even when provider packages are absent."""
    runtime_services = [service for service in services if service.in_stack]
    for service in runtime_services:
        for capability_type in _RUNTIME_SERVICE_CAPABILITIES.get(service.id, ()):
            providers = inventory.providers.setdefault(capability_type, [])
            if any(provider.name == service.id for provider in providers):
                continue
            providers.append(
                V2CapabilityProvider(
                    capability_type=capability_type,
                    name=service.id,
                    display_name=service.name,
                    package=None,
                    health=service.health,
                    metadata=_safe_metadata(
                        {
                            "source": "runtime-service",
                            "service": service.id,
                            "status": service.status,
                        }
                    ),
                )
            )


def _branches_available() -> bool:
    """Return whether branch actions can be backed by a catalog provider."""
    if _load_capabilities().features.get("branches") is False:
        return False
    return _catalog_branch_provider() is not None


def _pages_from_inventory(inventory: V2CapabilityInventory) -> list[V2CapabilityPage]:
    """Derive Observatory v2 page availability from capability requirements."""
    pages: list[V2CapabilityPage] = []
    for requirement in inventory.requirements:
        required_all_available = all(
            inventory.providers.get(capability_type) for capability_type in requirement.required_all
        )
        required_any_available = not requirement.required_any or any(
            inventory.providers.get(capability_type) for capability_type in requirement.required_any
        )
        available = required_all_available and required_any_available
        pages.append(
            V2CapabilityPage(
                id=requirement.route_id,
                label=requirement.label,
                path=requirement.path,
                available=available,
                nav=requirement.nav and available,
                reason=None if available else requirement.reason,
                providers=_provider_names_for_requirement(inventory, requirement),
                metadata={
                    "required_any": list(requirement.required_any),
                    "required_all": list(requirement.required_all),
                    "optional": list(requirement.optional),
                    "nav": requirement.nav,
                },
            )
        )
    return pages


def _provider_names_for_requirement(
    inventory: V2CapabilityInventory,
    requirement: V2RouteRequirement,
) -> list[str]:
    """Return installed provider names relevant to a route requirement."""
    names: list[str] = []
    seen: set[str] = set()
    capability_types = [
        *requirement.required_any,
        *requirement.required_all,
        *requirement.optional,
    ]
    for capability_type in capability_types:
        for provider in inventory.providers.get(capability_type, []):
            if provider.name in seen:
                continue
            seen.add(provider.name)
            names.append(provider.name)
    return names


def _surface_items_from_inventory(
    *capability_types: str,
    kind: str,
) -> list[V2SurfaceItem]:
    """Return provider-backed surface summaries from the capability inventory."""
    inventory = build_capability_inventory(_load_capability_registry())
    items: list[V2SurfaceItem] = []
    seen: set[tuple[str, str]] = set()
    for capability_type in capability_types:
        for provider in inventory.providers.get(capability_type, []):
            key = (capability_type, provider.name)
            if key in seen:
                continue
            seen.add(key)
            items.append(
                V2SurfaceItem(
                    id=f"{capability_type}:{provider.name}",
                    name=provider.display_name or provider.name,
                    kind=kind,
                    health=provider.health,
                    summary=f"{capability_type.replace('_', ' ')} provider",
                    metadata={
                        "capability_type": capability_type,
                        "provider": provider.name,
                        **provider.metadata,
                    },
                )
            )
    return items


def _surface_items_with_provider_fallback(
    loader: Any,
    *capability_types: str,
    kind: str,
) -> list[V2SurfaceItem]:
    items = loader()
    if items:
        return items
    return _surface_items_from_inventory(*capability_types, kind=kind)


def _load_settings() -> V2Settings:
    defaults: dict[str, str] = {"branch": "main"}
    try:
        from phlo.infrastructure import get_capability_defaults_from_config

        defaults.update(
            {
                str(key): str(value)
                for key, value in get_capability_defaults_from_config().items()
                if value is not None
            }
        )
    except Exception:
        pass

    capabilities = _load_capabilities()
    return V2Settings(
        defaults=defaults,
        features=capabilities.features,
        storage={"settings": "core"},
        metadata={
            "providers": capabilities.providers,
        },
    )


def _execute_action(request: V2ActionRequest) -> V2ActionResult:
    parts = request.action_id.rsplit(":", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid action id.")

    resource_id, action_name = parts
    services = _load_services()
    service = next((item for item in services if item.id == resource_id), None)
    if service is None or action_name not in {"add", "start", "stop", "restart"}:
        raise HTTPException(status_code=400, detail="Unsupported action.")

    action = next(
        (item for item in _service_actions(service) if item.id == request.action_id),
        None,
    )
    if action is None:
        raise HTTPException(status_code=400, detail="Unsupported action.")

    if not action.enabled:
        message = action.reason or f"{action.label} action is disabled."
        return V2ActionResult(
            action=action,
            status="skipped",
            message=message,
        )

    if action_name == "add":
        command = ["phlo", "services", "add", service.id]
    else:
        command = ["phlo", "services", action_name, "--service", service.id]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        message = str(exc)
        return V2ActionResult(
            action=action,
            status="failed",
            message=message,
            operation=V2Operation(
                id=request.action_id,
                name=action.label,
                kind=action.kind,
                status="failed",
                health=V2Health(state="error", message=message),
                target=V2ResourceRef(kind="service", id=service.id, label=service.name),
            ),
        )

    succeeded = result.returncode == 0
    message = (result.stdout or result.stderr or "").strip() or (
        f"{action.label} requested" if succeeded else f"{action.label} failed"
    )
    return V2ActionResult(
        action=action,
        status="succeeded" if succeeded else "failed",
        message=message[-500:],
        operation=V2Operation(
            id=request.action_id,
            name=action.label,
            kind=action.kind,
            status="succeeded" if succeeded else "failed",
            health=V2Health(state="ok" if succeeded else "error", message=message[-200:]),
            target=V2ResourceRef(kind="service", id=service.id, label=service.name),
        ),
    )


def _trusted_registry_service_packages() -> dict[str, dict[str, Any]]:
    try:
        registry = get_registry_data()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Package registry is unavailable.") from exc

    plugins = registry.get("plugins") if isinstance(registry, Mapping) else None
    if not isinstance(plugins, Mapping):
        return {}

    packages: dict[str, dict[str, Any]] = {}
    for name, payload in plugins.items():
        if not isinstance(payload, Mapping):
            continue
        package = str(payload.get("package") or "").strip()
        if not package:
            continue
        normalized = dict(payload)
        normalized["name"] = str(name)
        for key in {str(name), package, package.removeprefix("phlo-")}:
            if key:
                packages[key] = normalized
    return packages


def _uv_project_root() -> Path | None:
    configured = os.environ.get("PHLO_UV_PROJECT") or os.environ.get("UV_PROJECT")
    if configured:
        path = Path(configured).expanduser()
        if (path / "pyproject.toml").exists():
            return path

    for candidate in [_project_root(), Path.cwd(), *Path.cwd().parents]:
        if (candidate / "pyproject.toml").exists():
            return candidate
    return None


def _run_python_package_install(package_spec: str) -> tuple[bool, str]:
    uv = shutil.which("uv")
    if uv is not None:
        project_root = _uv_project_root()
        if project_root is not None:
            command = [uv, "add", "--active", package_spec]
            cwd = project_root
        else:
            command = [uv, "pip", "install", package_spec]
            cwd = None
    elif importlib.util.find_spec("pip") is not None:
        command = [sys.executable, "-m", "pip", "install", package_spec]
        cwd = None
    else:
        raise RuntimeError("Neither uv nor pip is available to install packages.")

    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    message = (result.stdout or result.stderr or "").strip()
    return result.returncode == 0, message or "Install command completed."


def _install_python_package(request: V2PackageInstallRequest) -> V2PackageInstallResult:
    requested = request.package_name.strip()
    if not requested:
        raise HTTPException(status_code=400, detail="Package name is required.")

    trusted_packages = _trusted_registry_service_packages()
    registry_entry = trusted_packages.get(requested)
    if registry_entry is None:
        raise HTTPException(
            status_code=400,
            detail="Only trusted Phlo packages from the registry can be installed.",
        )

    registry_name = str(registry_entry["name"])
    package_name = str(registry_entry["package"])
    package_spec, _display_name = resolve_install_target(registry_name)
    if not package_spec.startswith(package_name):
        package_spec = package_name
        version = str(registry_entry.get("version") or "").strip()
        if version:
            package_spec = f"{package_name}=={version}"

    try:
        succeeded, install_message = _run_python_package_install(package_spec)
    except Exception as exc:
        return V2PackageInstallResult(
            package_name=package_name,
            package_spec=package_spec,
            status="failed",
            message=f"Install failed: {exc}",
            services=[registry_name],
        )
    if not succeeded:
        return V2PackageInstallResult(
            package_name=package_name,
            package_spec=package_spec,
            status="failed",
            message=install_message[-500:],
            services=[registry_name],
        )

    importlib.invalidate_caches()
    _clear_read_model_cache()
    installed_services = [
        service.id
        for service in _load_services()
        if service.metadata.get("package") == package_name
    ]
    return V2PackageInstallResult(
        package_name=package_name,
        package_spec=package_spec,
        status="succeeded",
        message=(
            f"Installed {package_name}. Regenerate the Phlo service stack before starting it."
        ),
        services=installed_services or [registry_name],
    )


def _execute_branch_action(request: V2ActionRequest) -> V2ActionResult:
    parts = request.action_id.split(":", 2)
    if len(parts) != 3 or parts[0] != "branch":
        raise HTTPException(status_code=400, detail="Invalid branch action id.")

    action_name = parts[1]
    branch_name = parts[2].strip()
    if not branch_name:
        raise HTTPException(status_code=400, detail="Branch name is required.")

    provider = _catalog_branch_provider()
    branches_available = _branches_available() and provider is not None
    branch_unavailable_reason = "A catalog provider is required for branch actions."
    action = V2Action(
        id=request.action_id,
        label=action_name.title(),
        kind=f"branch.{action_name}",
        enabled=branches_available,
        requires_confirmation=True,
        reason=None if branches_available else branch_unavailable_reason,
    )
    if not action.enabled:
        return V2ActionResult(
            action=action,
            status="skipped",
            message=action.reason or branch_unavailable_reason,
            operation=None,
        )

    branches = _load_branches()
    existing = next((branch for branch in branches if branch.id == branch_name), None)
    if action_name == "create":
        if existing is None:
            create_branch = getattr(provider, "create_branch", None)
            if not callable(create_branch):
                status = "skipped"
                message = "Catalog provider does not support branch creation."
            else:
                try:
                    branch_hash = create_branch(branch_name, from_ref="main")
                except Exception as exc:
                    status = "failed"
                    message = f"Branch {branch_name} creation failed: {exc}"
                else:
                    if branch_hash:
                        branches.append(
                            V2Branch(
                                id=branch_name,
                                name=branch_name,
                                current=False,
                                protected=False,
                                metadata=_safe_metadata(
                                    {
                                        "source": "catalog-provider",
                                        "hash": branch_hash,
                                    }
                                ),
                            )
                        )
                        _write_branches(branches)
                        status = "succeeded"
                        message = f"Branch {branch_name} created."
                    else:
                        status = "failed"
                        message = f"Catalog provider did not create branch {branch_name}."
        else:
            status = "skipped"
            message = f"Branch {branch_name} already exists."
    elif action_name == "delete":
        if branch_name == "main":
            raise HTTPException(status_code=400, detail="The main branch is protected.")
        if existing is None:
            status = "skipped"
            message = f"Branch {branch_name} does not exist."
        else:
            delete_branch = getattr(provider, "delete_branch", None)
            if not callable(delete_branch):
                status = "skipped"
                message = "Catalog provider does not support branch deletion."
            else:
                try:
                    deleted = bool(delete_branch(branch_name))
                except Exception as exc:
                    status = "failed"
                    message = f"Branch {branch_name} deletion failed: {exc}"
                else:
                    if deleted:
                        branches = [branch for branch in branches if branch.id != branch_name]
                        _write_branches(branches)
                        status = "succeeded"
                        message = f"Branch {branch_name} deleted."
                    else:
                        status = "failed"
                        message = f"Catalog provider did not delete branch {branch_name}."
    elif action_name == "promote":
        if existing is None:
            raise _not_found("branch", branch_name)
        merge_branch = getattr(provider, "merge_branch", None)
        if not callable(merge_branch):
            status = "skipped"
            message = "Catalog provider does not support branch promotion."
        else:
            try:
                promoted = bool(merge_branch(branch_name, target="main"))
            except Exception as exc:
                status = "failed"
                message = f"Branch {branch_name} promotion failed: {exc}"
            else:
                status = "succeeded" if promoted else "failed"
                message = (
                    f"Branch {branch_name} promoted to main."
                    if promoted
                    else f"Catalog provider did not promote branch {branch_name}."
                )
    else:
        raise HTTPException(status_code=400, detail="Unsupported branch action.")

    health_state = "ok"
    if status == "skipped":
        health_state = "warning"
    elif status == "failed":
        health_state = "error"

    return V2ActionResult(
        action=action,
        status=status,  # type: ignore[arg-type]
        message=message,
        operation=V2Operation(
            id=request.action_id,
            name=action.label,
            kind=action.kind,
            status=status,  # type: ignore[arg-type]
            health=V2Health(state=health_state, message=message),  # type: ignore[arg-type]
            target=V2ResourceRef(kind="branch", id=branch_name, label=branch_name),
        ),
    )


@router.get("/overview", response_model=V2Overview)
def get_v2_overview() -> V2Overview:
    """Get the provider-neutral Observatory v2 overview."""
    return _cached_read_model(
        "overview",
        _FAST_READ_MODEL_TTL_SECONDS,
        lambda: V2Overview(
            health=_overview_health_from_services(_load_services()),
            counters={
                "services": len(_runtime_services(_load_services())),
                "operations": len(_load_operations()),
                "assets": len(_load_assets()),
                "tables": len(_load_tables_without_catalog()),
                "quality": len(_load_quality()),
                "incidents": 0,
            },
            recent=[],
        ),
    )


@router.get("/capabilities", response_model=V2Capabilities)
def get_v2_capabilities() -> JSONResponse:
    """Get the provider-neutral Observatory surface capabilities."""
    return JSONResponse(content=_load_capabilities().model_dump(mode="json"))


@router.get("/surface-capabilities")
def get_v2_surface_capabilities() -> JSONResponse:
    """Get Observatory surface capabilities without FastAPI model wrapping."""
    return JSONResponse(content=_load_surface_capabilities().model_dump(mode="json"))


@router.get("/capability-inventory", response_model=V2CapabilityInventory)
def get_v2_capability_inventory() -> V2CapabilityInventory:
    """Get the full provider-neutral capability inventory."""
    return _cached_read_model(
        "capability-inventory",
        _EXPENSIVE_READ_MODEL_TTL_SECONDS,
        lambda: build_capability_inventory(_load_capability_registry()),
    )


@router.get("/services", response_model=V2ServiceList)
def get_v2_services() -> V2ServiceList:
    """List provider-neutral Observatory v2 services."""
    return _cached_read_model(
        "services",
        _FAST_READ_MODEL_TTL_SECONDS,
        lambda: V2ServiceList(items=_load_services()),
    )


@router.get("/services/{service_id:path}", response_model=V2ServiceDetail)
def get_v2_service_detail(service_id: str) -> V2ServiceDetail:
    """Get provider-neutral Observatory v2 service detail."""
    return _load_service_detail(service_id)


@router.get("/operations", response_model=V2OperationList)
def get_v2_operations() -> V2OperationList:
    """List provider-neutral Observatory v2 operations."""
    return _cached_read_model(
        "operations",
        _FAST_READ_MODEL_TTL_SECONDS,
        lambda: V2OperationList(items=_load_operations()),
    )


@router.get("/operations/{operation_id:path}", response_model=V2OperationDetail)
def get_v2_operation_detail(operation_id: str) -> V2OperationDetail:
    """Get provider-neutral Observatory v2 operation detail."""
    return _load_operation_detail(operation_id)


@router.get("/runs", response_model=V2RunList)
def get_v2_runs() -> V2RunList:
    """List provider-neutral orchestrator runs."""
    return _cached_read_model(
        "runs",
        _FAST_READ_MODEL_TTL_SECONDS,
        lambda: V2RunList(items=_load_runs()),
    )


@router.get("/storage", response_model=V2SurfaceList)
def get_v2_storage() -> V2SurfaceList:
    """List provider-neutral storage surfaces."""
    return V2SurfaceList(
        items=_surface_items_with_provider_fallback(
            load_storage_items,
            "table_store",
            "object_store",
            kind="storage",
        )
    )


@router.get("/observability", response_model=V2SurfaceList)
def get_v2_observability() -> V2SurfaceList:
    """List provider-neutral observability surfaces."""
    return V2SurfaceList(
        items=_surface_items_with_provider_fallback(
            load_observability_items,
            "observability_backend",
            "alert_sink",
            kind="observability",
        )
    )


@router.get("/governance", response_model=V2SurfaceList)
def get_v2_governance() -> V2SurfaceList:
    """List provider-neutral governance surfaces."""
    return V2SurfaceList(
        items=_surface_items_with_provider_fallback(
            load_governance_items,
            "governance_backend",
            "authorization_policy_backend",
            "authentication_provider",
            "regulated_surface",
            kind="governance",
        )
    )


@router.get("/catalog", response_model=V2SurfaceList)
def get_v2_catalog() -> V2SurfaceList:
    """List provider-neutral catalog surfaces."""
    return V2SurfaceList(
        items=_surface_items_with_provider_fallback(
            load_catalog_items,
            "metadata_catalog",
            "catalog_scanner",
            "catalog",
            kind="catalog",
        )
    )


@router.get("/apis", response_model=V2SurfaceList)
def get_v2_apis() -> V2SurfaceList:
    """List provider-neutral API surfaces."""
    return V2SurfaceList(
        items=_surface_items_with_provider_fallback(
            load_api_items,
            "api_backend",
            kind="api",
        )
    )


@router.get("/bi", response_model=V2SurfaceList)
def get_v2_bi() -> V2SurfaceList:
    """List provider-neutral BI surfaces."""
    return V2SurfaceList(
        items=_surface_items_with_provider_fallback(
            load_bi_items,
            "publish_target",
            "query_engine",
            kind="bi",
        )
    )


@router.get("/assets", response_model=V2AssetList)
def get_v2_assets() -> V2AssetList:
    """List provider-neutral Observatory v2 assets."""
    return _cached_read_model(
        "assets",
        _EXPENSIVE_READ_MODEL_TTL_SECONDS,
        lambda: V2AssetList(items=_load_assets()),
    )


@router.get("/assets/{asset_id:path}", response_model=V2AssetDetail)
def get_v2_asset_detail(asset_id: str) -> V2AssetDetail:
    """Get provider-neutral Observatory v2 asset detail."""
    return _load_asset_detail(asset_id)


@router.get("/tables", response_model=V2TableList)
def get_v2_tables() -> V2TableList:
    """List provider-neutral Observatory v2 tables."""
    return _cached_read_model(
        "tables",
        _EXPENSIVE_READ_MODEL_TTL_SECONDS,
        lambda: V2TableList(items=_compact_tables(_load_tables())),
    )


@router.get("/table-preview/{table_id:path}", response_model=V2TablePreview)
def get_v2_table_preview(table_id: str, limit: int = 50, offset: int = 0) -> V2TablePreview:
    """Get provider-neutral table preview metadata."""
    return _cached_read_model(
        f"table-preview:{table_id}:{limit}:{offset}",
        _EXPENSIVE_READ_MODEL_TTL_SECONDS,
        lambda: _load_table_preview(table_id, limit=limit, offset=offset),
    )


@router.get("/saved-queries", response_model=V2SavedQueryList)
def get_v2_saved_queries() -> V2SavedQueryList:
    """List saved Observatory v2 queries."""
    return V2SavedQueryList(items=_load_saved_queries())


@router.post("/saved-queries", response_model=V2SavedQuery)
def post_v2_saved_query(request: V2SavedQueryRequest) -> V2SavedQuery:
    """Persist a saved Observatory v2 query."""
    return _save_query(request)


@router.get("/stage-diff", response_model=V2StageDiff)
def get_v2_stage_diff(source_table_id: str, target_table_id: str) -> V2StageDiff:
    """Get provider-neutral stage diff context."""
    return _load_stage_diff(source_table_id, target_table_id)


@router.post("/query", response_model=V2QueryResult)
def post_v2_query(request: V2QueryRequest) -> V2QueryResult:
    """Run a provider-neutral read-only table query."""
    return _run_read_query(request)


@router.get("/row-journey/{table_id:path}/{row_id:path}", response_model=V2RowJourney)
def get_v2_row_journey(table_id: str, row_id: str) -> V2RowJourney:
    """Get provider-neutral row journey context."""
    return _load_row_journey(table_id, row_id)


@router.get("/quality", response_model=V2QualityList)
def get_v2_quality() -> V2QualityList:
    """List provider-neutral Observatory v2 quality checks."""
    return _cached_read_model(
        "quality",
        _EXPENSIVE_READ_MODEL_TTL_SECONDS,
        lambda: V2QualityList(items=_load_quality()),
    )


@router.get("/quality/{check_id:path}", response_model=V2QualityDetail)
def get_v2_quality_detail(check_id: str) -> V2QualityDetail:
    """Get provider-neutral Observatory v2 quality detail."""
    return _load_quality_detail(check_id)


@router.get("/logs", response_model=V2LogList)
def get_v2_logs() -> V2LogList:
    """List provider-neutral Observatory v2 log events."""
    return _cached_read_model(
        "logs", _FAST_READ_MODEL_TTL_SECONDS, lambda: V2LogList(items=_load_logs())
    )


@router.get("/logs/facets", response_model=V2LogFacets)
def get_v2_log_facets() -> V2LogFacets:
    """Get provider-neutral Observatory v2 log facets."""
    return _cached_read_model(
        "log-facets",
        _EXPENSIVE_READ_MODEL_TTL_SECONDS,
        lambda: _load_log_facets(_load_logs()),
    )


@router.get("/branches", response_model=V2BranchList)
def get_v2_branches() -> V2BranchList:
    """List provider-neutral Observatory v2 branches."""
    return _cached_read_model(
        "branches",
        _EXPENSIVE_READ_MODEL_TTL_SECONDS,
        lambda: V2BranchList(items=_load_branches()),
    )


@router.post("/branches/actions", response_model=V2ActionResult)
def post_v2_branch_action(request: V2ActionRequest) -> V2ActionResult:
    """Execute a guarded branch workflow action."""
    result = _execute_branch_action(request)
    recorded = record_action_result(_project_root(), result)
    _clear_read_model_cache()
    return recorded


@router.get("/branches/{branch_name:path}", response_model=V2BranchDetail)
def get_v2_branch_detail(branch_name: str) -> V2BranchDetail:
    """Get provider-neutral Observatory v2 branch detail."""
    return _load_branch_detail(branch_name)


@router.get("/extensions", response_model=V2ExtensionList)
def get_v2_extensions() -> V2ExtensionList:
    """List provider-neutral Observatory v2 extensions."""
    return _cached_read_model(
        "extensions",
        _EXPENSIVE_READ_MODEL_TTL_SECONDS,
        lambda: V2ExtensionList(items=_load_extensions()),
    )


@router.get("/extensions/{extension_id:path}", response_model=V2ExtensionDetail)
def get_v2_extension_detail(extension_id: str) -> V2ExtensionDetail:
    """Get provider-neutral Observatory v2 extension detail."""
    return _load_extension_detail(extension_id)


@router.get("/settings", response_model=V2Settings)
def get_v2_settings() -> V2Settings:
    """Get provider-neutral Observatory v2 settings."""
    return _cached_read_model("settings", _EXPENSIVE_READ_MODEL_TTL_SECONDS, _load_settings)


@router.get("/workflow-wizard")
def get_v2_workflow_wizard() -> dict[str, Any]:
    """Return provider-neutral workflow wizard contributions."""

    return build_workflow_wizard_payload()


@router.post("/workflow-wizard/proposals")
def post_v2_workflow_wizard_proposal(request: V2WorkflowProposalRequest) -> dict[str, Any]:
    """Build a side-effect-free workflow proposal."""

    return build_workflow_proposal(_project_root(), request)


@router.post("/workflow-wizard/actions", response_model=V2WorkflowActionResult)
def post_v2_workflow_wizard_action(request: V2WorkflowActionRequest) -> V2WorkflowActionResult:
    """Run a guarded workflow wizard apply action."""

    try:
        result = apply_workflow_action(_project_root(), request)
    except HTTPException as exc:
        message = str(exc.detail)
        append_operation(
            _project_root(),
            operation_from_workflow_action(
                action_id=request.action_id,
                status="failed",
                message=message,
                files=[],
            ),
        )
        _clear_read_model_cache()
        raise

    append_operation(
        _project_root(),
        operation_from_workflow_action(
            action_id=request.action_id,
            status=result.status,
            message=result.message,
            files=result.files,
        ),
    )
    _clear_read_model_cache()
    return result


@router.get("/search", response_model=V2SearchList)
def get_v2_search(q: str) -> V2SearchList:
    """Search provider-neutral Observatory v2 resources."""
    return V2SearchList(items=_search_results(q))


@router.post("/actions", response_model=V2ActionResult)
def post_v2_action(request: V2ActionRequest) -> V2ActionResult:
    """Execute a guarded Observatory v2 action."""
    resource_id, separator, action_name = request.action_id.rpartition(":")
    services = _load_services()
    is_service_control_action = (
        bool(separator)
        and action_name in {"add", "start", "stop", "restart"}
        and any(service.id == resource_id for service in services)
    )
    result = (
        _execute_action(request)
        if is_service_control_action
        else execute_v2_action(request, registry=_load_capability_registry())
    )
    recorded = record_action_result(_project_root(), result)
    _clear_read_model_cache()
    return recorded


@router.post("/packages/install", response_model=V2PackageInstallResult)
def post_v2_package_install(request: V2PackageInstallRequest) -> V2PackageInstallResult:
    """Install a trusted Phlo Python package into the current environment."""
    result = _install_python_package(request)
    _clear_read_model_cache()
    return result

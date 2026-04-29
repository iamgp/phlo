"""Observatory v2 provider-neutral API resources."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, is_dataclass
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel

from phlo_api.observatory_api.v2_models import (
    V2Action,
    V2Asset,
    V2AssetDetail,
    V2Branch,
    V2BranchDetail,
    V2Extension,
    V2ExtensionDetail,
    V2Health,
    V2LogEvent,
    V2LogFacets,
    V2Operation,
    V2OperationDetail,
    V2Overview,
    V2QualityCheck,
    V2QualityDetail,
    V2ResourceRef,
    V2SearchResult,
    V2Service,
    V2ServiceDetail,
    V2Settings,
    V2Table,
    V2TablePreview,
)

router = APIRouter(tags=["observatory-v2"])

_PRIVATE_METADATA_TOKENS = (
    "url",
    "uri",
    "dsn",
    "endpoint",
    "connection",
    "password",
    "secret",
    "token",
    "key",
)

_DOCKER_SERVICE_STATUS_RANK = {
    "running": 4,
    "unhealthy": 3,
    "starting": 2,
    "stopped": 1,
    "unknown": 0,
}


class V2ServiceList(BaseModel):
    """List envelope for v2 services."""

    items: list[V2Service]


class V2OperationList(BaseModel):
    """List envelope for v2 operations."""

    items: list[V2Operation]


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


def _not_found(kind: str, resource_id: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f"{kind} not found: {resource_id}")


def _safe_metadata(value: Any) -> dict[str, Any]:
    """Return deterministic non-secret, non-provider-URL metadata."""
    if not isinstance(value, Mapping):
        return {}

    safe: dict[str, Any] = {}
    for raw_key, raw_value in value.items():
        key = str(raw_key)
        key_l = key.lower()
        if any(token in key_l for token in _PRIVATE_METADATA_TOKENS):
            continue
        if isinstance(raw_value, str | int | float | bool) or raw_value is None:
            safe[key] = raw_value
        elif isinstance(raw_value, list | tuple | set):
            safe[key] = [
                item
                for item in raw_value
                if isinstance(item, str | int | float | bool) or item is None
            ]
        elif isinstance(raw_value, Mapping):
            nested = _safe_metadata(raw_value)
            if nested:
                safe[key] = nested
    return safe


def _coerce_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _dataclass_dict(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    return {}


def _project_root() -> Path:
    return Path(os.environ.get("PHLO_PROJECT_PATH", Path.cwd())).resolve()


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


def _load_capability_registry() -> Any | None:
    """Load the core capability registry if available."""
    try:
        from phlo.capabilities import get_capability_registry
        from phlo.capabilities.discovery import discover_capabilities

        _import_project_workflows(_project_root())
        discover_capabilities()
        return get_capability_registry()
    except Exception:
        return None


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
            impacts=["observatory"],
            metadata={"source": "fallback", "core": True},
        ),
        V2Service(
            id="observatory",
            name="observatory",
            kind="ui",
            status="unknown",
            health=V2Health(state="unknown", message="Runtime status unavailable"),
            depends_on=["phlo-api"],
            metadata={"source": "fallback", "core": True},
        ),
    ]


def _docker_status_from_container(container: Mapping[str, Any]) -> tuple[str, V2Health]:
    state = _coerce_str(container.get("State"), "unknown").lower()
    status_text = _coerce_str(container.get("Status"), "")
    status_lower = status_text.lower()

    if state == "running" and "(unhealthy)" in status_lower:
        return "unhealthy", V2Health(state="error", message=status_text)
    if state == "running" and "starting" in status_lower:
        return "starting", V2Health(state="warning", message=status_text)
    if state == "running":
        health = "ok" if "(healthy)" in status_lower else "unknown"
        return "running", V2Health(state=health, message=status_text or None)
    if state in {"created", "restarting"}:
        return "starting", V2Health(state="warning", message=status_text or state)
    if state in {"exited", "dead", "removing"}:
        return "stopped", V2Health(state="warning", message=status_text or state)
    return "unknown", V2Health(state="unknown", message=status_text or None)


def _service_name_from_container(name: str, service_ids: set[str]) -> str | None:
    for service_id in sorted(service_ids, key=len, reverse=True):
        if name == service_id or name.endswith(f"-{service_id}-1"):
            return service_id
    return None


def _load_docker_service_statuses(service_ids: set[str]) -> dict[str, tuple[str, V2Health]]:
    if not service_ids:
        return {}

    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}

    if result.returncode != 0:
        return {}

    statuses: dict[str, tuple[str, V2Health]] = {}
    for line in result.stdout.splitlines():
        try:
            container = json.loads(line)
        except json.JSONDecodeError:
            continue
        name = _coerce_str(container.get("Names"), "")
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


def _load_services() -> list[V2Service]:
    """Load services through core discovery, falling back deterministically."""
    try:
        from phlo.plugins.discovery import ServiceDiscovery

        discovered = ServiceDiscovery().discover().values()
    except Exception:
        return _fallback_services()

    services: list[V2Service] = []
    runtime_statuses = _load_docker_service_statuses({service.name for service in discovered})
    for service in discovered:
        status, health = runtime_statuses.get(
            service.name,
            ("unknown", V2Health(state="unknown", message="Runtime status unavailable")),
        )
        services.append(
            V2Service(
                id=service.name,
                name=service.name,
                kind=service.category or "service",
                status=status,
                health=health,
                depends_on=list(service.depends_on or []),
                impacts=[],
                links=[],
                metadata=_safe_metadata(
                    {
                        "default": bool(service.default),
                        "profile": service.profile,
                        "core": bool(getattr(service, "core", False)),
                    }
                ),
            )
        )

    return sorted(services, key=lambda item: item.id) if services else _fallback_services()


def _load_assets() -> list[V2Asset]:
    registry = _load_capability_registry()
    if registry is None:
        return []

    checks_by_asset: dict[str, list[str]] = {}
    for check in registry.list_checks():
        checks_by_asset.setdefault(check.asset_key, []).append(check.name)

    assets: list[V2Asset] = []
    for asset in registry.list_assets():
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
    return sorted(assets, key=lambda item: item.id)


def _table_name_from_asset(asset: Any) -> str | None:
    metadata = asset.metadata if isinstance(asset.metadata, Mapping) else {}
    for key in ("table", "table_name", "relation", "name"):
        value = metadata.get(key)
        if isinstance(value, str) and value:
            return value
    if "table" in asset.kinds or "dataset" in asset.kinds:
        return asset.key
    return None


def _load_tables() -> list[V2Table]:
    registry = _load_capability_registry()
    if registry is None:
        return []

    tables: list[V2Table] = []
    for asset in registry.list_assets():
        table_name = _table_name_from_asset(asset)
        if not table_name:
            continue
        metadata = asset.metadata if isinstance(asset.metadata, Mapping) else {}
        namespace = metadata.get("namespace")
        tables.append(
            V2Table(
                id=str(table_name),
                name=str(table_name),
                namespace=str(namespace) if namespace else asset.group,
                asset_id=asset.key,
                format=_coerce_str(metadata.get("format"), "") or None,
                branch=_coerce_str(metadata.get("branch"), "") or None,
                schema_name=_coerce_str(metadata.get("schema"), "") or None,
                metadata=_safe_metadata(metadata),
            )
        )
    return sorted(tables, key=lambda item: item.id)


def _load_quality() -> list[V2QualityCheck]:
    registry = _load_capability_registry()
    if registry is None:
        return []

    checks: list[V2QualityCheck] = []
    for check in registry.list_checks():
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
    return sorted(checks, key=lambda item: item.id)


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
    registry = _load_capability_registry()
    if registry is None:
        return []

    operations: list[V2Operation] = []
    for spec in registry.list_maintenance_read_models():
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
    return sorted(operations, key=lambda item: item.id)


def _load_logs() -> list[V2LogEvent]:
    try:
        from phlo.capabilities.telemetry import iter_telemetry_events
    except Exception:
        return []

    events: list[V2LogEvent] = []
    try:
        raw_events = list(iter_telemetry_events())[-50:]
    except Exception:
        return []

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
    return events


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
    return [
        V2Action(
            id=f"{service.id}:start",
            label="Start",
            kind="service.start",
            enabled=False,
            reason="Action descriptors are exposed; execution requires a guarded phlo-api operation.",
        ),
        V2Action(
            id=f"{service.id}:stop",
            label="Stop",
            kind="service.stop",
            enabled=False,
            reason="Action descriptors are exposed; execution requires a guarded phlo-api operation.",
        ),
        V2Action(
            id=f"{service.id}:restart",
            label="Restart",
            kind="service.restart",
            enabled=False,
            reason="Action descriptors are exposed; execution requires a guarded phlo-api operation.",
        ),
    ]


def _quality_actions(check: V2QualityCheck) -> list[V2Action]:
    return [
        V2Action(
            id=f"{check.id}:rerun",
            label="Re-run",
            kind="quality.rerun",
            enabled=False,
            reason="Quality execution needs a guarded phlo-api operation contract.",
        ),
        V2Action(
            id=f"{check.id}:acknowledge",
            label="Acknowledge",
            kind="quality.acknowledge",
            enabled=False,
            reason="Acknowledgements need a persisted v2 workflow contract.",
        ),
    ]


def _operation_actions(operation: V2Operation) -> list[V2Action]:
    return [
        V2Action(
            id=f"{operation.id}:retry",
            label="Retry",
            kind="operation.retry",
            enabled=False,
            reason="Retries need a guarded phlo-api operation execution contract.",
        ),
        V2Action(
            id=f"{operation.id}:open-target",
            label="Open Target",
            kind="operation.open_target",
            enabled=operation.target is not None,
            requires_confirmation=False,
        ),
    ]


def _table_columns_from_metadata(table: V2Table) -> list[str]:
    columns = table.metadata.get("columns")
    if isinstance(columns, list):
        return [str(column) for column in columns if column is not None]

    schema = table.metadata.get("schema")
    if isinstance(schema, Mapping):
        return [str(key) for key in schema.keys()]

    return []


def _load_branches() -> list[V2Branch]:
    """Return neutral branch data; core-only fallback is the main branch."""
    return [V2Branch(id="main", name="main", current=True, protected=True)]


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
    return V2AssetDetail(
        asset=asset,
        upstream=upstream,
        downstream=downstream,
        tables=tables,
        quality=quality,
        logs=_asset_related_logs(asset.id, logs),
        operations=_asset_related_operations(asset.id, operations),
    )


def _load_service_detail(service_id: str) -> V2ServiceDetail:
    services = _load_services()
    service = next((item for item in services if item.id == service_id), None)
    if service is None:
        raise _not_found("service", service_id)

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
    tables = _load_tables()
    table = next(
        (
            item
            for item in tables
            if item.id == table_id
            or item.name == table_id
            or f"{item.namespace}.{item.name}" == table_id
        ),
        None,
    )
    if table is None:
        raise _not_found("table", table_id)

    row_count_raw = table.metadata.get("records")
    row_count = row_count_raw if isinstance(row_count_raw, int) else None
    return V2TablePreview(
        table=table,
        columns=_table_columns_from_metadata(table),
        rows=[],
        row_count=row_count,
        limit=limit,
        offset=offset,
        has_more=False,
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

    contents = [
        V2ResourceRef(kind="table", id=table.id, label=table.name)
        for table in _load_tables()
        if table.branch in {None, "", branch.name}
    ]
    commits = [
        operation
        for operation in _load_operations()
        if operation.target is not None
        and operation.target.kind == "branch"
        and operation.target.id == branch.name
    ]
    return V2BranchDetail(
        branch=branch,
        contents=contents,
        commits=commits,
        compare={"added": 0, "changed": 0, "removed": 0},
    )


def _search_results(query: str) -> list[V2SearchResult]:
    needle = query.strip().lower()
    if not needle:
        return []

    results: list[V2SearchResult] = []
    for service in _load_services():
        haystack = " ".join([service.id, service.name, service.kind, service.status]).lower()
        if needle in haystack:
            results.append(
                V2SearchResult(
                    id=f"service:{service.id}",
                    label=service.name,
                    kind="service",
                    summary=f"{service.kind} · {service.status}",
                    href="/v2/services",
                )
            )

    for asset in _load_assets():
        haystack = " ".join(
            [asset.id, asset.name, asset.group or "", asset.description or "", *asset.kinds]
        ).lower()
        if needle in haystack:
            results.append(
                V2SearchResult(
                    id=f"asset:{asset.id}",
                    label=asset.name,
                    kind="asset",
                    summary=asset.description or asset.group,
                    href=f"/v2/asset/{asset.id}",
                )
            )

    for table in _load_tables():
        haystack = " ".join(
            [table.id, table.name, table.namespace or "", table.format or "", table.branch or ""]
        ).lower()
        if needle in haystack:
            results.append(
                V2SearchResult(
                    id=f"table:{table.id}",
                    label=table.namespace + "." + table.name if table.namespace else table.name,
                    kind="table",
                    summary=f"{table.format or 'table'} · {table.branch or 'main'}",
                    href=f"/v2/table/{table.id}",
                )
            )

    for check in _load_quality():
        haystack = " ".join(
            [check.id, check.name, check.asset_id, check.status, check.severity or ""]
        ).lower()
        if needle in haystack:
            results.append(
                V2SearchResult(
                    id=f"quality:{check.id}",
                    label=check.name,
                    kind="quality",
                    summary=f"{check.asset_id} · {check.status}",
                    href="/v2/quality",
                )
            )

    for extension in _load_extensions():
        haystack = " ".join([extension.id, extension.name, extension.version or ""]).lower()
        if needle in haystack:
            results.append(
                V2SearchResult(
                    id=f"extension:{extension.id}",
                    label=extension.name,
                    kind="extension",
                    summary=extension.settings_scope or extension.version,
                    href=f"/v2/extension/{extension.id}",
                )
            )

    return results[:25]


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

    return V2Settings(
        defaults=defaults,
        features={
            "operations": True,
            "assets": True,
            "tables": True,
            "quality": True,
            "logs": True,
            "branches": True,
            "extensions": True,
            "settings": True,
        },
        storage={"settings": "core"},
    )


@router.get("/overview", response_model=V2Overview)
def get_v2_overview() -> V2Overview:
    """Get the provider-neutral Observatory v2 overview."""
    services = _load_services()
    assets = _load_assets()
    tables = _load_tables()
    quality = _load_quality()
    return V2Overview(
        health=V2Health(state="unknown", message="Runtime status unavailable"),
        counters={
            "services": len(services),
            "operations": len(_load_operations()),
            "assets": len(assets),
            "tables": len(tables),
            "quality": len(quality),
            "incidents": 0,
        },
        recent=[],
    )


@router.get("/services", response_model=V2ServiceList)
def get_v2_services() -> V2ServiceList:
    """List provider-neutral Observatory v2 services."""
    return V2ServiceList(items=_load_services())


@router.get("/services/{service_id:path}", response_model=V2ServiceDetail)
def get_v2_service_detail(service_id: str) -> V2ServiceDetail:
    """Get provider-neutral Observatory v2 service detail."""
    return _load_service_detail(service_id)


@router.get("/operations", response_model=V2OperationList)
def get_v2_operations() -> V2OperationList:
    """List provider-neutral Observatory v2 operations."""
    return V2OperationList(items=_load_operations())


@router.get("/operations/{operation_id:path}", response_model=V2OperationDetail)
def get_v2_operation_detail(operation_id: str) -> V2OperationDetail:
    """Get provider-neutral Observatory v2 operation detail."""
    return _load_operation_detail(operation_id)


@router.get("/assets", response_model=V2AssetList)
def get_v2_assets() -> V2AssetList:
    """List provider-neutral Observatory v2 assets."""
    return V2AssetList(items=_load_assets())


@router.get("/assets/{asset_id:path}", response_model=V2AssetDetail)
def get_v2_asset_detail(asset_id: str) -> V2AssetDetail:
    """Get provider-neutral Observatory v2 asset detail."""
    return _load_asset_detail(asset_id)


@router.get("/tables", response_model=V2TableList)
def get_v2_tables() -> V2TableList:
    """List provider-neutral Observatory v2 tables."""
    return V2TableList(items=_load_tables())


@router.get("/table-preview/{table_id:path}", response_model=V2TablePreview)
def get_v2_table_preview(table_id: str, limit: int = 50, offset: int = 0) -> V2TablePreview:
    """Get provider-neutral table preview metadata."""
    return _load_table_preview(table_id, limit=limit, offset=offset)


@router.get("/quality", response_model=V2QualityList)
def get_v2_quality() -> V2QualityList:
    """List provider-neutral Observatory v2 quality checks."""
    return V2QualityList(items=_load_quality())


@router.get("/quality/{check_id:path}", response_model=V2QualityDetail)
def get_v2_quality_detail(check_id: str) -> V2QualityDetail:
    """Get provider-neutral Observatory v2 quality detail."""
    return _load_quality_detail(check_id)


@router.get("/logs", response_model=V2LogList)
def get_v2_logs() -> V2LogList:
    """List provider-neutral Observatory v2 log events."""
    return V2LogList(items=_load_logs())


@router.get("/logs/facets", response_model=V2LogFacets)
def get_v2_log_facets() -> V2LogFacets:
    """Get provider-neutral Observatory v2 log facets."""
    return _load_log_facets(_load_logs())


@router.get("/branches", response_model=V2BranchList)
def get_v2_branches() -> V2BranchList:
    """List provider-neutral Observatory v2 branches."""
    return V2BranchList(items=_load_branches())


@router.get("/branches/{branch_name:path}", response_model=V2BranchDetail)
def get_v2_branch_detail(branch_name: str) -> V2BranchDetail:
    """Get provider-neutral Observatory v2 branch detail."""
    return _load_branch_detail(branch_name)


@router.get("/extensions", response_model=V2ExtensionList)
def get_v2_extensions() -> V2ExtensionList:
    """List provider-neutral Observatory v2 extensions."""
    return V2ExtensionList(items=_load_extensions())


@router.get("/extensions/{extension_id:path}", response_model=V2ExtensionDetail)
def get_v2_extension_detail(extension_id: str) -> V2ExtensionDetail:
    """Get provider-neutral Observatory v2 extension detail."""
    return _load_extension_detail(extension_id)


@router.get("/settings", response_model=V2Settings)
def get_v2_settings() -> V2Settings:
    """Get provider-neutral Observatory v2 settings."""
    return _load_settings()


@router.get("/search", response_model=V2SearchList)
def get_v2_search(q: str) -> V2SearchList:
    """Search provider-neutral Observatory v2 resources."""
    return V2SearchList(items=_search_results(q))

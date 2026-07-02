"""Provider-neutral Observatory API resources."""

from __future__ import annotations

import asyncio
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, is_dataclass
import importlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any, cast

from fastapi import APIRouter, BackgroundTasks, Body, Query, Request
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import AliasChoices, BaseModel, Field, ValidationError

from phlo_api.observatory_api.observatory_actions import execute_observatory_action
from phlo_api.observatory_api.observatory_cache import ReadModelCache
from phlo_api.observatory_api.observatory_capabilities import build_capability_inventory
from phlo_api.observatory_api.observatory_models import (
    HealthState,
    ObservatoryAction,
    ObservatoryActionRequest,
    ObservatoryActionResult,
    ObservatoryAsset,
    ObservatoryAssetDetail,
    ObservatoryAssetGraph,
    ObservatoryAssetGraphEdge,
    ObservatoryAssetGraphNode,
    ObservatoryAssetList,
    ObservatoryBranch,
    ObservatoryBranchDetail,
    ObservatoryBranchList,
    ObservatoryCapabilities,
    ObservatoryCapabilityInventory,
    ObservatoryCapabilityPage,
    ObservatoryCapabilityProvider,
    ObservatoryContributingRowsPageRequest,
    ObservatoryContributingRowsPageResponse,
    ObservatoryContributingRowsQueryRequest,
    ObservatoryContributingRowsQueryResponse,
    ObservatoryControlEvidence,
    ObservatoryAccessActivity,
    ObservatoryConsumerAdoption,
    ObservatoryDataProduct,
    ObservatoryDataProductControl,
    ObservatoryDataProductList,
    ObservatoryDataProductProfile,
    ObservatoryDataProductUsage,
    ObservatoryDependencyActivity,
    ObservatoryExtension,
    ObservatoryExtensionDetail,
    ObservatoryExtensionList,
    ObservatoryHealth,
    ObservatoryGovernanceMatrix,
    ObservatoryGovernanceRow,
    ObservatoryLogEvent,
    ObservatoryLogFacets,
    ObservatoryLogList,
    ObservatoryOperation,
    ObservatoryOperationDetail,
    ObservatoryOperationList,
    ObservatoryOverview,
    ObservatoryPackageInstallRequest,
    ObservatoryPackageInstallResult,
    ObservatoryQualityCheck,
    ObservatoryQualityDetail,
    ObservatoryQualityList,
    ObservatoryQueryRequest,
    ObservatoryQueryResult,
    PublicationState,
    ObservatoryImpactedAsset,
    ObservatoryResourceRef,
    ObservatoryRouteRequirement,
    ObservatoryRowJourney,
    ObservatoryRun,
    ObservatoryRunList,
    ObservatorySavedQuery,
    ObservatorySavedQueryList,
    ObservatorySavedQueryRequest,
    ObservatorySearchList,
    ObservatorySearchResult,
    ObservatoryService,
    ObservatoryServiceDetail,
    ObservatoryServiceList,
    ObservatorySettings,
    ObservatoryStageDiff,
    ObservatorySurfaceList,
    ObservatorySurfaceItem,
    ObservatoryTable,
    ObservatoryTableList,
    ObservatoryTablePreview,
    ObservatoryTelemetryPrivacyPolicy,
    ObservatoryUpstreamTableRef,
)
from phlo_api.observatory_api.observatory_metadata import safe_metadata as _safe_metadata
from phlo_api.observatory_api.observatory_operation_journal import (
    append_operation,
    build_operation_observability_context,
    load_operation_journal,
    operation_from_workflow_action,
    record_action_result,
    sort_operations,
)
from phlo_api.observatory_api.orchestrator_operations import resolve_orchestrator_operations
from phlo_api.observatory_api.observatory_runs import load_runs
from phlo_api.observatory_api.observatory_saved_queries import (
    dedupe_saved_queries as _dedupe_saved_queries_impl,
    load_saved_queries as _load_saved_queries_impl,
    save_query as _save_query_impl,
    validate_saved_query_sql as _validate_saved_query_sql_impl,
    write_saved_queries as _write_saved_queries_impl,
)
from phlo_api.observatory_api.observatory_search import search_results as _search_results_impl
from phlo_api.observatory_api.observatory_services import load_project_docker_containers
from phlo_api.observatory_api.observatory_services import load_services as _load_services_impl
from phlo_api.observatory_api.observatory_services import (
    service_config_from_definition as _service_config_from_definition,
)
from phlo_api.observatory_api.observatory_services import (
    service_ports_from_definition as _service_ports_from_definition,
)
from phlo_api.observatory_api.observatory_workflow_wizard import (
    ObservatoryWorkflowActionRequest,
    ObservatoryWorkflowActionResult,
    ObservatoryWorkflowProposalRequest,
    apply_workflow_action,
    build_workflow_proposal,
    build_workflow_wizard_payload,
)
from phlo.cli.commands.plugin.install import resolve_install_target
from phlo.plugins.registry_client import get_registry_data
from phlo_api.api.operation_controls import (
    audit_operation,
    enforce_rate_limit,
    replay_or_execute_async,
    require_scope,
)
from phlo_api.pagination import paginate_items

router = APIRouter(tags=["observatory"])


def _jsonable_result(result: Any) -> dict[str, Any]:
    if isinstance(result, BaseModel):
        return result.model_dump(mode="json")
    if isinstance(result, dict):
        return result
    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")
    return {"result": result}


class ObservatoryMaterializeAssetRequest(BaseModel):
    model_config = {"populate_by_name": True}

    dry_run: bool = True
    partition_key: str | None = Field(
        default=None, validation_alias=AliasChoices("partition_key", "partition")
    )
    job_name: str | None = None
    repository_location_name: str | None = None
    repository_name: str | None = None
    run_config: dict[str, Any] | None = None
    idempotency_key: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)


class ObservatoryRetryRunRequest(BaseModel):
    dry_run: bool = True
    strategy: str = "FROM_FAILURE"
    idempotency_key: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)


class ObservatoryCancelRunRequest(BaseModel):
    reason: str | None = None
    idempotency_key: str | None = None


class ObservatoryBackfillAssetRequest(BaseModel):
    dry_run: bool = True
    partitions: list[str] = Field(default_factory=list)
    partition_range: dict[str, str] | None = None
    partition_set_name: str | None = None
    repository_location_name: str | None = None
    repository_name: str | None = None
    idempotency_key: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)


class ObservatorySchemaDiffRequest(BaseModel):
    asset_key: str
    from_run: str | None = None
    to_run: str | None = None


_READ_QUERY_RE = re.compile(
    r"^\s*select\s+\*\s+from\s+(?P<table>[A-Za-z0-9_.:-]+)(?:\s+limit\s+(?P<limit>\d+))?\s*;?\s*$",
    re.IGNORECASE,
)
_TABLE_LIST_METADATA_PREFIX_DENYLIST = ("phlo/compiled_sql",)
_TABLE_LIST_METADATA_DENYLIST = {"preview_rows"}
_FAST_READ_MODEL_TTL_SECONDS = 30
_EXPENSIVE_READ_MODEL_TTL_SECONDS = 120
_READ_MODEL_CACHE = ReadModelCache(project_key=lambda: str(_project_root()))


def _cached_read_model(name: str, ttl_seconds: float, loader: Any) -> Any:
    return _READ_MODEL_CACHE.cached(name, ttl_seconds, loader)


def _clear_read_model_cache() -> None:
    _READ_MODEL_CACHE.clear()


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


def _observatory_state_dir() -> Path:
    state_dir = _project_root() / ".phlo" / "observatory"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def _saved_queries_path() -> Path:
    return _observatory_state_dir() / "saved_queries.json"


def _branches_path() -> Path:
    return _observatory_state_dir() / "branches.json"


def _lakehouse_manifest_path() -> Path:
    return _observatory_state_dir() / "lakehouse_manifest.json"


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
        module_name = "phlo_observatory_observatory_workflow_" + "_".join(
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


def _load_services() -> list[ObservatoryService]:
    project_root = _project_root()
    return _load_services_impl(
        project_root, containers=load_project_docker_containers(project_root)
    )


def _overview_health_from_services(services: Sequence[ObservatoryService]) -> ObservatoryHealth:
    if not services:
        return ObservatoryHealth(state="unknown", message="No services discovered")

    runtime_services = _runtime_services(services)
    if not runtime_services:
        return ObservatoryHealth(state="unknown", message="No runtime containers found")

    status_counts = Counter(service.status for service in runtime_services)
    attention = sum(
        1
        for service in runtime_services
        if service.status in {"unhealthy", "starting"}
        or service.health.state in {"error", "warning"}
        or (service.status == "stopped" and service.health.state != "ok")
    )

    if attention:
        return ObservatoryHealth(
            state="warning",
            message=f"{attention} services need attention",
        )

    running = status_counts["running"]
    if running:
        return ObservatoryHealth(state="ok", message=f"{running} services running")

    unknown = status_counts["unknown"]
    if unknown == len(runtime_services):
        return ObservatoryHealth(state="unknown", message="No runtime containers found")

    return ObservatoryHealth(state="unknown", message="Runtime status incomplete")


def _runtime_services(services: Sequence[ObservatoryService]) -> list[ObservatoryService]:
    return [
        service
        for service in services
        if service.status != "unknown"
        or service.health.state != "unknown"
        or service.health.message != "Runtime status unavailable"
    ]


def _load_assets() -> list[ObservatoryAsset]:
    registry = _load_capability_registry()
    if registry is None:
        return sorted(_manifest_records("assets", ObservatoryAsset), key=lambda item: item.id)

    checks_by_asset: dict[str, list[str]] = {}
    for check in registry.list("check"):
        checks_by_asset.setdefault(check.asset_key, []).append(check.name)

    assets: list[ObservatoryAsset] = list(_manifest_records("assets", ObservatoryAsset))
    for asset in registry.list("asset"):
        assets.append(
            ObservatoryAsset(
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


def _load_tables(*, enrich_catalog: bool = True) -> list[ObservatoryTable]:
    registry = _load_capability_registry()
    if registry is None:
        return sorted(_manifest_records("tables", ObservatoryTable), key=lambda item: item.id)

    catalog_tables = _catalog_tables() if enrich_catalog else None
    tables: list[ObservatoryTable] = list(_manifest_records("tables", ObservatoryTable))
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
            ObservatoryTable(
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


def _compact_table(table: ObservatoryTable) -> ObservatoryTable:
    """Return a table payload suitable for frequently refreshed UI surfaces."""
    metadata = {
        key: value
        for key, value in table.metadata.items()
        if key not in _TABLE_LIST_METADATA_DENYLIST
        and not any(key.startswith(prefix) for prefix in _TABLE_LIST_METADATA_PREFIX_DENYLIST)
    }
    return table.model_copy(update={"metadata": metadata})


def _compact_tables(tables: Iterable[ObservatoryTable]) -> list[ObservatoryTable]:
    return [_compact_table(table) for table in tables]


def _load_tables_without_catalog() -> list[ObservatoryTable]:
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


def _load_quality() -> list[ObservatoryQualityCheck]:
    registry = _load_capability_registry()
    if registry is None:
        return sorted(
            _manifest_records("quality", ObservatoryQualityCheck), key=lambda item: item.id
        )

    checks: list[ObservatoryQualityCheck] = list(
        _manifest_records("quality", ObservatoryQualityCheck)
    )
    for check in registry.list("check"):
        check_id = f"{check.asset_key}:{check.name}"
        checks.append(
            ObservatoryQualityCheck(
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


def _metadata_strings(metadata: Mapping[str, Any], *keys: str) -> list[str]:
    values: list[str] = []
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            values.extend(str(item).strip() for item in value if str(item).strip())
    return sorted(set(values))


def _publication_state(metadata: Mapping[str, Any]) -> str:
    value = metadata.get("publication_state") or metadata.get("publishing_state")
    if isinstance(value, str) and value.lower() in {"draft", "published", "retired"}:
        return value.lower()
    if metadata.get("published") is True:
        return "published"
    return "draft"


def _readiness_state(checks: Sequence[ObservatoryQualityCheck]) -> str:
    if not checks:
        return "unknown"
    statuses = {check.status for check in checks}
    if "failing" in statuses:
        return "error"
    if "warning" in statuses or "unknown" in statuses:
        return "warning"
    return "ok"


def _data_product_from_asset(
    asset: ObservatoryAsset,
    *,
    tables: Sequence[ObservatoryTable],
    quality: Sequence[ObservatoryQualityCheck],
) -> ObservatoryDataProduct:
    metadata = asset.metadata if isinstance(asset.metadata, Mapping) else {}
    owner = metadata.get("owner") or metadata.get("team") or metadata.get("maintainer")
    product_tables = [table for table in tables if table.asset_id == asset.id]
    product_quality = [check for check in quality if check.asset_id == asset.id]
    source_refs = [ObservatoryResourceRef(kind="asset", id=asset.id, label=asset.name)]
    source_refs.extend(
        ObservatoryResourceRef(kind="table", id=table.id, label=table.name)
        for table in product_tables
    )
    return ObservatoryDataProduct(
        id=asset.id,
        name=_coerce_str(metadata.get("data_product_name"), asset.name),
        description=asset.description,
        owner=_coerce_str(owner, "") or None,
        classifications=_metadata_strings(
            metadata,
            "classification",
            "classifications",
            "sensitivity",
            "tags",
        ),
        publication_state=cast(PublicationState, _publication_state(metadata)),
        readiness_state=cast(HealthState, _readiness_state(product_quality)),
        candidate=False,
        kinds=_sorted_strings([*asset.kinds, "asset"]),
        source_refs=source_refs,
        metadata=_safe_metadata(metadata),
    )


def _candidate_data_product_from_table(table: ObservatoryTable) -> ObservatoryDataProduct:
    metadata = table.metadata if isinstance(table.metadata, Mapping) else {}
    return ObservatoryDataProduct(
        id=f"candidate:{table.id}",
        name=table.name,
        description=None,
        owner=None,
        classifications=_metadata_strings(metadata, "classification", "classifications"),
        publication_state="draft",
        readiness_state="unknown",
        candidate=True,
        kinds=_sorted_strings([table.format or "table", "table"]),
        source_refs=[ObservatoryResourceRef(kind="table", id=table.id, label=table.name)],
        metadata=_safe_metadata(
            {
                **metadata,
                "candidate_reason": "table has no promoted Data Product",
                "table_id": table.id,
            }
        ),
    )


def _load_data_products() -> list[ObservatoryDataProduct]:
    tables = _load_tables_without_catalog()
    quality = _load_quality()
    assets = _load_assets()
    products = [_data_product_from_asset(asset, tables=tables, quality=quality) for asset in assets]
    products.extend(
        _candidate_data_product_from_table(table)
        for table in tables
        if table.asset_id is None or not any(asset.id == table.asset_id for asset in assets)
    )
    return sorted(_merge_by_id(products), key=lambda item: item.name.lower())


def _load_data_product_profile(product_id: str) -> ObservatoryDataProductProfile:
    assets = _load_assets()
    tables = _load_tables_without_catalog()
    quality = _load_quality()
    asset = next((item for item in assets if item.id == product_id), None)
    if asset is None:
        table = next((item for item in tables if item.id == product_id), None)
        if table is None or table.asset_id is None:
            raise _not_found("data product", product_id)
        asset = next((item for item in assets if item.id == table.asset_id), None)
    if asset is None:
        raise _not_found("data product", product_id)

    product = _data_product_from_asset(asset, tables=tables, quality=quality)
    product_tables = [table for table in tables if table.asset_id == asset.id]
    product_quality = [check for check in quality if check.asset_id == asset.id]
    governance = _governance_controls_for_product(product, product_quality)
    usage = _load_data_product_usage(product, asset=asset, tables=product_tables)
    related_ids = {
        asset.id,
        *[table.id for table in product_tables],
        *[check.id for check in product_quality],
    }
    upstream = [
        ObservatoryResourceRef(kind="asset", id=item.id, label=item.name)
        for item in assets
        if item.id in set(asset.dependencies)
    ]
    downstream = [
        ObservatoryResourceRef(kind="asset", id=item.id, label=item.name)
        for item in assets
        if asset.id in item.dependencies
    ]
    logs = [
        event
        for event in _load_logs()
        if event.resource is not None and event.resource.id in related_ids
    ]
    operations = [
        operation
        for operation in _load_operations()
        if operation.target is not None and operation.target.id in related_ids
    ]
    return ObservatoryDataProductProfile(
        product=product,
        asset=asset,
        tables=product_tables,
        quality=product_quality,
        upstream=upstream,
        downstream=downstream,
        logs=logs,
        operations=operations,
        governance=governance,
        usage=usage,
        sections={
            "overview": True,
            "contract": bool(product.owner or product.description),
            "lineage": bool(upstream or downstream or asset.dependencies),
            "quality": bool(product_quality),
            "access": False,
            "usage": _has_usage(usage),
            "pipelines": bool(operations),
            "governance": bool(governance),
            "publishing": True,
        },
    )


def _load_governance_matrix() -> ObservatoryGovernanceMatrix:
    products = _load_data_products()
    quality = _load_quality()
    rows = [
        _governance_row_for_product(
            product,
            [
                check
                for check in quality
                if any(ref.id == check.asset_id for ref in product.source_refs)
            ],
        )
        for product in products
    ]
    status_counts = Counter(row.status for row in rows)
    return ObservatoryGovernanceMatrix(
        controls=["owner", "classification", "blocking_quality"],
        rows=rows,
        status_counts={status: status_counts.get(status, 0) for status in CONTROL_STATUSES},
    )


CONTROL_STATUSES = ("pass", "fail", "warning", "unknown", "not_applicable")


def _governance_row_for_product(
    product: ObservatoryDataProduct,
    quality: Sequence[ObservatoryQualityCheck],
) -> ObservatoryGovernanceRow:
    controls = _governance_controls_for_product(product, quality)
    return ObservatoryGovernanceRow(
        product=product,
        owner=product.owner,
        classifications=product.classifications,
        status=_aggregate_control_status(controls),
        controls=controls,
    )


def _governance_controls_for_product(
    product: ObservatoryDataProduct,
    quality: Sequence[ObservatoryQualityCheck],
) -> list[ObservatoryDataProductControl]:
    product_ref = ObservatoryResourceRef(kind="data_product", id=product.id, label=product.name)
    owner_evidence = (
        [
            ObservatoryControlEvidence(
                kind="fact",
                id=f"{product.id}:owner",
                label="Owner",
                value=product.owner,
                resource=product_ref,
            )
        ]
        if product.owner
        else []
    )
    classification_evidence = [
        ObservatoryControlEvidence(
            kind="classification",
            id=f"{product.id}:classification:{classification}",
            label="Classification",
            value=classification,
            resource=product_ref,
        )
        for classification in product.classifications
    ]
    blocking_quality = [check for check in quality if check.blocking]
    quality_evidence = [
        ObservatoryControlEvidence(
            kind="quality_check",
            id=check.id,
            label=check.name,
            value=check.status,
            resource=ObservatoryResourceRef(kind="quality", id=check.id, label=check.name),
            metadata={"blocking": check.blocking, "severity": check.severity},
        )
        for check in blocking_quality
    ]
    quality_status = _quality_control_status(product, blocking_quality)
    return [
        ObservatoryDataProductControl(
            id="owner",
            label="Owner assigned",
            status="pass" if product.owner else "fail",
            message="One owner is assigned." if product.owner else "No owner assigned.",
            evidence=owner_evidence,
        ),
        ObservatoryDataProductControl(
            id="classification",
            label="Classification declared",
            status="pass" if classification_evidence else "fail",
            message=(
                "Classification evidence is present."
                if classification_evidence
                else "No classification evidence returned."
            ),
            evidence=classification_evidence,
        ),
        ObservatoryDataProductControl(
            id="blocking_quality",
            label="Blocking quality clear",
            status=quality_status,
            message=_quality_control_message(product, blocking_quality, quality_status),
            evidence=quality_evidence,
        ),
    ]


def _quality_control_status(
    product: ObservatoryDataProduct,
    quality: Sequence[ObservatoryQualityCheck],
) -> str:
    if product.candidate:
        return "not_applicable"
    if not quality:
        return "unknown"
    statuses = {check.status for check in quality}
    if "failing" in statuses:
        return "fail"
    if "warning" in statuses:
        return "warning"
    if "unknown" in statuses:
        return "unknown"
    return "pass"


def _quality_control_message(
    product: ObservatoryDataProduct,
    quality: Sequence[ObservatoryQualityCheck],
    status: str,
) -> str:
    if status == "not_applicable":
        return "Candidate products are not quality-gated yet."
    if not quality:
        return "No blocking quality evidence returned."
    if status == "fail":
        return "A blocking quality check is failing."
    if status == "warning":
        return "A blocking quality check is warning."
    if status == "unknown":
        return "A blocking quality check is unknown."
    return "Blocking quality checks are clear."


def _aggregate_control_status(controls: Sequence[ObservatoryDataProductControl]) -> str:
    statuses = [control.status for control in controls]
    for status in ("fail", "warning", "unknown", "not_applicable"):
        if status in statuses:
            return status
    return "pass"


def _load_data_product_usage(
    product: ObservatoryDataProduct,
    *,
    asset: ObservatoryAsset,
    tables: Sequence[ObservatoryTable],
) -> ObservatoryDataProductUsage:
    usage_model = _usage_manifest()
    policy = _usage_privacy_policy(usage_model.get("privacy_policy"))
    related_ids = {product.id, asset.id, *[table.id for table in tables]}
    access = [
        _access_activity_from_mapping(item, product=product, policy=policy)
        for item in _usage_items(usage_model, "access_activity", related_ids)
    ]
    dependencies = [
        _dependency_activity_from_mapping(item)
        for item in _usage_items(usage_model, "dependency_activity", related_ids)
    ]
    if not dependencies and asset.dependencies:
        dependencies = [
            ObservatoryDependencyActivity(
                id=f"{dependency}->{asset.id}",
                source=ObservatoryResourceRef(kind="asset", id=dependency, label=dependency),
                target=ObservatoryResourceRef(
                    kind="data_product", id=product.id, label=product.name
                ),
                kind="asset_dependency",
            )
            for dependency in asset.dependencies
        ]
    consumers = [
        _consumer_adoption_from_mapping(item, product=product)
        for item in _usage_items(usage_model, "consumer_adoption", related_ids)
    ]
    for item in _metadata_list(asset.metadata, "consumers", "consumer_adoption"):
        consumers.append(_consumer_adoption_from_mapping(item, product=product))
    return ObservatoryDataProductUsage(
        privacy_policy=policy,
        access_activity=access,
        dependency_activity=dependencies,
        consumer_adoption=_merge_by_id(consumers),
    )


def _usage_manifest() -> Mapping[str, Any]:
    manifest = _load_lakehouse_manifest()
    usage = manifest.get("usage") if isinstance(manifest, Mapping) else None
    return usage if isinstance(usage, Mapping) else {}


def _usage_privacy_policy(raw: Any) -> ObservatoryTelemetryPrivacyPolicy:
    policy = raw if isinstance(raw, Mapping) else {}
    identity_detail = _coerce_str(policy.get("identity_detail"), "aggregate")
    if identity_detail not in {"anonymous", "aggregate", "identity", "audit_only"}:
        identity_detail = "aggregate"
    return ObservatoryTelemetryPrivacyPolicy(
        identity_detail=cast(Any, identity_detail),
        retention_days=_coerce_int(policy.get("retention_days"), 0) or None,
        audit_drilldown=bool(policy.get("audit_drilldown")),
        metadata=_safe_metadata(policy),
    )


def _usage_items(
    usage_model: Mapping[str, Any],
    key: str,
    related_ids: set[str],
) -> list[Mapping[str, Any]]:
    raw_items = usage_model.get(key)
    if not isinstance(raw_items, list):
        return []
    items: list[Mapping[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, Mapping):
            continue
        item_product = _coerce_str(item.get("product_id") or item.get("asset_id"), "")
        source = item.get("source")
        target = item.get("target")
        linked_ids = {item_product}
        for ref in (source, target):
            if isinstance(ref, Mapping):
                linked_ids.add(_coerce_str(ref.get("id"), ""))
        if linked_ids & related_ids:
            items.append(item)
    return items


def _access_activity_from_mapping(
    item: Mapping[str, Any],
    *,
    product: ObservatoryDataProduct,
    policy: ObservatoryTelemetryPrivacyPolicy,
) -> ObservatoryAccessActivity:
    actor = _coerce_str(item.get("actor") or item.get("user") or item.get("principal"), "")
    actor_label = _privacy_shaped_actor(actor, policy)
    metadata = _safe_metadata(
        {
            key: value
            for key, value in item.items()
            if key not in {"actor", "user", "principal", "email"}
        }
    )
    if policy.identity_detail == "audit_only":
        metadata["audit_drilldown"] = policy.audit_drilldown
    return ObservatoryAccessActivity(
        id=_coerce_str(item.get("id"), f"{product.id}:access:{len(metadata)}"),
        action=_coerce_str(item.get("action"), "access"),
        actor_label=actor_label,
        actor_kind=_coerce_str(item.get("actor_kind"), "") or None,
        count=max(1, _coerce_int(item.get("count"), 1)),
        last_seen_at=_coerce_str(item.get("last_seen_at") or item.get("timestamp"), "") or None,
        metadata=metadata,
    )


def _privacy_shaped_actor(actor: str, policy: ObservatoryTelemetryPrivacyPolicy) -> str | None:
    if policy.identity_detail == "identity":
        return actor or None
    if policy.identity_detail == "audit_only":
        return "audit only"
    if policy.identity_detail == "anonymous":
        return "anonymous"
    return "aggregated users"


def _dependency_activity_from_mapping(item: Mapping[str, Any]) -> ObservatoryDependencyActivity:
    return ObservatoryDependencyActivity(
        id=_coerce_str(item.get("id"), "dependency"),
        source=_resource_ref_from_mapping(item.get("source"), "asset"),
        target=_resource_ref_from_mapping(item.get("target"), "data_product"),
        kind=_coerce_str(item.get("kind"), "dependency"),
        count=max(1, _coerce_int(item.get("count"), 1)),
        last_seen_at=_coerce_str(item.get("last_seen_at") or item.get("timestamp"), "") or None,
        metadata=_safe_metadata(item),
    )


def _consumer_adoption_from_mapping(
    item: Mapping[str, Any],
    *,
    product: ObservatoryDataProduct,
) -> ObservatoryConsumerAdoption:
    consumer = _coerce_str(item.get("consumer") or item.get("name") or item.get("id"), "consumer")
    return ObservatoryConsumerAdoption(
        id=_coerce_str(item.get("id"), f"{product.id}:consumer:{consumer}"),
        consumer=consumer,
        kind=_coerce_str(item.get("kind"), "team"),
        owner=_coerce_str(item.get("owner"), "") or None,
        status=_coerce_str(item.get("status"), "declared"),
        declared_at=_coerce_str(item.get("declared_at"), "") or None,
        metadata=_safe_metadata(item),
    )


def _resource_ref_from_mapping(raw: Any, default_kind: str) -> ObservatoryResourceRef:
    if isinstance(raw, Mapping):
        ref_id = _coerce_str(raw.get("id"), default_kind)
        return ObservatoryResourceRef(
            kind=_coerce_str(raw.get("kind"), default_kind),
            id=ref_id,
            label=_coerce_str(raw.get("label") or raw.get("name"), ref_id),
        )
    ref_id = _coerce_str(raw, default_kind)
    return ObservatoryResourceRef(kind=default_kind, id=ref_id, label=ref_id)


def _metadata_list(metadata: Mapping[str, Any], *keys: str) -> list[Mapping[str, Any]]:
    for key in keys:
        raw = metadata.get(key)
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, Mapping)]
    return []


def _has_usage(usage: ObservatoryDataProductUsage) -> bool:
    return bool(usage.access_activity or usage.dependency_activity or usage.consumer_adoption)


def _operation_from_maintenance_status(status: Any) -> ObservatoryOperation:
    payload = _dataclass_dict(status)
    operation = _coerce_str(payload.get("operation"), "operation")
    namespace = _coerce_str(payload.get("namespace"), "default")
    ref = _coerce_str(payload.get("ref"), "main")
    completed_at = payload.get("completed_at")
    state = "ok" if payload.get("status") == "succeeded" else "unknown"
    return ObservatoryOperation(
        id=":".join([operation, namespace, ref]),
        name=operation,
        kind="maintenance",
        status="succeeded" if payload.get("status") == "succeeded" else "unknown",
        health=ObservatoryHealth(state=state),
        target=ObservatoryResourceRef(kind="branch", id=ref, label=ref),
        completed_at=completed_at.isoformat() if hasattr(completed_at, "isoformat") else None,
        duration_seconds=payload.get("duration_seconds"),
        metadata=_safe_metadata(payload),
    )


def _load_wap_report_operations() -> list[ObservatoryOperation]:
    reports_dir = _project_root() / ".phlo" / "wap-reports"
    if not reports_dir.exists():
        return []

    operations: list[ObservatoryOperation] = []
    for path in reports_dir.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, Mapping):
            continue
        run_id = _coerce_str(payload.get("run_id"), path.stem)
        branch = _coerce_str(payload.get("branch"), "unknown")
        status = _coerce_str(payload.get("status"), "unknown")
        succeeded = status == "promoted"
        failed = status.endswith("_failed")
        operations.append(
            ObservatoryOperation(
                id=f"wap:{run_id}",
                name="WAP publish" if succeeded else "WAP lifecycle",
                kind="wap",
                status="succeeded" if succeeded else "failed" if failed else "running",
                health=ObservatoryHealth(
                    state="ok" if succeeded else "error" if failed else "warning",
                    message=status.replace("_", " "),
                ),
                target=ObservatoryResourceRef(kind="branch", id=branch, label=branch),
                started_at=payload.get("created_at")
                if isinstance(payload.get("created_at"), str)
                else None,
                completed_at=payload.get("updated_at")
                if isinstance(payload.get("updated_at"), str)
                else None,
                metadata=_safe_metadata(payload),
            )
        )
    return operations


def _load_operations() -> list[ObservatoryOperation]:
    operations = [
        *list(load_operation_journal(_project_root())),
        *_load_wap_report_operations(),
        *_manifest_records("operations", ObservatoryOperation),
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


def _filter_operations(
    operations: list[ObservatoryOperation],
    *,
    status: str | None = None,
    kind: str | None = None,
    q: str | None = None,
    limit: int | None = None,
) -> list[ObservatoryOperation]:
    status_filter = status.strip().lower() if status else None
    kind_filter = kind.strip().lower() if kind else None
    query = q.strip().lower() if q else None

    filtered: list[ObservatoryOperation] = []
    for operation in operations:
        if status_filter and operation.status.lower() != status_filter:
            continue
        if kind_filter and operation.kind.lower() != kind_filter:
            continue
        if query and query not in operation.model_dump_json().lower():
            continue
        filtered.append(operation)
        if limit is not None and len(filtered) >= limit:
            break
    return filtered


def _load_runs() -> list[ObservatoryRun]:
    manifest_runs = list(_manifest_records("runs", ObservatoryRun))
    provider_runs = load_runs()
    return sorted(
        _merge_by_id([*manifest_runs, *provider_runs]),
        key=lambda item: item.completed_at or item.started_at or item.id,
        reverse=True,
    )


def _load_logs() -> list[ObservatoryLogEvent]:
    project_root = _project_root()
    events = [
        *_manifest_records("logs", ObservatoryLogEvent),
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
            ObservatoryLogEvent(
                id=_coerce_str(event.get("id"), f"log-{index}"),
                timestamp=_coerce_str(timestamp, "") or None,
                level=level,
                message=name,
                source=_coerce_str(event.get("source"), "") or None,
                metadata=_safe_metadata(event),
            )
        )
    return events[:100]


def _load_project_log_events(project_root: Path) -> list[ObservatoryLogEvent]:
    """Load structured Phlo project logs from `.phlo/logs/*.log`."""
    logs_dir = project_root / ".phlo" / "logs"
    if not logs_dir.exists():
        return []

    events: list[ObservatoryLogEvent] = []
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
                ObservatoryLogEvent(
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


def _asset_related_logs(
    asset_id: str, logs: list[ObservatoryLogEvent]
) -> list[ObservatoryLogEvent]:
    return [
        event
        for event in logs
        if event.resource is not None
        and event.resource.kind == "asset"
        and event.resource.id == asset_id
    ]


def _asset_related_operations(
    asset_id: str, operations: list[ObservatoryOperation]
) -> list[ObservatoryOperation]:
    return [
        operation
        for operation in operations
        if operation.target is not None
        and operation.target.kind in {"asset", "table"}
        and operation.target.id == asset_id
    ]


def _service_actions(service: ObservatoryService) -> list[ObservatoryAction]:
    if not service.in_stack:
        package_installed = service.metadata.get("package_installed") is not False
        package_name = _coerce_str(service.metadata.get("package"), service.name)
        return [
            ObservatoryAction(
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
        ObservatoryAction(
            id=f"{service.id}:start",
            label="Start",
            kind="service.start",
            enabled=service.status == "stopped",
            reason=None
            if service.status == "stopped"
            else "Service is already running, starting, or its runtime state is unknown.",
        ),
        ObservatoryAction(
            id=f"{service.id}:stop",
            label="Stop",
            kind="service.stop",
            enabled=service.status in {"running", "unhealthy", "starting"},
            reason=None
            if service.status in {"running", "unhealthy", "starting"}
            else "Service is not running.",
        ),
        ObservatoryAction(
            id=f"{service.id}:restart",
            label="Restart",
            kind="service.restart",
            enabled=service.status in {"running", "unhealthy", "starting"},
            reason=None
            if service.status in {"running", "unhealthy", "starting"}
            else "Service must be running or starting before restart.",
        ),
    ]


def _quality_actions(check: ObservatoryQualityCheck) -> list[ObservatoryAction]:
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
        ObservatoryAction(
            id=f"{check.id}:rerun",
            label="Re-run",
            kind="quality.rerun",
            enabled=executable,
            reason=None if executable else "This quality check has no executable function.",
        ),
    ]


def _operation_actions(operation: ObservatoryOperation) -> list[ObservatoryAction]:
    actions = []
    if operation.target is not None:
        actions.append(
            ObservatoryAction(
                id=f"{operation.id}:open-target",
                label="Open Target",
                kind="operation.open_target",
                enabled=True,
                requires_confirmation=False,
            )
        )
    return actions


def _table_columns_from_metadata(table: ObservatoryTable) -> list[str]:
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


def _table_column_types_from_metadata(table: ObservatoryTable, columns: list[str]) -> list[str]:
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


def _sample_value(table: ObservatoryTable, column: str, row_index: int) -> Any:
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
    table: ObservatoryTable, columns: list[str], limit: int, offset: int
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


def _relation_from_metadata(table: ObservatoryTable) -> str | None:
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


def _discovered_relation(table: ObservatoryTable) -> str | None:
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


def _query_relation_for_table(table: ObservatoryTable) -> str | None:
    return _relation_from_metadata(table) or _discovered_relation(table)


def _select_sql_for_table(table: ObservatoryTable, *, limit: int, offset: int = 0) -> str | None:
    relation = _query_relation_for_table(table)
    if relation is None:
        return None
    sql = f"select * from {relation}"
    if offset > 0:
        sql = f"{sql} offset {max(0, offset)}"
    sql = f"{sql} limit {max(1, min(limit, 500))}"
    return sql


def _count_sql_for_table(table: ObservatoryTable) -> str | None:
    relation = _query_relation_for_table(table)
    if relation is None:
        return None
    return f"select count(*) as row_count from {relation}"


def _preview_from_query_engine(
    table: ObservatoryTable, limit: int, offset: int
) -> ObservatoryTablePreview | None:
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

    return ObservatoryTablePreview(
        table=_compact_table(table),
        columns=columns,
        column_types=column_types,
        rows=rows,
        row_count=row_count,
        limit=effective_limit,
        offset=offset,
        has_more=row_count is not None and offset + len(rows) < row_count,
    )


def _find_table(
    table_id: str, tables: list[ObservatoryTable] | None = None
) -> ObservatoryTable | None:
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


def _load_provider_branches() -> list[ObservatoryBranch]:
    provider = _catalog_branch_provider()
    list_branches = getattr(provider, "list_branches", None)
    if not callable(list_branches):
        return []
    try:
        raw_branches = list_branches()
    except Exception:
        return []

    branches: list[ObservatoryBranch] = []
    for raw_branch in raw_branches or []:
        name = _provider_branch_name(raw_branch)
        if not name or name == "main":
            continue
        branches.append(
            ObservatoryBranch(
                id=name,
                name=name,
                current=False,
                protected=False,
                metadata=_provider_branch_metadata(raw_branch),
            )
        )
    return branches


def _load_branches() -> list[ObservatoryBranch]:
    """Return neutral branch data; core-only fallback is the main branch."""
    branches_by_id = {
        "main": ObservatoryBranch(id="main", name="main", current=True, protected=True),
    }
    for branch in _manifest_records("branches", ObservatoryBranch):
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
                        branch = ObservatoryBranch.model_validate(item)
                    except Exception:
                        continue
                    if branch.id != "main":
                        branches_by_id[branch.id] = branch
    return sorted(branches_by_id.values(), key=lambda item: (not item.current, item.name))


def _write_branches(branches: list[ObservatoryBranch]) -> None:
    stored = [branch for branch in branches if branch.id != "main"]
    _branches_path().write_text(
        json.dumps({"items": [branch.model_dump() for branch in stored]}, indent=2),
        encoding="utf-8",
    )


def _load_extensions() -> list[ObservatoryExtension]:
    try:
        from phlo.plugins.observatory import discover_observatory_extensions
    except Exception:
        return []

    extensions: list[ObservatoryExtension] = []
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
            ObservatoryExtension(
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


def _load_asset_detail(asset_id: str) -> ObservatoryAssetDetail:
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
        *(ObservatoryResourceRef(kind="asset", id=item.id, label=item.name) for item in upstream),
        ObservatoryResourceRef(kind="asset", id=asset.id, label=asset.name),
        *(ObservatoryResourceRef(kind="asset", id=item.id, label=item.name) for item in downstream),
    ]
    columns = _table_columns_from_metadata(tables[0]) if tables else []
    upstream_columns = [
        f"{dependency}.{column}" for dependency in asset.dependencies for column in columns[:3]
    ]
    return ObservatoryAssetDetail(
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


def _asset_layer(asset: ObservatoryAsset) -> str:
    group = (asset.group or asset.id.split(".", maxsplit=1)[0]).lower()
    if group in {"source", "bronze", "silver", "gold", "marts", "publish"}:
        return group
    return "unknown"


def _asset_graph_from_assets(assets: list[ObservatoryAsset]) -> ObservatoryAssetGraph:
    asset_ids = {asset.id for asset in assets}
    downstream_counts: Counter[str] = Counter()
    edges: list[ObservatoryAssetGraphEdge] = []

    for asset in assets:
        for dependency in asset.dependencies:
            if dependency not in asset_ids:
                continue
            edges.append(ObservatoryAssetGraphEdge(source=dependency, target=asset.id))
            downstream_counts[dependency] += 1

    nodes = [
        ObservatoryAssetGraphNode(
            id=asset.id,
            key=[part for part in re.split(r"[./]", asset.id) if part],
            key_path=asset.id,
            label=asset.name or asset.id,
            description=asset.description,
            compute_kind=asset.kinds[0] if asset.kinds else None,
            group_name=asset.group,
            layer=_asset_layer(asset),
            upstream_count=len(
                [dependency for dependency in asset.dependencies if dependency in asset_ids]
            ),
            downstream_count=downstream_counts[asset.id],
        )
        for asset in assets
    ]
    return ObservatoryAssetGraph(nodes=nodes, edges=edges)


def _load_asset_graph() -> ObservatoryAssetGraph:
    return _asset_graph_from_assets(_load_assets())


def _load_asset_neighbors(asset_key: str, direction: str, depth: int) -> ObservatoryAssetGraph:
    graph = _load_asset_graph()
    max_depth = max(1, min(depth, 10))
    wanted = {asset_key}
    frontier = {asset_key}

    for _ in range(max_depth):
        next_frontier: set[str] = set()
        for edge in graph.edges:
            if direction in {"upstream", "both"} and edge.target in frontier:
                next_frontier.add(edge.source)
            if direction in {"downstream", "both"} and edge.source in frontier:
                next_frontier.add(edge.target)
        next_frontier -= wanted
        if not next_frontier:
            break
        wanted.update(next_frontier)
        frontier = next_frontier

    return ObservatoryAssetGraph(
        nodes=[node for node in graph.nodes if node.id in wanted],
        edges=[edge for edge in graph.edges if edge.source in wanted and edge.target in wanted],
    )


def _load_asset_impact(asset_key: str, max_depth: int) -> list[ObservatoryImpactedAsset]:
    graph = _load_asset_graph()
    node_by_id = {node.id: node for node in graph.nodes}
    outgoing: dict[str, list[str]] = {}
    for edge in graph.edges:
        outgoing.setdefault(edge.source, []).append(edge.target)

    impacted: list[ObservatoryImpactedAsset] = []
    seen = {asset_key}
    queue: list[tuple[str, int]] = [(asset_key, 0)]
    depth_limit = max(1, min(max_depth, 25))

    while queue:
        current, depth = queue.pop(0)
        if depth >= depth_limit:
            continue
        for target in outgoing.get(current, []):
            if target in seen:
                continue
            seen.add(target)
            node = node_by_id.get(target)
            if node is not None:
                impacted.append(
                    ObservatoryImpactedAsset(
                        key_path=node.key_path,
                        label=node.label,
                        layer=node.layer,
                        depth=depth + 1,
                    )
                )
            queue.append((target, depth + 1))

    return impacted


def _load_service_detail(service_id: str) -> ObservatoryServiceDetail:
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
    return ObservatoryServiceDetail(
        service=service,
        dependencies=dependencies,
        dependents=dependents,
        actions=_service_actions(service),
        logs=logs,
        ports=_service_ports_from_definition(raw_service),
        config=_service_config_from_definition(raw_service),
    )


def _load_operation_detail(operation_id: str) -> ObservatoryOperationDetail:
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
    return ObservatoryOperationDetail(
        operation=operation,
        related=related,
        logs=logs,
        actions=_operation_actions(operation),
    )


def _load_table_preview(table_id: str, limit: int, offset: int) -> ObservatoryTablePreview:
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
    available_preview_count = (
        len([row for row in preview_rows if isinstance(row, Mapping)])
        if isinstance(preview_rows, list)
        else None
    )
    columns = _table_columns_from_metadata(table)
    column_types = _table_column_types_from_metadata(table, columns)
    rows = _table_rows(table, columns, limit, max(0, offset))
    if not columns and rows:
        columns = [str(key) for key in rows[0]]
        column_types = ["unknown"] * len(columns)
    return ObservatoryTablePreview(
        table=_compact_table(table),
        columns=columns,
        column_types=column_types,
        rows=rows,
        row_count=row_count,
        limit=limit,
        offset=offset,
        has_more=(
            max(0, offset) + len(rows)
            < (available_preview_count if available_preview_count is not None else row_count or 0)
        ),
    )


def _run_read_query(request: ObservatoryQueryRequest) -> ObservatoryQueryResult:
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
    return ObservatoryQueryResult(
        columns=preview.columns,
        rows=preview.rows,
        row_count=preview.row_count,
        effective_sql=effective_sql,
        limit=limit,
        offset=preview.offset,
        warnings=warnings,
    )


async def _contributing_rows_query(
    request: ObservatoryContributingRowsQueryRequest,
) -> ObservatoryContributingRowsQueryResponse | dict[str, str]:
    from phlo_api.observatory_api.contributing import (
        ContributingRowsQueryRequest,
        get_contributing_rows_query,
    )

    result = await get_contributing_rows_query(
        ContributingRowsQueryRequest.model_validate(request.model_dump())
    )
    if isinstance(result, Mapping):
        error = result.get("error")
        if isinstance(error, str):
            return {"error": error}
    return ObservatoryContributingRowsQueryResponse(
        query=result.query,
        upstream=ObservatoryUpstreamTableRef(
            schema_name=result.upstream.schema_name,
            table=result.upstream.table,
        ),
    )


async def _contributing_rows_page(
    request: ObservatoryContributingRowsPageRequest,
) -> ObservatoryContributingRowsPageResponse | dict[str, str]:
    from phlo_api.observatory_api.contributing import (
        ContributingRowsPageRequest,
        get_contributing_rows_page,
    )

    result = await get_contributing_rows_page(
        ContributingRowsPageRequest.model_validate(request.model_dump())
    )
    if isinstance(result, Mapping):
        error = result.get("error")
        if isinstance(error, str):
            return {"error": error}
    return ObservatoryContributingRowsPageResponse(
        mode=result.mode,
        page=result.page,
        page_size=result.page_size,
        has_more=result.has_more,
        query=result.query,
        upstream=ObservatoryUpstreamTableRef(
            schema_name=result.upstream.schema_name,
            table=result.upstream.table,
        ),
        columns=result.columns,
        column_types=result.column_types,
        rows=result.rows,
    )


def _try_run_query_engine(
    sql: str,
    *,
    branch: str | None,
    limit: int,
    offset: int,
) -> ObservatoryQueryResult | None:
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
    return ObservatoryQueryResult(
        columns=[str(column) for column in columns],
        rows=[dict(row) for row in clean_rows[:limit]],
        row_count=len(clean_rows),
        effective_sql=_coerce_str(result.get("effective_query"), sql),
        limit=limit,
        offset=offset,
        warnings=[],
    )


def _load_row_journey(table_id: str, row_id: str) -> ObservatoryRowJourney:
    preview = _load_table_preview(table_id, limit=1, offset=max(0, _row_offset(row_id)))
    table = preview.table
    row = preview.rows[0] if preview.rows else {}
    asset = next((item for item in _load_assets() if item.id == table.asset_id), None)
    upstream: list[ObservatoryResourceRef] = []
    downstream: list[ObservatoryResourceRef] = []
    stages: list[ObservatoryResourceRef] = []
    if asset is not None:
        stages.append(ObservatoryResourceRef(kind="asset", id=asset.id, label=asset.name))
        upstream = [
            ObservatoryResourceRef(kind="asset", id=item.id, label=item.name)
            for item in _load_assets()
            if item.id in set(asset.dependencies)
        ]
        downstream = [
            ObservatoryResourceRef(kind="asset", id=item.id, label=item.name)
            for item in _load_assets()
            if asset.id in item.dependencies
        ]
    return ObservatoryRowJourney(
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


def _load_saved_queries() -> list[ObservatorySavedQuery]:
    return _load_saved_queries_impl(_project_root())


def _dedupe_saved_queries(queries: list[ObservatorySavedQuery]) -> list[ObservatorySavedQuery]:
    return _dedupe_saved_queries_impl(queries)


def _write_saved_queries(queries: list[ObservatorySavedQuery]) -> None:
    _write_saved_queries_impl(_project_root(), queries)


def _save_query(request: ObservatorySavedQueryRequest) -> ObservatorySavedQuery:
    return _save_query_impl(_project_root(), request)


def _validate_saved_query_sql(sql: str) -> str | None:
    return _validate_saved_query_sql_impl(sql)


def _load_stage_diff(source_table_id: str, target_table_id: str) -> ObservatoryStageDiff:
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

    return ObservatoryStageDiff(
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


def _load_quality_detail(check_id: str) -> ObservatoryQualityDetail:
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
    return ObservatoryQualityDetail(
        check=check,
        asset=asset,
        history=operations,
        logs=logs,
        actions=_quality_actions(check),
    )


def _load_log_facets(logs: list[ObservatoryLogEvent]) -> ObservatoryLogFacets:
    resources: dict[str, ObservatoryResourceRef] = {}
    for event in logs:
        if event.resource is not None:
            resources[f"{event.resource.kind}:{event.resource.id}"] = event.resource
    return ObservatoryLogFacets(
        sources=sorted({event.source or "platform" for event in logs}),
        levels=sorted({event.level for event in logs}),
        resources=sorted(resources.values(), key=lambda item: (item.kind, item.label)),
    )


def _load_branch_detail(branch_name: str) -> ObservatoryBranchDetail:
    branches = _load_branches()
    branch = next(
        (item for item in branches if item.id == branch_name or item.name == branch_name), None
    )
    if branch is None:
        raise _not_found("branch", branch_name)

    tables = [table for table in _load_tables() if table.branch in {None, "", branch.name}]
    if not tables:
        tables = _tables_from_branch_operations(branch.name)
    contents = [
        ObservatoryResourceRef(kind="table", id=table.id, label=table.name) for table in tables
    ]
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

    return ObservatoryBranchDetail(
        branch=branch,
        contents=contents,
        commits=commits,
        compare=compare,
        tables=tables,
    )


def _tables_from_branch_operations(branch_name: str) -> list[ObservatoryTable]:
    tables: dict[str, ObservatoryTable] = {}
    for operation in _load_operations():
        if operation.target is None or operation.target.kind != "branch":
            continue
        if operation.target.id != branch_name:
            continue
        for table in _tables_from_metadata(operation.metadata, branch_name):
            tables.setdefault(table.id, table)
    return sorted(tables.values(), key=lambda item: item.id)


def _tables_from_metadata(metadata: Mapping[str, Any], branch_name: str) -> list[ObservatoryTable]:
    raw_tables = metadata.get("tables") or metadata.get("changed_tables")
    if not isinstance(raw_tables, list):
        return []

    tables: list[ObservatoryTable] = []
    for item in raw_tables:
        if isinstance(item, str):
            table_id = item
            namespace, _, name = item.rpartition(".")
            tables.append(
                ObservatoryTable(
                    id=table_id,
                    name=name or item,
                    namespace=namespace or None,
                    branch=branch_name,
                    metadata={"source": "wap_report"},
                )
            )
        elif isinstance(item, Mapping):
            name = _coerce_str(item.get("name") or item.get("id"), "")
            if not name:
                continue
            namespace = _coerce_str(item.get("namespace"), "") or None
            table_id = _coerce_str(item.get("id"), "") or ".".join(
                part for part in (namespace, name) if part
            )
            tables.append(
                ObservatoryTable(
                    id=table_id,
                    name=name,
                    namespace=namespace,
                    asset_id=_coerce_str(item.get("asset_id"), "") or None,
                    format=_coerce_str(item.get("format"), "") or None,
                    branch=branch_name,
                    schema_name=_coerce_str(item.get("schema_name"), "") or namespace,
                    metadata={
                        **(
                            _safe_metadata(dict(item["metadata"]))
                            if isinstance(item.get("metadata"), Mapping)
                            else {}
                        ),
                        **_safe_metadata(
                            {key: value for key, value in item.items() if key != "metadata"}
                        ),
                        "source": "wap_report",
                    },
                )
            )
    return tables


def _search_results(query: str) -> list[ObservatorySearchResult]:
    return _search_results_impl(
        query=query,
        services=_load_services(),
        assets=_load_assets(),
        tables=_load_tables_without_catalog(),
        operations=_load_operations(),
        quality=_load_quality(),
        extensions=_load_extensions(),
    )


def _load_extension_detail(extension_id: str) -> ObservatoryExtensionDetail:
    extensions = _load_extensions()
    extension = next(
        (item for item in extensions if item.id == extension_id or item.name == extension_id),
        None,
    )
    if extension is None:
        raise _not_found("extension", extension_id)

    capabilities = [
        ObservatoryResourceRef(kind="route", id=route, label=route) for route in extension.routes
    ]
    return ObservatoryExtensionDetail(
        extension=extension,
        routes=extension.routes,
        nav=extension.nav,
        capabilities=capabilities,
    )


def _providers_for_path(extensions: Sequence[ObservatoryExtension], path: str) -> list[str]:
    providers: list[str] = []
    for extension in extensions:
        paths = {*extension.nav, *extension.routes}
        if path in paths or any(item == path or item.startswith(f"{path}/") for item in paths):
            providers.append(extension.id)
    return sorted(providers)


def _providers_matching(extensions: Sequence[ObservatoryExtension], *needles: str) -> list[str]:
    matches: list[str] = []
    lowered_needles = tuple(needle.lower() for needle in needles)
    for extension in extensions:
        haystack = " ".join(
            [extension.id, extension.name, *extension.nav, *extension.routes]
        ).lower()
        if any(needle in haystack for needle in lowered_needles):
            matches.append(extension.id)
    return sorted(set(matches))


def _load_capabilities() -> ObservatoryCapabilities:
    inventory = build_capability_inventory(_load_capability_registry())
    _add_orchestrator_plugin_providers(inventory)
    services = _load_services()
    _filter_capabilities_to_project_services(inventory, services)
    _add_runtime_capability_providers(inventory, services)
    pages = _pages_from_inventory(inventory)
    pages = _apply_manifest_capability_overrides(pages)
    features = {page.id: page.available for page in pages}
    providers = {page.id: page.providers for page in pages if page.providers}

    return ObservatoryCapabilities(
        pages=pages,
        features=features,
        providers=providers,
    )


def _load_surface_capabilities() -> ObservatoryCapabilities:
    """Build route-gating capabilities without dynamic package discovery."""
    inventory = build_capability_inventory(None)
    services = _load_services()
    _filter_capabilities_to_project_services(inventory, services)
    _add_runtime_capability_providers(inventory, services)
    pages = _apply_manifest_capability_overrides(_pages_from_inventory(inventory))
    features = {page.id: page.available for page in pages}
    providers = {page.id: page.providers for page in pages if page.providers}
    return ObservatoryCapabilities(pages=pages, features=features, providers=providers)


def _apply_manifest_capability_overrides(
    pages: list[ObservatoryCapabilityPage],
) -> list[ObservatoryCapabilityPage]:
    manifest = _load_lakehouse_manifest()
    if not manifest:
        return pages

    route_providers: dict[str, str] = {}
    if manifest.get("tables"):
        route_providers["data"] = "lakehouse-manifest"
        route_providers["assets"] = "lakehouse-manifest"
    if manifest.get("assets"):
        route_providers["assets"] = "lakehouse-manifest"
    if _load_data_products():
        route_providers["catalog"] = "lakehouse-manifest"
        route_providers["governance"] = "lakehouse-manifest"
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

    overridden: list[ObservatoryCapabilityPage] = []
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


def _add_orchestrator_plugin_providers(inventory: ObservatoryCapabilityInventory) -> None:
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
            ObservatoryCapabilityProvider(
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
    inventory: ObservatoryCapabilityInventory,
    services: Sequence[ObservatoryService],
) -> None:
    """Keep service-backed providers aligned with the current project stack."""
    project_service_ids = {
        service.id
        for service in services
        if service.in_stack or service.definition_state == "configured"
    }

    for capability_type, providers in list(inventory.providers.items()):
        filtered: list[ObservatoryCapabilityProvider] = []
        for provider in providers:
            dependencies = _provider_service_dependencies(capability_type, provider)
            if not dependencies or any(
                service_id in project_service_ids for service_id in dependencies
            ):
                filtered.append(provider)
        inventory.providers[capability_type] = filtered


def _provider_service_dependencies(
    capability_type: str,
    provider: ObservatoryCapabilityProvider,
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
    inventory: ObservatoryCapabilityInventory, services: Sequence[ObservatoryService]
) -> None:
    """Expose running service-backed capabilities even when provider packages are absent."""
    runtime_services = [service for service in services if service.in_stack]
    for service in runtime_services:
        for capability_type in _RUNTIME_SERVICE_CAPABILITIES.get(service.id, ()):
            providers = inventory.providers.setdefault(capability_type, [])
            if any(provider.name == service.id for provider in providers):
                continue
            providers.append(
                ObservatoryCapabilityProvider(
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


def _pages_from_inventory(
    inventory: ObservatoryCapabilityInventory,
) -> list[ObservatoryCapabilityPage]:
    """Derive Observatory page availability from capability requirements."""
    pages: list[ObservatoryCapabilityPage] = []
    for requirement in inventory.requirements:
        required_all_available = all(
            inventory.providers.get(capability_type) for capability_type in requirement.required_all
        )
        required_any_available = not requirement.required_any or any(
            inventory.providers.get(capability_type) for capability_type in requirement.required_any
        )
        available = required_all_available and required_any_available
        pages.append(
            ObservatoryCapabilityPage(
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
    inventory: ObservatoryCapabilityInventory,
    requirement: ObservatoryRouteRequirement,
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
) -> list[ObservatorySurfaceItem]:
    """Return provider-backed surface summaries from the capability inventory."""
    inventory = build_capability_inventory(_load_capability_registry())
    items: list[ObservatorySurfaceItem] = []
    seen: set[tuple[str, str]] = set()
    for capability_type in capability_types:
        for provider in inventory.providers.get(capability_type, []):
            key = (capability_type, provider.name)
            if key in seen:
                continue
            seen.add(key)
            items.append(
                ObservatorySurfaceItem(
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
) -> list[ObservatorySurfaceItem]:
    items = loader()
    if items:
        return items
    return _surface_items_from_inventory(*capability_types, kind=kind)


def _load_settings() -> ObservatorySettings:
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
    return ObservatorySettings(
        defaults=defaults,
        features=capabilities.features,
        storage={"settings": "core"},
        metadata={
            "providers": capabilities.providers,
        },
    )


def _execute_action(request: ObservatoryActionRequest) -> ObservatoryActionResult:
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
        return ObservatoryActionResult(
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
        return ObservatoryActionResult(
            action=action,
            status="failed",
            message=message,
            operation=ObservatoryOperation(
                id=request.action_id,
                name=action.label,
                kind=action.kind,
                status="failed",
                health=ObservatoryHealth(state="error", message=message),
                target=ObservatoryResourceRef(kind="service", id=service.id, label=service.name),
            ),
        )

    succeeded = result.returncode == 0
    message = (result.stdout or result.stderr or "").strip() or (
        f"{action.label} requested" if succeeded else f"{action.label} failed"
    )
    return ObservatoryActionResult(
        action=action,
        status="succeeded" if succeeded else "failed",
        message=message[-500:],
        operation=ObservatoryOperation(
            id=request.action_id,
            name=action.label,
            kind=action.kind,
            status="succeeded" if succeeded else "failed",
            health=ObservatoryHealth(state="ok" if succeeded else "error", message=message[-200:]),
            target=ObservatoryResourceRef(kind="service", id=service.id, label=service.name),
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


def _install_python_package(
    request: ObservatoryPackageInstallRequest,
) -> ObservatoryPackageInstallResult:
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
        return ObservatoryPackageInstallResult(
            package_name=package_name,
            package_spec=package_spec,
            status="failed",
            message=f"Install failed: {exc}",
            services=[registry_name],
        )
    if not succeeded:
        return ObservatoryPackageInstallResult(
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
    return ObservatoryPackageInstallResult(
        package_name=package_name,
        package_spec=package_spec,
        status="succeeded",
        message=(
            f"Installed {package_name}. Regenerate the Phlo service stack before starting it."
        ),
        services=installed_services or [registry_name],
    )


def _execute_branch_action(request: ObservatoryActionRequest) -> ObservatoryActionResult:
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
    action = ObservatoryAction(
        id=request.action_id,
        label=action_name.title(),
        kind=f"branch.{action_name}",
        enabled=branches_available,
        requires_confirmation=True,
        reason=None if branches_available else branch_unavailable_reason,
    )
    if not action.enabled:
        return ObservatoryActionResult(
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
                            ObservatoryBranch(
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

    return ObservatoryActionResult(
        action=action,
        status=status,  # type: ignore[arg-type]
        message=message,
        operation=ObservatoryOperation(
            id=request.action_id,
            name=action.label,
            kind=action.kind,
            status=status,  # type: ignore[arg-type]
            health=ObservatoryHealth(state=health_state, message=message),  # type: ignore[arg-type]
            target=ObservatoryResourceRef(kind="branch", id=branch_name, label=branch_name),
        ),
    )


@router.get("/overview", response_model=ObservatoryOverview)
def get_observatory_overview() -> ObservatoryOverview:
    """Get the provider-neutral Observatory overview."""
    return _cached_read_model(
        "overview",
        _FAST_READ_MODEL_TTL_SECONDS,
        lambda: ObservatoryOverview(
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


@router.get("/capabilities", response_model=ObservatoryCapabilities)
def get_observatory_capabilities() -> JSONResponse:
    """Get the provider-neutral Observatory surface capabilities."""
    return JSONResponse(content=_load_capabilities().model_dump(mode="json"))


@router.get("/surface-capabilities")
def get_observatory_surface_capabilities() -> JSONResponse:
    """Get Observatory surface capabilities without FastAPI model wrapping."""
    return JSONResponse(content=_load_surface_capabilities().model_dump(mode="json"))


@router.get("/capability-inventory", response_model=ObservatoryCapabilityInventory)
def get_observatory_capability_inventory() -> ObservatoryCapabilityInventory:
    """Get the full provider-neutral capability inventory."""
    return _cached_read_model(
        "capability-inventory",
        _EXPENSIVE_READ_MODEL_TTL_SECONDS,
        lambda: build_capability_inventory(_load_capability_registry()),
    )


@router.get("/services", response_model=ObservatoryServiceList)
def get_observatory_services() -> ObservatoryServiceList:
    """List provider-neutral Observatory services."""
    return _cached_read_model(
        "services",
        _FAST_READ_MODEL_TTL_SECONDS,
        lambda: ObservatoryServiceList(items=_load_services()),
    )


@router.get("/services/{service_id:path}", response_model=ObservatoryServiceDetail)
def get_observatory_service_detail(service_id: str) -> ObservatoryServiceDetail:
    """Get provider-neutral Observatory service detail."""
    return _load_service_detail(service_id)


@router.get("/operations", response_model=ObservatoryOperationList)
def get_observatory_operations(
    status: str | None = None,
    kind: str | None = None,
    q: str | None = None,
    limit: int | None = Query(default=None, ge=1, le=200),
) -> ObservatoryOperationList:
    """List provider-neutral Observatory operations."""
    result = _cached_read_model(
        "operations",
        _FAST_READ_MODEL_TTL_SECONDS,
        lambda: ObservatoryOperationList(items=_load_operations()),
    )
    return ObservatoryOperationList(
        items=_filter_operations(
            result.items,
            status=status,
            kind=kind,
            q=q,
            limit=limit,
        )
    )


@router.get("/operations/{operation_id:path}/agent-context")
def get_observatory_operation_agent_context(operation_id: str) -> dict[str, object]:
    """Get stable observability context for agents investigating an operation."""
    detail = _load_operation_detail(operation_id)
    context = build_operation_observability_context(detail.operation)
    context["related"] = [item.model_dump(mode="json") for item in detail.related]
    context["logs"] = [item.model_dump(mode="json") for item in detail.logs]
    context["actions"] = [item.model_dump(mode="json") for item in detail.actions]
    return context


@router.get("/operations/{operation_id:path}", response_model=ObservatoryOperationDetail)
def get_observatory_operation_detail(operation_id: str) -> ObservatoryOperationDetail:
    """Get provider-neutral Observatory operation detail."""
    return _load_operation_detail(operation_id)


@router.get("/runs", response_model=ObservatoryRunList, response_model_exclude_none=True)
def get_observatory_runs(
    limit: int = 100, cursor: str | None = None, q: str | None = None
) -> ObservatoryRunList:
    """List provider-neutral orchestrator runs."""
    result = _cached_read_model(
        "runs",
        _FAST_READ_MODEL_TTL_SECONDS,
        lambda: ObservatoryRunList(items=_load_runs()),
    )
    items = result.items
    if q:
        items = [item for item in items if q.lower() in item.model_dump_json().lower()]
    page, next_cursor = paginate_items(items, limit=limit, cursor=cursor)
    return ObservatoryRunList(items=page, next_cursor=next_cursor)


@router.get("/runs/{run_id:path}/status")
async def get_observatory_run_status(run_id: str) -> Any:
    """Get provider-neutral run status from the active orchestrator provider."""
    provider = resolve_orchestrator_operations()
    return await provider.get_run_status(run_id)


@router.post("/runs/{run_id:path}/retry")
async def post_observatory_run_retry(
    run_id: str, request: ObservatoryRetryRunRequest, http_request: Request
) -> Any:
    """Validate or request retry for a failed run through the active orchestrator provider."""
    auth = require_scope(http_request, "lakehouse:operate")
    enforce_rate_limit(auth["subject"], "retry_failed_run")
    provider = resolve_orchestrator_operations()

    async def execute() -> dict[str, Any]:
        result = await provider.retry_run(run_id, request.model_dump())
        return _jsonable_result(result)

    payload = await replay_or_execute_async(
        idempotency_key=request.idempotency_key,
        operation="retry_failed_run",
        target=run_id,
        execute=execute,
    )
    audit_operation(
        operation="retry_failed_run",
        target=run_id,
        dry_run=request.dry_run,
        auth=auth,
        payload=request.model_dump(mode="json"),
        result=payload,
    )
    return payload


@router.post("/runs/{run_id:path}/cancel")
async def post_observatory_run_cancel(
    run_id: str, request: ObservatoryCancelRunRequest, http_request: Request
) -> Any:
    """Request cancellation for a run through the active orchestrator provider."""
    auth = require_scope(http_request, "lakehouse:operate")
    enforce_rate_limit(auth["subject"], "cancel_run")
    provider = resolve_orchestrator_operations()

    async def execute() -> dict[str, Any]:
        result = await provider.cancel_run(run_id, request.model_dump())
        return _jsonable_result(result)

    payload = await replay_or_execute_async(
        idempotency_key=request.idempotency_key,
        operation="cancel_run",
        target=run_id,
        execute=execute,
    )
    audit_operation(
        operation="cancel_run",
        target=run_id,
        dry_run=False,
        auth=auth,
        payload=request.model_dump(mode="json"),
        result=payload,
    )
    return payload


@router.get("/storage", response_model=ObservatorySurfaceList)
def get_observatory_storage() -> ObservatorySurfaceList:
    """List provider-neutral storage surfaces."""
    return ObservatorySurfaceList(
        items=_surface_items_from_inventory(
            "table_store",
            "object_store",
            kind="storage",
        )
    )


@router.get("/observability", response_model=ObservatorySurfaceList)
def get_observatory_observability() -> ObservatorySurfaceList:
    """List provider-neutral observability surfaces."""
    return ObservatorySurfaceList(
        items=_surface_items_from_inventory(
            "observability_backend",
            "alert_sink",
            kind="observability",
        )
    )


@router.get("/governance", response_model=ObservatoryGovernanceMatrix)
def get_observatory_governance() -> ObservatoryGovernanceMatrix:
    """Get the Data Product governance control matrix."""
    return _load_governance_matrix()


@router.get("/catalog", response_model=ObservatorySurfaceList)
def get_observatory_catalog() -> ObservatorySurfaceList:
    """List provider-neutral catalog surfaces."""
    return ObservatorySurfaceList(
        items=_surface_items_from_inventory(
            "metadata_catalog",
            "catalog_scanner",
            "catalog",
            kind="catalog",
        )
    )


@router.get("/apis", response_model=ObservatorySurfaceList)
def get_observatory_apis() -> ObservatorySurfaceList:
    """List provider-neutral API surfaces."""
    return ObservatorySurfaceList(
        items=_surface_items_from_inventory(
            "api_backend",
            kind="api",
        )
    )


@router.get("/bi", response_model=ObservatorySurfaceList)
def get_observatory_bi() -> ObservatorySurfaceList:
    """List provider-neutral BI surfaces."""
    return ObservatorySurfaceList(
        items=_surface_items_from_inventory(
            "publish_target",
            "query_engine",
            kind="bi",
        )
    )


@router.get("/assets", response_model=ObservatoryAssetList, response_model_exclude_none=True)
def get_observatory_assets(limit: int = 100, cursor: str | None = None) -> ObservatoryAssetList:
    """List provider-neutral Observatory assets."""
    result = _cached_read_model(
        "assets",
        _EXPENSIVE_READ_MODEL_TTL_SECONDS,
        lambda: ObservatoryAssetList(items=_load_assets()),
    )
    page, next_cursor = paginate_items(result.items, limit=limit, cursor=cursor)
    return ObservatoryAssetList(items=page, next_cursor=next_cursor)


@router.get(
    "/data-products",
    response_model=ObservatoryDataProductList,
    response_model_exclude_none=True,
)
def get_observatory_data_products(
    limit: int = 100, cursor: str | None = None
) -> ObservatoryDataProductList:
    """List provider-neutral Observatory Data Products."""
    result = _cached_read_model(
        "data-products",
        _EXPENSIVE_READ_MODEL_TTL_SECONDS,
        lambda: ObservatoryDataProductList(items=_load_data_products()),
    )
    page, next_cursor = paginate_items(result.items, limit=limit, cursor=cursor)
    return ObservatoryDataProductList(items=page, next_cursor=next_cursor)


@router.get("/data-products/{product_id:path}", response_model=ObservatoryDataProductProfile)
def get_observatory_data_product_profile(product_id: str) -> ObservatoryDataProductProfile:
    """Get the shared provider-neutral Data Product Profile."""
    return _cached_read_model(
        f"data-product-profile:{product_id}",
        _EXPENSIVE_READ_MODEL_TTL_SECONDS,
        lambda: _load_data_product_profile(product_id),
    )


@router.get("/asset-graph", response_model=ObservatoryAssetGraph)
def get_observatory_asset_graph() -> ObservatoryAssetGraph:
    """Get the provider-neutral asset dependency graph."""
    return _cached_read_model(
        "asset-graph",
        _EXPENSIVE_READ_MODEL_TTL_SECONDS,
        _load_asset_graph,
    )


@router.get("/asset-graph/neighbors", response_model=ObservatoryAssetGraph)
def get_observatory_asset_neighbors(
    asset_key: str, direction: str = "both", depth: int = 1
) -> ObservatoryAssetGraph:
    """Get a bounded asset graph around one asset."""
    if direction not in {"upstream", "downstream", "both"}:
        raise HTTPException(
            status_code=400, detail="direction must be upstream, downstream, or both"
        )
    return _load_asset_neighbors(asset_key=asset_key, direction=direction, depth=depth)


@router.get("/asset-graph/impact", response_model=list[ObservatoryImpactedAsset])
def get_observatory_asset_impact(
    asset_key: str, max_depth: int = 99
) -> list[ObservatoryImpactedAsset]:
    """Get downstream assets impacted by one asset."""
    return _load_asset_impact(asset_key=asset_key, max_depth=max_depth)


@router.get("/assets/{asset_id:path}/materializations")
async def get_observatory_asset_materializations(asset_id: str, limit: int = 10) -> Any:
    """Get recent materializations for an asset from the active orchestrator provider."""
    limit = max(1, min(limit, 200))
    provider = resolve_orchestrator_operations()
    return await provider.get_materialization_history(asset_id, limit=limit)


@router.post("/assets/{asset_id:path}/materialize")
async def post_observatory_asset_materialize(
    asset_id: str, request: ObservatoryMaterializeAssetRequest, http_request: Request
) -> Any:
    """Validate or request asset materialization through the active orchestrator provider."""
    auth = require_scope(http_request, "lakehouse:operate")
    enforce_rate_limit(auth["subject"], "materialize_asset")
    provider = resolve_orchestrator_operations()

    async def execute() -> dict[str, Any]:
        result = await provider.materialize_asset(asset_id, request.model_dump())
        return _jsonable_result(result)

    payload = await replay_or_execute_async(
        idempotency_key=request.idempotency_key,
        operation="materialize_asset",
        target=asset_id,
        execute=execute,
    )
    audit_operation(
        operation="materialize_asset",
        target=asset_id,
        dry_run=request.dry_run,
        auth=auth,
        payload=request.model_dump(mode="json"),
        result=payload,
    )
    return payload


@router.post("/assets/{asset_id:path}/backfill")
async def post_observatory_asset_backfill(
    asset_id: str, request: ObservatoryBackfillAssetRequest, http_request: Request
) -> Any:
    """Validate or request asset partition backfill through the active orchestrator provider."""
    auth = require_scope(http_request, "lakehouse:operate")
    enforce_rate_limit(auth["subject"], "backfill_asset")
    provider = resolve_orchestrator_operations()

    async def execute() -> dict[str, Any]:
        result = await provider.backfill_asset(asset_id, request.model_dump())
        return _jsonable_result(result)

    payload = await replay_or_execute_async(
        idempotency_key=request.idempotency_key,
        operation="backfill_asset",
        target=asset_id,
        execute=execute,
    )
    audit_operation(
        operation="backfill_asset",
        target=asset_id,
        dry_run=request.dry_run,
        auth=auth,
        payload=request.model_dump(mode="json"),
        result=payload,
    )
    return payload


@router.get("/assets/{asset_id:path}/partitions")
async def get_observatory_asset_partitions(asset_id: str) -> Any:
    """List partitions for an asset from the active orchestrator provider."""
    provider = resolve_orchestrator_operations()
    return await provider.list_partitions(asset_id)


@router.get("/assets/{asset_id:path}", response_model=ObservatoryAssetDetail)
def get_observatory_asset_detail(asset_id: str) -> ObservatoryAssetDetail:
    """Get provider-neutral Observatory asset detail."""
    return _load_asset_detail(asset_id)


@router.get("/tables", response_model=ObservatoryTableList)
def get_observatory_tables() -> ObservatoryTableList:
    """List provider-neutral Observatory tables."""
    return _cached_read_model(
        "tables",
        _EXPENSIVE_READ_MODEL_TTL_SECONDS,
        lambda: ObservatoryTableList(items=_compact_tables(_load_tables())),
    )


@router.get("/table-preview/{table_id:path}", response_model=ObservatoryTablePreview)
def get_observatory_table_preview(
    table_id: str, limit: int = 50, offset: int = 0
) -> ObservatoryTablePreview:
    """Get provider-neutral table preview metadata."""
    return _cached_read_model(
        f"table-preview:{table_id}:{limit}:{offset}",
        _EXPENSIVE_READ_MODEL_TTL_SECONDS,
        lambda: _load_table_preview(table_id, limit=limit, offset=offset),
    )


@router.get("/saved-queries", response_model=ObservatorySavedQueryList)
def get_observatory_saved_queries() -> ObservatorySavedQueryList:
    """List saved Observatory queries."""
    return ObservatorySavedQueryList(items=_load_saved_queries())


@router.post("/saved-queries", response_model=ObservatorySavedQuery)
def post_observatory_saved_query(request: ObservatorySavedQueryRequest) -> ObservatorySavedQuery:
    """Persist a saved Observatory query."""
    return _save_query(request)


@router.get("/stage-diff", response_model=ObservatoryStageDiff)
def get_observatory_stage_diff(source_table_id: str, target_table_id: str) -> ObservatoryStageDiff:
    """Get provider-neutral stage diff context."""
    return _load_stage_diff(source_table_id, target_table_id)


@router.post("/schemas/diff")
def post_observatory_schema_diff(request: ObservatorySchemaDiffRequest) -> dict[str, Any]:
    """Return a stable schema-diff envelope for one asset."""
    detail = _load_asset_detail(request.asset_key)
    columns = _table_columns_from_metadata(detail.tables[0]) if detail.tables else []
    return {
        "asset_key": request.asset_key,
        "from_run": request.from_run,
        "to_run": request.to_run,
        "changes": [],
        "current_columns": columns,
        "snapshot_available": False,
        "message": "No comparable run schema snapshots were found for this asset.",
    }


@router.post("/query", response_model=ObservatoryQueryResult)
def post_observatory_query(request: ObservatoryQueryRequest) -> ObservatoryQueryResult:
    """Run a provider-neutral read-only table query."""
    return _run_read_query(request)


@router.get("/row-journey/{table_id:path}/{row_id:path}", response_model=ObservatoryRowJourney)
def get_observatory_row_journey(table_id: str, row_id: str) -> ObservatoryRowJourney:
    """Get provider-neutral row journey context."""
    return _load_row_journey(table_id, row_id)


@router.post(
    "/contributing-rows/query",
    response_model=ObservatoryContributingRowsQueryResponse | dict[str, str],
)
async def post_observatory_contributing_rows_query(
    request: ObservatoryContributingRowsQueryRequest,
) -> ObservatoryContributingRowsQueryResponse | dict[str, str]:
    """Build a query for rows that contributed to a selected downstream row."""
    return await _contributing_rows_query(request)


@router.post(
    "/contributing-rows/page",
    response_model=ObservatoryContributingRowsPageResponse | dict[str, str],
)
async def post_observatory_contributing_rows_page(
    request: ObservatoryContributingRowsPageRequest,
) -> ObservatoryContributingRowsPageResponse | dict[str, str]:
    """Return a page of rows that contributed to a selected downstream row."""
    return await _contributing_rows_page(request)


@router.get("/quality", response_model=ObservatoryQualityList)
def get_observatory_quality() -> ObservatoryQualityList:
    """List provider-neutral Observatory quality checks."""
    return _cached_read_model(
        "quality",
        _EXPENSIVE_READ_MODEL_TTL_SECONDS,
        lambda: ObservatoryQualityList(items=_load_quality()),
    )


@router.get("/quality/{check_id:path}", response_model=ObservatoryQualityDetail)
def get_observatory_quality_detail(check_id: str) -> ObservatoryQualityDetail:
    """Get provider-neutral Observatory quality detail."""
    return _load_quality_detail(check_id)


@router.get("/logs", response_model=ObservatoryLogList)
def get_observatory_logs() -> ObservatoryLogList:
    """List provider-neutral Observatory log events."""
    return _cached_read_model(
        "logs", _FAST_READ_MODEL_TTL_SECONDS, lambda: ObservatoryLogList(items=_load_logs())
    )


@router.get("/logs/facets", response_model=ObservatoryLogFacets)
def get_observatory_log_facets() -> ObservatoryLogFacets:
    """Get provider-neutral Observatory log facets."""
    return _cached_read_model(
        "log-facets",
        _EXPENSIVE_READ_MODEL_TTL_SECONDS,
        lambda: _load_log_facets(_load_logs()),
    )


@router.get("/branches", response_model=ObservatoryBranchList)
def get_observatory_branches() -> ObservatoryBranchList:
    """List provider-neutral Observatory branches."""
    return _cached_read_model(
        "branches",
        _EXPENSIVE_READ_MODEL_TTL_SECONDS,
        lambda: ObservatoryBranchList(items=_load_branches()),
    )


@router.post("/branches/actions", response_model=ObservatoryActionResult)
def post_observatory_branch_action(request: ObservatoryActionRequest) -> ObservatoryActionResult:
    """Execute a guarded branch workflow action."""
    result = _execute_branch_action(request)
    recorded = record_action_result(_project_root(), result)
    _clear_read_model_cache()
    return recorded


@router.get("/branches/{branch_name:path}", response_model=ObservatoryBranchDetail)
def get_observatory_branch_detail(branch_name: str) -> ObservatoryBranchDetail:
    """Get provider-neutral Observatory branch detail."""
    return _load_branch_detail(branch_name)


@router.get("/extensions", response_model=ObservatoryExtensionList)
def get_observatory_extensions() -> ObservatoryExtensionList:
    """List provider-neutral Observatory extensions."""
    return _cached_read_model(
        "extensions",
        _EXPENSIVE_READ_MODEL_TTL_SECONDS,
        lambda: ObservatoryExtensionList(items=_load_extensions()),
    )


@router.get("/extension-manifests")
def get_observatory_extension_manifests() -> dict[str, Any]:
    """List extension manifests used by the browser extension loader."""
    from phlo_api.observatory_api.extensions import list_extensions

    return list_extensions()


@router.get("/extensions/{name}/assets/{asset_path:path}")
def get_observatory_extension_asset(
    name: str, asset_path: str, background_tasks: BackgroundTasks
) -> Any:
    """Serve an extension asset from the canonical Observatory API."""
    from phlo_api.observatory_api.extensions import get_extension_asset

    return get_extension_asset(name, asset_path, background_tasks)


@router.get("/extensions/{name}/settings")
async def get_observatory_extension_settings(name: str) -> Any:
    """Fetch settings for an extension from the canonical Observatory API."""
    from phlo_api.observatory_api.extension_settings import get_extension_settings

    return await get_extension_settings(name)


@router.put("/extensions/{name}/settings")
async def put_observatory_extension_settings(name: str, payload: Any = Body(...)) -> Any:
    """Persist settings for an extension from the canonical Observatory API."""
    from phlo_api.observatory_api.extension_settings import (
        ExtensionSettingsPayload,
        put_extension_settings,
    )

    try:
        settings_payload = ExtensionSettingsPayload.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    return await put_extension_settings(name, settings_payload)


@router.get("/extensions/{extension_id:path}", response_model=ObservatoryExtensionDetail)
def get_observatory_extension_detail(extension_id: str) -> ObservatoryExtensionDetail:
    """Get provider-neutral Observatory extension detail."""
    return _load_extension_detail(extension_id)


@router.get("/preferences")
async def get_observatory_preferences(request: Request) -> Any:
    """Fetch persisted browser preferences from the canonical Observatory API."""
    from phlo_api.observatory_api.settings import get_observatory_settings

    return await get_observatory_settings(request)


@router.put("/preferences")
async def put_observatory_preferences(request: Request, payload: Any) -> Any:
    """Persist browser preferences from the canonical Observatory API."""
    from phlo_api.observatory_api.settings import (
        ObservatorySettingsPayload,
        put_observatory_settings,
    )

    return await put_observatory_settings(
        request,
        ObservatorySettingsPayload.model_validate(payload),
    )


@router.get("/settings", response_model=ObservatorySettings)
def get_observatory_settings() -> ObservatorySettings:
    """Get provider-neutral Observatory settings."""
    return _cached_read_model("settings", _EXPENSIVE_READ_MODEL_TTL_SECONDS, _load_settings)


@router.get("/workflow-wizard")
def get_observatory_workflow_wizard() -> dict[str, Any]:
    """Return provider-neutral workflow wizard contributions."""

    return build_workflow_wizard_payload()


@router.post("/workflow-wizard/proposals")
def post_observatory_workflow_wizard_proposal(
    request: ObservatoryWorkflowProposalRequest,
) -> dict[str, Any]:
    """Build a side-effect-free workflow proposal."""

    return build_workflow_proposal(_project_root(), request)


@router.post("/workflow-wizard/actions", response_model=ObservatoryWorkflowActionResult)
def post_observatory_workflow_wizard_action(
    request: ObservatoryWorkflowActionRequest,
) -> ObservatoryWorkflowActionResult:
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


@router.get("/search", response_model=ObservatorySearchList, response_model_exclude_none=True)
def get_observatory_search(
    q: str, limit: int = 100, cursor: str | None = None
) -> ObservatorySearchList:
    """Search provider-neutral Observatory resources."""
    page, next_cursor = paginate_items(_search_results(q), limit=limit, cursor=cursor)
    return ObservatorySearchList(items=page, next_cursor=next_cursor)


@router.post("/actions", response_model=ObservatoryActionResult)
def post_observatory_action(request: ObservatoryActionRequest) -> ObservatoryActionResult:
    """Execute a guarded Observatory action."""
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
        else execute_observatory_action(request, registry=_load_capability_registry())
    )
    recorded = record_action_result(_project_root(), result)
    _clear_read_model_cache()
    return recorded


@router.post("/packages/install", response_model=ObservatoryPackageInstallResult)
def post_observatory_package_install(
    request: ObservatoryPackageInstallRequest, http_request: Request
) -> ObservatoryPackageInstallResult:
    """Install a trusted Phlo Python package into the current environment."""
    auth = require_scope(http_request, "admin")
    enforce_rate_limit(auth["subject"], "install_package")
    result = _install_python_package(request)
    audit_operation(
        operation="install_package",
        target=request.package_name,
        dry_run=False,
        auth=auth,
        payload=request.model_dump(mode="json"),
        result=result.model_dump(mode="json"),
    )
    _clear_read_model_cache()
    return result

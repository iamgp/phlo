"""Provider-neutral Observatory v2 workflow wizard helpers."""

from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Any, Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field

from phlo.capabilities import (
    WorkflowApplyAction,
    WorkflowFilePreview,
    WorkflowProposal,
    WorkflowProposalRequest,
    detect_file_conflicts,
    validate_proposal_request,
)

STAGES = ["source", "transform", "quality", "publish"]
WORKFLOW_WIZARD_MODULES = (
    "phlo_dlt.plugin",
    "phlo_sling.plugin",
    "phlo_dbt.plugin",
    "phlo_pandera.plugin",
    "phlo_dagster.plugin",
    "phlo_openmetadata.plugin",
)


class V2WorkflowWizardSelection(BaseModel):
    """User-selected contribution and values for one workflow stage."""

    contribution_id: str
    values: dict[str, Any] = Field(default_factory=dict)


class V2WorkflowGraphNode(BaseModel):
    """Canvas node selected by the workflow builder."""

    id: str
    contribution_id: str
    stage: str
    values: dict[str, Any] = Field(default_factory=dict)


class V2WorkflowGraphEdge(BaseModel):
    """Canvas edge connecting workflow builder nodes."""

    id: str
    source: str
    target: str


class V2WorkflowGraph(BaseModel):
    """Workflow graph authored by Observatory."""

    nodes: list[V2WorkflowGraphNode] = Field(default_factory=list)
    edges: list[V2WorkflowGraphEdge] = Field(default_factory=list)


class V2WorkflowProposalRequest(BaseModel):
    """Request body for workflow wizard proposal generation."""

    workflow_name: str
    domain: str
    graph: V2WorkflowGraph


class V2WorkflowActionRequest(BaseModel):
    """Request body for guarded workflow wizard apply actions."""

    action_id: str
    proposal: dict[str, Any]


class V2WorkflowActionResult(BaseModel):
    """Result for a guarded workflow wizard action."""

    action_id: str
    status: Literal["succeeded", "failed", "skipped"]
    message: str
    files: list[str] = Field(default_factory=list)


def list_workflow_wizard_contributions() -> list[dict[str, Any]]:
    """Return package-provided workflow wizard contributions."""

    contributions: list[dict[str, Any]] = []
    for module_name in WORKFLOW_WIZARD_MODULES:
        try:
            module = importlib.import_module(module_name)
            loader = getattr(module, "get_workflow_wizard_contributions", None)
            if callable(loader):
                contributions.extend(item.to_browser_dict() for item in loader())
        except Exception:
            continue
    return contributions


def build_workflow_wizard_payload() -> dict[str, Any]:
    """Build the workflow wizard discovery payload."""

    return {"version": 1, "stages": STAGES, "contributions": list_workflow_wizard_contributions()}


def build_workflow_proposal(
    project_root: Path,
    request: V2WorkflowProposalRequest,
) -> dict[str, Any]:
    """Build a side-effect-free workflow proposal for the browser."""

    if not request.graph.nodes:
        raise HTTPException(status_code=422, detail={"graph": ["Add at least one workflow node."]})

    contract_request = WorkflowProposalRequest(
        workflow_name=request.workflow_name,
        domain=request.domain,
        selections={
            stage: _selection_payload(selection)
            for stage, selection in _selections_from_graph(request.graph).items()
        },
    )
    errors = validate_proposal_request(contract_request)
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    proposal = _proposal_from_request(contract_request)
    conflicts = detect_file_conflicts(project_root, proposal)
    if conflicts:
        proposal = _with_conflict_action_disabled(proposal, conflicts)
    return proposal.to_browser_dict()


def _selections_from_graph(
    graph: V2WorkflowGraph,
) -> dict[str, V2WorkflowWizardSelection | list[V2WorkflowWizardSelection]]:
    grouped: dict[str, list[V2WorkflowWizardSelection]] = {}
    for node in _topological_nodes(graph):
        grouped.setdefault(node.stage, []).append(
            V2WorkflowWizardSelection(
                contribution_id=node.contribution_id,
                values=node.values,
            )
        )

    selections: dict[str, V2WorkflowWizardSelection | list[V2WorkflowWizardSelection]] = {}
    for stage, stage_nodes in grouped.items():
        selections[stage] = stage_nodes[0] if stage == "source" and stage_nodes else stage_nodes
    return selections


def _topological_nodes(graph: V2WorkflowGraph) -> list[V2WorkflowGraphNode]:
    by_id = {node.id: node for node in graph.nodes}
    indegree = {node.id: 0 for node in graph.nodes}
    outgoing: dict[str, list[str]] = {node.id: [] for node in graph.nodes}
    for edge in graph.edges:
        if edge.source not in by_id or edge.target not in by_id:
            continue
        outgoing[edge.source].append(edge.target)
        indegree[edge.target] += 1

    ready = [node.id for node in graph.nodes if indegree[node.id] == 0]
    ordered: list[V2WorkflowGraphNode] = []
    while ready:
        node_id = ready.pop(0)
        ordered.append(by_id[node_id])
        for target in outgoing[node_id]:
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)

    return ordered if len(ordered) == len(graph.nodes) else graph.nodes


def _selection_payload(
    selection: V2WorkflowWizardSelection | list[V2WorkflowWizardSelection],
) -> dict[str, Any] | list[dict[str, Any]]:
    if isinstance(selection, list):
        return [_selection_payload(item) for item in selection]
    return {
        "contribution_id": selection.contribution_id,
        "values": selection.values,
    }


def apply_workflow_action(
    project_root: Path, request: V2WorkflowActionRequest
) -> V2WorkflowActionResult:
    """Apply a guarded workflow wizard action by writing proposed files."""

    proposal = _proposal_from_payload(request.proposal)
    action = next((item for item in proposal.actions if item.id == request.action_id), None)
    if action is None:
        raise HTTPException(
            status_code=404, detail=f"Workflow action not found: {request.action_id}"
        )

    conflicts = detect_file_conflicts(project_root, proposal)
    if conflicts and action.conflict_policy == "fail-on-conflict":
        raise HTTPException(status_code=409, detail=f"File conflicts: {', '.join(conflicts)}")

    written: list[str] = []
    for preview in proposal.files:
        target = project_root / preview.path
        if target.exists() and action.conflict_policy == "skip-if-exists":
            continue
        if target.exists() and action.conflict_policy == "fail-on-conflict":
            raise HTTPException(status_code=409, detail=f"File conflicts: {preview.path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(preview.content, encoding="utf-8")
        written.append(preview.path)

    return V2WorkflowActionResult(
        action_id=action.id,
        status="succeeded",
        message=f"Created {len(written)} workflow file{'s' if len(written) != 1 else ''}.",
        files=written,
    )


def _proposal_from_request(request: WorkflowProposalRequest) -> WorkflowProposal:
    source = request.selection_for("source")
    assert source is not None
    source_values = source.values
    domain = _slug(str(source_values.get("domain") or request.domain))
    table_name = _slug(
        str(
            source_values.get("table_name")
            or source_values.get("target_table")
            or request.workflow_name
        )
    )
    unique_key = _slug(
        str(source_values.get("unique_key") or source_values.get("primary_key") or "id")
    )
    fields = _coerce_fields(source_values.get("fields"))
    files: list[WorkflowFilePreview] = []
    selected = [source.contribution_id]
    planned_assets: list[str] = []
    planned_tables = [table_name]
    planned_models: list[str] = []

    if source.contribution_id == "sling.replication-source":
        source_name = str(source_values.get("source_name") or "POSTGRES")
        source_stream = str(source_values.get("source_stream") or table_name)
        replication_mode = str(source_values.get("replication_mode") or "incremental")
        update_key = str(source_values.get("update_key") or "")
        cron = str(source_values.get("schedule") or "0 2 * * *")
        planned_assets.append(f"sling_{table_name}")
        files.extend(
            [
                WorkflowFilePreview(
                    path=f"workflows/ingestion/{domain}/{table_name}_sling.py",
                    content=_render_sling_asset(
                        domain,
                        table_name,
                        unique_key,
                        source_name,
                        source_stream,
                        replication_mode,
                        update_key,
                        cron,
                    ),
                ),
                WorkflowFilePreview(
                    path=f"workflows/ingestion/{domain}/{table_name}_sling.yml",
                    content=_render_sling_replication_config(
                        domain,
                        table_name,
                        unique_key,
                        source_name,
                        source_stream,
                        replication_mode,
                        update_key,
                        cron,
                    ),
                ),
            ]
        )
    else:
        api_base_url = str(source_values.get("api_base_url") or "")
        cron = str(source_values.get("cron") or "0 */1 * * *")
        response_path = str(source_values.get("response_path") or "")
        pagination = str(source_values.get("pagination") or "none")
        auth = str(source_values.get("auth") or "none")
        planned_assets.append(f"dlt_{table_name}")
        files.extend(
            [
                WorkflowFilePreview(
                    path=f"workflows/schemas/{domain}.py",
                    content=_render_schema(domain, table_name, unique_key, fields),
                ),
                WorkflowFilePreview(
                    path=f"workflows/ingestion/{domain}/{table_name}.py",
                    content=_render_dlt_asset(
                        domain,
                        table_name,
                        unique_key,
                        api_base_url,
                        cron,
                        response_path,
                        pagination,
                        auth,
                    ),
                ),
                WorkflowFilePreview(
                    path=f"tests/test_{domain}_{table_name}.py",
                    content=_render_ingestion_test(domain, table_name, unique_key),
                ),
            ]
        )

    for transform in request.selections_for("transform"):
        if not transform.contribution_id:
            continue
        selected.append(transform.contribution_id)
        transform_values = transform.values
        if transform.contribution_id == "dbt.transform":
            planned_models.extend(
                _append_dbt_transform_files(
                    files,
                    request.workflow_name,
                    table_name,
                    unique_key,
                    fields,
                    transform_values,
                )
            )
            continue
        if transform.contribution_id == "dbt.initialize-project":
            project_name = _slug(str(transform_values.get("project_name") or request.workflow_name))
            files.append(
                WorkflowFilePreview(
                    path="workflows/transforms/dbt/dbt_project.yml",
                    content=_render_dbt_project(project_name),
                )
            )
        if transform.contribution_id == "dbt.basic-model":
            model_name = _slug(str(transform_values.get("model_name") or f"stg_{table_name}"))
            source_relation = str(transform_values.get("source_relation") or f"raw.{table_name}")
            planned_models.append(model_name)
            files.append(
                WorkflowFilePreview(
                    path=f"workflows/transforms/dbt/models/{model_name}.sql",
                    content=_render_dbt_model(source_relation),
                )
            )
        if transform.contribution_id == "dbt.source-yml":
            source_name = _slug(str(transform_values.get("source_name") or "raw"))
            source_table = _slug(str(transform_values.get("table_name") or table_name))
            files.append(
                WorkflowFilePreview(
                    path=f"workflows/transforms/dbt/models/sources/{source_name}.yml",
                    content=_render_dbt_source_yml(source_name, source_table, fields),
                )
            )
        if transform.contribution_id == "dbt.schema-tests":
            model_name = _slug(str(transform_values.get("model_name") or f"stg_{table_name}"))
            model_key = _slug(str(transform_values.get("unique_key") or unique_key))
            files.append(
                WorkflowFilePreview(
                    path=f"workflows/transforms/dbt/models/{model_name}.yml",
                    content=_render_dbt_schema_tests(model_name, model_key, fields),
                )
            )
        if transform.contribution_id == "dbt.rename-columns":
            model_name = _slug(str(transform_values.get("model_name") or f"renamed_{table_name}"))
            source_relation = str(
                transform_values.get("source_relation") or f"ref('stg_{table_name}')"
            )
            planned_models.append(model_name)
            files.append(
                WorkflowFilePreview(
                    path=f"workflows/transforms/dbt/models/{model_name}.sql",
                    content=_render_dbt_rename_columns(
                        source_relation,
                        _coerce_fields(transform_values.get("renames")),
                    ),
                )
            )
        if transform.contribution_id == "dbt.cast-columns":
            model_name = _slug(str(transform_values.get("model_name") or f"typed_{table_name}"))
            source_relation = str(
                transform_values.get("source_relation") or f"ref('stg_{table_name}')"
            )
            planned_models.append(model_name)
            files.append(
                WorkflowFilePreview(
                    path=f"workflows/transforms/dbt/models/{model_name}.sql",
                    content=_render_dbt_cast_columns(
                        source_relation,
                        _coerce_fields(transform_values.get("casts")),
                    ),
                )
            )
        if transform.contribution_id == "dbt.filter-rows":
            model_name = _slug(str(transform_values.get("model_name") or f"filtered_{table_name}"))
            source_relation = str(
                transform_values.get("source_relation") or f"ref('stg_{table_name}')"
            )
            planned_models.append(model_name)
            files.append(
                WorkflowFilePreview(
                    path=f"workflows/transforms/dbt/models/{model_name}.sql",
                    content=_render_dbt_filter_rows(
                        source_relation,
                        str(transform_values.get("where") or "1 = 1"),
                    ),
                )
            )
        if transform.contribution_id == "dbt.deduplicate":
            model_name = _slug(str(transform_values.get("model_name") or f"deduped_{table_name}"))
            source_relation = str(
                transform_values.get("source_relation") or f"ref('stg_{table_name}')"
            )
            planned_models.append(model_name)
            files.append(
                WorkflowFilePreview(
                    path=f"workflows/transforms/dbt/models/{model_name}.sql",
                    content=_render_dbt_deduplicate(
                        source_relation,
                        str(transform_values.get("partition_by") or unique_key),
                        str(transform_values.get("order_by") or unique_key),
                    ),
                )
            )
        if transform.contribution_id == "dbt.aggregate":
            model_name = _slug(str(transform_values.get("model_name") or f"{table_name}_summary"))
            source_relation = str(
                transform_values.get("source_relation") or f"ref('stg_{table_name}')"
            )
            planned_models.append(model_name)
            files.append(
                WorkflowFilePreview(
                    path=f"workflows/transforms/dbt/models/{model_name}.sql",
                    content=_render_dbt_aggregate(
                        source_relation,
                        str(transform_values.get("group_by") or unique_key),
                        _coerce_fields(transform_values.get("metrics")),
                    ),
                )
            )

    for quality in request.selections_for("quality"):
        if quality.contribution_id != "pandera.quality-checks":
            continue
        selected.append(quality.contribution_id)
        files.append(
            WorkflowFilePreview(
                path=f"workflows/quality/{domain}/{table_name}_quality.py",
                content=_render_pandera_quality(
                    domain,
                    table_name,
                    unique_key,
                    quality.values,
                ),
            )
        )

    for publish in request.selections_for("publish"):
        if not publish.contribution_id:
            continue
        selected.append(publish.contribution_id)
        if publish.contribution_id == "dagster.orchestration":
            files.append(
                WorkflowFilePreview(
                    path=f"workflows/orchestration/{_slug(request.workflow_name)}.py",
                    content=_render_dagster_orchestration(
                        request.workflow_name,
                        domain,
                        table_name,
                        planned_assets,
                        planned_models,
                        publish.values,
                    ),
                )
            )
        if publish.contribution_id == "openmetadata.catalog":
            files.append(
                WorkflowFilePreview(
                    path=f"workflows/catalog/{domain}/{_slug(request.workflow_name)}.yml",
                    content=_render_openmetadata_catalog(
                        request.workflow_name,
                        domain,
                        table_name,
                        planned_models,
                        publish.values,
                    ),
                )
            )

    disabled_stages: dict[str, str] = {}
    if not request.selections_for("quality"):
        disabled_stages["quality"] = "No quality wizard contribution selected."
    if not request.selections_for("publish"):
        disabled_stages["publish"] = "No publish wizard contribution selected."

    action = WorkflowApplyAction(
        id=f"workflow.apply.{_slug(request.workflow_name)}",
        label="Create workflow files",
        target_files=[file.path for file in files],
        conflict_policy="fail-on-conflict",
        expected_evidence=[f"Created {file.path}" for file in files],
    )
    return WorkflowProposal(
        workflow_name=request.workflow_name,
        domain=domain,
        selected_contributions=selected,
        planned_assets=planned_assets,
        planned_tables=planned_tables,
        planned_models=planned_models,
        files=files,
        disabled_stages=disabled_stages,
        actions=[action],
    )


def _append_dbt_transform_files(
    files: list[WorkflowFilePreview],
    workflow_name: str,
    table_name: str,
    unique_key: str,
    fields: list[tuple[str, str]],
    values: dict[str, Any],
) -> list[str]:
    planned_models: list[str] = []
    project_name = _slug(str(values.get("project_name") or workflow_name))
    source_name = _slug(str(values.get("source_name") or "raw"))
    source_table = _slug(str(values.get("source_table") or table_name))
    staging_model = _slug(str(values.get("staging_model_name") or f"stg_{table_name}"))
    staging_relation = str(values.get("staging_source_relation") or f"{source_name}.{source_table}")

    files.extend(
        [
            WorkflowFilePreview(
                path="workflows/transforms/dbt/dbt_project.yml",
                content=_render_dbt_project(project_name),
            ),
            WorkflowFilePreview(
                path=f"workflows/transforms/dbt/models/sources/{source_name}.yml",
                content=_render_dbt_source_yml(source_name, source_table, fields),
            ),
            WorkflowFilePreview(
                path=f"workflows/transforms/dbt/models/{staging_model}.sql",
                content=_render_dbt_model(staging_relation),
            ),
        ]
    )
    planned_models.append(staging_model)
    upstream_relation = f"ref('{staging_model}')"

    if str(values.get("enable_rename") or "no") == "yes" and values.get("renames"):
        model_name = _slug(str(values.get("rename_model_name") or f"renamed_{table_name}"))
        files.append(
            WorkflowFilePreview(
                path=f"workflows/transforms/dbt/models/{model_name}.sql",
                content=_render_dbt_rename_columns(
                    upstream_relation,
                    _coerce_fields(values.get("renames")),
                ),
            )
        )
        planned_models.append(model_name)
        upstream_relation = f"ref('{model_name}')"

    if str(values.get("enable_cast") or "no") == "yes" and values.get("casts"):
        model_name = _slug(str(values.get("cast_model_name") or f"typed_{table_name}"))
        files.append(
            WorkflowFilePreview(
                path=f"workflows/transforms/dbt/models/{model_name}.sql",
                content=_render_dbt_cast_columns(
                    upstream_relation,
                    _coerce_fields(values.get("casts")),
                ),
            )
        )
        planned_models.append(model_name)
        upstream_relation = f"ref('{model_name}')"

    if values.get("where"):
        model_name = _slug(str(values.get("filter_model_name") or f"filtered_{table_name}"))
        files.append(
            WorkflowFilePreview(
                path=f"workflows/transforms/dbt/models/{model_name}.sql",
                content=_render_dbt_filter_rows(
                    upstream_relation,
                    str(values.get("where") or "1 = 1"),
                ),
            )
        )
        planned_models.append(model_name)
        upstream_relation = f"ref('{model_name}')"

    dedupe_model = _slug(str(values.get("dedupe_model_name") or f"clean_{table_name}"))
    files.append(
        WorkflowFilePreview(
            path=f"workflows/transforms/dbt/models/{dedupe_model}.sql",
            content=_render_dbt_deduplicate(
                upstream_relation,
                str(values.get("partition_by") or unique_key),
                str(values.get("order_by") or unique_key),
            ),
        )
    )
    planned_models.append(dedupe_model)
    upstream_relation = f"ref('{dedupe_model}')"

    if str(values.get("enable_aggregate") or "no") == "yes":
        model_name = _slug(str(values.get("aggregate_model_name") or f"{table_name}_summary"))
        files.append(
            WorkflowFilePreview(
                path=f"workflows/transforms/dbt/models/{model_name}.sql",
                content=_render_dbt_aggregate(
                    upstream_relation,
                    str(values.get("group_by") or unique_key),
                    _coerce_fields(values.get("metrics")),
                ),
            )
        )
        planned_models.append(model_name)

    test_model = _slug(str(values.get("test_model_name") or dedupe_model))
    files.append(
        WorkflowFilePreview(
            path=f"workflows/transforms/dbt/models/{test_model}.yml",
            content=_render_dbt_schema_tests(
                test_model,
                _slug(str(values.get("unique_key") or unique_key)),
                fields,
            ),
        )
    )
    return planned_models


def _with_conflict_action_disabled(
    proposal: WorkflowProposal,
    conflicts: list[str],
) -> WorkflowProposal:
    action = WorkflowApplyAction(
        id=proposal.actions[0].id,
        label=proposal.actions[0].label,
        target_files=proposal.actions[0].target_files,
        conflict_policy=proposal.actions[0].conflict_policy,
        enabled=False,
        reason=f"Resolve file conflicts before applying: {', '.join(conflicts)}",
        expected_evidence=proposal.actions[0].expected_evidence,
    )
    return WorkflowProposal(
        workflow_name=proposal.workflow_name,
        domain=proposal.domain,
        selected_contributions=proposal.selected_contributions,
        planned_assets=proposal.planned_assets,
        planned_tables=proposal.planned_tables,
        planned_models=proposal.planned_models,
        files=proposal.files,
        warnings=[*proposal.warnings, f"File conflicts: {', '.join(conflicts)}"],
        missing_capabilities=proposal.missing_capabilities,
        disabled_stages=proposal.disabled_stages,
        actions=[action],
    )


def _proposal_from_payload(payload: dict[str, Any]) -> WorkflowProposal:
    return WorkflowProposal(
        workflow_name=str(payload.get("workflow_name") or ""),
        domain=str(payload.get("domain") or ""),
        selected_contributions=list(payload.get("selected_contributions") or []),
        planned_assets=list(payload.get("planned_assets") or []),
        planned_tables=list(payload.get("planned_tables") or []),
        planned_models=list(payload.get("planned_models") or []),
        files=[
            WorkflowFilePreview(
                path=str(item["path"]),
                content=str(item.get("content") or ""),
                mode=item.get("mode", "create"),
            )
            for item in payload.get("files", [])
        ],
        warnings=list(payload.get("warnings") or []),
        missing_capabilities=list(payload.get("missing_capabilities") or []),
        disabled_stages=dict(payload.get("disabled_stages") or {}),
        actions=[
            WorkflowApplyAction(
                id=str(item["id"]),
                label=str(item["label"]),
                target_files=list(item.get("target_files") or []),
                conflict_policy=item.get("conflict_policy", "fail-on-conflict"),
                enabled=bool(item.get("enabled", True)),
                reason=item.get("reason"),
                expected_evidence=list(item.get("expected_evidence") or []),
            )
            for item in payload.get("actions", [])
        ],
    )


def _slug(value: str) -> str:
    lowered = value.strip().lower().replace("-", "_")
    slugged = re.sub(r"[^a-z0-9_]+", "_", lowered).strip("_")
    return slugged or "workflow"


def _class_name(table_name: str) -> str:
    return "Raw" + "".join(part.capitalize() for part in table_name.split("_"))


def _coerce_fields(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]
    return []


def _render_schema(domain: str, table_name: str, unique_key: str, fields: list[str]) -> str:
    class_name = _class_name(table_name)
    field_lines = [f"    {unique_key}: Series[str] = pa.Field(nullable=False)"]
    for item in fields:
        name, _, raw_type = item.partition(":")
        if not name:
            continue
        type_name = raw_type.rstrip("?!") or "str"
        py_type = {"float": "float", "int": "int", "datetime": "str"}.get(type_name, "str")
        nullable = "True" if raw_type.endswith("?") else "False"
        field_lines.append(f"    {_slug(name)}: Series[{py_type}] = pa.Field(nullable={nullable})")
    return (
        f'"""Generated schema for {domain}.{table_name}."""\n\n'
        "import pandera.pandas as pa\n"
        "from pandera.typing import Series\n\n\n"
        f"class {class_name}(pa.DataFrameModel):\n"
        + "\n".join(field_lines)
        + "\n\n    class Config:\n        strict = True\n        coerce = True\n"
    )


def _render_dlt_asset(
    domain: str,
    table_name: str,
    unique_key: str,
    api_base_url: str,
    cron: str,
    response_path: str,
    pagination: str,
    auth: str,
) -> str:
    class_name = _class_name(table_name)
    response_path_line = f', "data_selector": "{response_path}"' if response_path else ""
    pagination_line = ""
    if pagination == "offset-limit":
        pagination_line = ', "paginator": {"type": "offset", "limit": 100}'
    elif pagination == "page-number":
        pagination_line = ', "paginator": {"type": "page_number", "base_page": 1}'
    auth_lines = ""
    if auth == "bearer-token":
        auth_lines = '\n    headers = {"Authorization": "Bearer ${TOKEN}"}'
    elif auth == "api-key-header":
        auth_lines = '\n    headers = {"X-API-Key": "${API_KEY}"}'
    else:
        auth_lines = "\n    headers = {}"
    return f'''"""Generated DLT ingestion asset for {domain}.{table_name}."""

from dlt.sources.rest_api import rest_api
from phlo_dlt import phlo_ingestion

from workflows.schemas.{domain} import {class_name}


@phlo_ingestion(
    table_name="{table_name}",
    unique_key="{unique_key}",
    validation_schema={class_name},
    group="{domain}",
    cron="{cron}",
    freshness_hours=(1, 24),
)
def {table_name}(partition_date: str):
    base_url = "{api_base_url}"
    if not base_url:
        raise RuntimeError("Missing API base URL. Configure base_url before materializing.")
{auth_lines}

    return rest_api(
        client={{"base_url": base_url, "headers": headers}},
        resources=[{{"name": "{table_name}", "endpoint": {{"path": ""{response_path_line}{pagination_line}}}}}],
    )
'''


def _render_ingestion_test(domain: str, table_name: str, unique_key: str) -> str:
    class_name = _class_name(table_name)
    return f'''"""Generated tests for {domain}.{table_name}."""

from workflows.schemas.{domain} import {class_name}


def test_schema_contains_unique_key() -> None:
    assert "{unique_key}" in {class_name}.to_schema().columns
'''


def _render_sling_asset(
    domain: str,
    table_name: str,
    primary_key: str,
    source_name: str,
    source_stream: str,
    replication_mode: str,
    update_key: str,
    cron: str,
) -> str:
    resolved_update_key = update_key or primary_key
    return f'''"""Generated Sling replication asset for {domain}.{table_name}."""

from phlo_sling import phlo_sling_replication


@phlo_sling_replication(
    stream_name="{source_stream}",
    table_name="{table_name}",
    source_conn="{source_name}",
    group="{domain}",
    mode="{replication_mode}",
    primary_key="{primary_key}",
    update_key="{resolved_update_key}",
    cron="{cron}",
    freshness_hours=(4, 24),
)
def replicate_{table_name}(context):
    return None
'''


def _render_sling_replication_config(
    domain: str,
    table_name: str,
    primary_key: str,
    source_name: str,
    source_stream: str,
    replication_mode: str,
    update_key: str,
    cron: str,
) -> str:
    update_key_line = f"\nupdate_key: {update_key or primary_key}"
    return f"""name: {domain}_{table_name}_replication
provider: phlo-sling
schedule: "{cron}"
source:
  connection: {source_name}
  stream: {source_stream}
target:
  table: {table_name}
replication:
  mode: {replication_mode}
  primary_key: {primary_key}{update_key_line}
"""


def _render_pandera_quality(
    domain: str,
    table_name: str,
    unique_key: str,
    values: dict[str, Any],
) -> str:
    target_table = str(values.get("target_table") or f"{domain}.{table_name}")
    check_name = _slug(str(values.get("check_name") or f"{table_name}_quality"))
    null_columns = _coerce_fields(values.get("not_null_columns")) or [unique_key]
    range_checks = _coerce_fields(values.get("range_checks"))
    freshness_column = str(values.get("freshness_column") or "").strip()
    freshness_hours = str(values.get("freshness_hours") or "24").strip() or "24"
    min_rows = str(values.get("min_rows") or "1").strip() or "1"

    check_lines = [
        f'        UniqueCheck(columns=["{unique_key}"]),',
        f"        NullCheck(columns={null_columns!r}),",
        f"        CountCheck(min_rows={min_rows}),",
    ]
    for item in range_checks:
        column, _, bounds = item.partition(":")
        minimum, _, maximum = bounds.partition(":")
        if column.strip() and minimum.strip() and maximum.strip():
            check_lines.append(
                "        "
                f'RangeCheck(column="{_slug(column)}", min_value={minimum.strip()}, '
                f"max_value={maximum.strip()}),"
            )
    if freshness_column:
        check_lines.append(
            "        "
            f'FreshnessCheck(timestamp_column="{_slug(freshness_column)}", '
            f"max_age_hours={freshness_hours}),"
        )
    checks = "\n".join(check_lines)
    return f'''"""Generated Pandera quality checks for {target_table}."""

from phlo_pandera import (
    CountCheck,
    FreshnessCheck,
    NullCheck,
    RangeCheck,
    UniqueCheck,
    phlo_pandera,
)


@phlo_pandera(
    table="{target_table}",
    group="{domain}",
    checks=[
{checks}
    ],
)
def {check_name}():
    pass
'''


def _render_dagster_orchestration(
    workflow_name: str,
    domain: str,
    table_name: str,
    planned_assets: list[str],
    planned_models: list[str],
    values: dict[str, Any],
) -> str:
    job_name = _slug(str(values.get("job_name") or f"{workflow_name}_job"))
    asset_group = _slug(str(values.get("asset_group") or domain))
    schedule = str(values.get("schedule") or "0 2 * * *")
    include_sensor = str(values.get("include_sensor") or "no") == "yes"
    asset_list = ", ".join(f'"{item}"' for item in planned_assets)
    model_list = ", ".join(f'"{item}"' for item in planned_models)
    sensor = ""
    sensor_names = ""
    if include_sensor:
        sensor = f"""

@dg.sensor(job={job_name})
def {_slug(workflow_name)}_external_sensor(context):
    return dg.SkipReason("Connect this sensor to an external event source.")
"""
        sensor_names = f", sensors=[{_slug(workflow_name)}_external_sensor]"
    return f'''"""Generated Dagster orchestration scaffold for {workflow_name}."""

import dagster as dg

WORKFLOW_ASSETS = [{asset_list}]
WORKFLOW_MODELS = [{model_list}]
ASSET_GROUP = "{asset_group}"
TARGET_TABLE = "{table_name}"

{job_name} = dg.define_asset_job(
    name="{job_name}",
    selection=dg.AssetSelection.groups(ASSET_GROUP),
)

{_slug(workflow_name)}_schedule = dg.ScheduleDefinition(
    job={job_name},
    cron_schedule="{schedule}",
)
{sensor}

defs = dg.Definitions(
    jobs=[{job_name}],
    schedules=[{_slug(workflow_name)}_schedule]{sensor_names},
)
'''


def _render_openmetadata_catalog(
    workflow_name: str,
    domain: str,
    table_name: str,
    planned_models: list[str],
    values: dict[str, Any],
) -> str:
    tags = _coerce_fields(values.get("tags"))
    tag_lines = "\n".join(f"  - {tag}" for tag in tags) or "  - generated"
    model_lines = "\n".join(f"  - {model}" for model in planned_models) or "  - none"
    description = str(
        values.get("description") or f"Generated catalog metadata for the {workflow_name} workflow."
    )
    return f"""workflow: {workflow_name}
provider: phlo-openmetadata
service: {values.get("service_name") or "phlo"}
database: {values.get("database") or "warehouse"}
schema: {values.get("schema") or domain}
owner: {values.get("owner") or "data-platform"}
description: "{description}"
tables:
  - name: {table_name}
    domain: {domain}
    generated_models:
{model_lines}
tags:
{tag_lines}
"""


def _render_dbt_project(project_name: str) -> str:
    return f"""name: {project_name}
version: 1.0.0
config-version: 2
profile: phlo
model-paths: ["models"]
models:
  {project_name}:
    +materialized: table
"""


def _render_dbt_model(source_relation: str) -> str:
    return f"""select *
from {source_relation}
"""


def _render_dbt_rename_columns(source_relation: str, renames: list[str]) -> str:
    expressions = []
    for item in renames:
        source, _, target = item.partition(":")
        if source.strip() and target.strip():
            expressions.append(f"    {source.strip()} as {_slug(target)}")
    if not expressions:
        expressions.append("    *")
    select_lines = ",\n".join(expressions)
    return f"""select
{select_lines}
from {source_relation}
"""


def _render_dbt_cast_columns(source_relation: str, casts: list[str]) -> str:
    expressions = []
    for item in casts:
        column, _, target_type = item.partition(":")
        if column.strip() and target_type.strip():
            expressions.append(
                f"    cast({column.strip()} as {target_type.strip()}) as {_slug(column)}"
            )
    if not expressions:
        expressions.append("    *")
    select_lines = ",\n".join(expressions)
    return f"""select
{select_lines}
from {source_relation}
"""


def _render_dbt_filter_rows(source_relation: str, where_clause: str) -> str:
    return f"""select *
from {source_relation}
where {where_clause.strip() or "1 = 1"}
"""


def _render_dbt_deduplicate(source_relation: str, partition_by: str, order_by: str) -> str:
    return f"""with ranked as (
    select
        *,
        row_number() over (
            partition by {partition_by}
            order by {order_by} desc
        ) as phlo_row_number
    from {source_relation}
)

select * exclude (phlo_row_number)
from ranked
where phlo_row_number = 1
"""


def _render_dbt_aggregate(source_relation: str, group_by: str, metrics: list[str]) -> str:
    group_columns = [column.strip() for column in group_by.split(",") if column.strip()]
    metric_expressions = []
    for item in metrics:
        name, _, expression = item.partition(":")
        if name.strip() and expression.strip():
            metric_expressions.append(f"    {expression.strip()} as {_slug(name)}")
    select_lines = [f"    {column}" for column in group_columns] + metric_expressions
    if not select_lines:
        select_lines = ["    count(*) as row_count"]
    group_line = f"\ngroup by {', '.join(group_columns)}" if group_columns else ""
    select_sql = ",\n".join(select_lines)
    return f"""select
{select_sql}
from {source_relation}{group_line}
"""


def _render_dbt_source_yml(source_name: str, table_name: str, fields: list[str]) -> str:
    columns = "\n".join(
        f"      - name: {_slug(item.partition(':')[0])}"
        for item in fields
        if item.partition(":")[0]
    )
    if not columns:
        columns = "      - name: id"
    return f"""version: 2

sources:
  - name: {source_name}
    schema: raw
    tables:
      - name: {table_name}
        columns:
{columns}
"""


def _render_dbt_schema_tests(model_name: str, unique_key: str, fields: list[str]) -> str:
    extra_columns = "\n".join(
        f"      - name: {_slug(item.partition(':')[0])}"
        for item in fields
        if item.partition(":")[0]
    )
    return f"""version: 2

models:
  - name: {model_name}
    description: Staging model generated by the Phlo workflow wizard.
    columns:
      - name: {unique_key}
        tests:
          - not_null
          - unique
{extra_columns}
"""

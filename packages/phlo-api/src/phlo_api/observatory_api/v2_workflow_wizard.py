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


class V2WorkflowWizardSelection(BaseModel):
    """User-selected contribution and values for one workflow stage."""

    contribution_id: str
    values: dict[str, Any] = Field(default_factory=dict)


class V2WorkflowProposalRequest(BaseModel):
    """Request body for workflow wizard proposal generation."""

    workflow_name: str
    domain: str
    selections: dict[str, V2WorkflowWizardSelection | list[V2WorkflowWizardSelection]] = Field(
        default_factory=dict
    )


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
    for module_name in ("phlo_dlt.plugin", "phlo_dbt.plugin"):
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

    contract_request = WorkflowProposalRequest(
        workflow_name=request.workflow_name,
        domain=request.domain,
        selections={
            stage: _selection_payload(selection) for stage, selection in request.selections.items()
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
    table_name = _slug(str(source_values.get("table_name") or request.workflow_name))
    unique_key = _slug(str(source_values.get("unique_key") or "id"))
    fields = _coerce_fields(source_values.get("fields"))
    api_base_url = str(source_values.get("api_base_url") or "")
    cron = str(source_values.get("cron") or "0 */1 * * *")
    response_path = str(source_values.get("response_path") or "")
    pagination = str(source_values.get("pagination") or "none")
    auth = str(source_values.get("auth") or "none")

    files = [
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
    selected = [source.contribution_id]
    planned_models: list[str] = []

    for transform in request.selections_for("transform"):
        if not transform.contribution_id:
            continue
        selected.append(transform.contribution_id)
        transform_values = transform.values
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
        planned_assets=[f"dlt_{table_name}"],
        planned_tables=[table_name],
        planned_models=planned_models,
        files=files,
        disabled_stages={
            "quality": "No quality wizard contribution selected.",
            "publish": "No publish wizard contribution selected.",
        },
        actions=[action],
    )


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

"""Provider-neutral workflow authoring helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from phlo.capabilities import list_capabilities, resolve_capability
from phlo.capabilities.discovery import discover_capabilities


class WorkflowAuthoringError(RuntimeError):
    """Raised when a workflow authoring provider cannot complete a request."""


@dataclass(frozen=True)
class WorkflowCreateResult:
    """Normalized result returned by workflow authoring providers."""

    workflow_type: str
    provider: str
    domain: str
    table: str
    files: list[str]
    next_steps: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


def create_workflow_with_provider(
    *,
    project_root: Path,
    workflow_type: str,
    domain: str,
    table: str,
    unique_key: str,
    cron: str,
    api_base_url: str | None = None,
    fields: list[str] | None = None,
    provider: str | None = None,
    contribution_id: str | None = None,
    values: Mapping[str, Any] | None = None,
) -> WorkflowCreateResult:
    """Create a workflow through the resolved workflow authoring capability."""
    resolution = _resolve_workflow_authoring(provider)
    request = {
        "workflow_type": workflow_type,
        "domain": domain,
        "table": table,
        "unique_key": unique_key,
        "cron": cron,
        "api_base_url": api_base_url,
        "fields": list(fields or []),
        "provider": provider,
        "contribution_id": contribution_id,
        "values": dict(values or {}),
    }
    try:
        raw_result = resolution.provider.create_workflow(
            project_root=project_root.resolve(),
            request=request,
        )
    except (FileExistsError, WorkflowAuthoringError):
        raise
    except Exception as exc:
        raise WorkflowAuthoringError(str(exc)) from exc
    return _normalize_create_result(raw_result, provider=resolution.name)


def _resolve_workflow_authoring(provider: str | None) -> Any:
    discover_capabilities()
    resolution = resolve_capability("workflow_authoring", provider)
    if resolution is not None:
        return resolution

    available = list_capabilities("workflow_authoring")
    if provider:
        raise WorkflowAuthoringError(
            f"Workflow authoring provider {provider!r} is not available. "
            f"Available providers: {', '.join(available) or 'none'}."
        )
    if not available:
        raise WorkflowAuthoringError(
            'No workflow authoring provider is available. Install an ingestion provider such as "phlo-dlt" or "phlo-sling".'
        )
    raise WorkflowAuthoringError(
        "Multiple workflow authoring providers are available. "
        f"Choose one with --provider or configure phlo_default_capabilities.workflow_authoring. "
        f"Available providers: {', '.join(available)}."
    )


def _normalize_create_result(result: Mapping[str, Any], *, provider: str) -> WorkflowCreateResult:
    try:
        return WorkflowCreateResult(
            workflow_type=str(result.get("workflow_type") or "ingestion"),
            provider=str(result.get("provider") or provider),
            domain=str(result["domain"]),
            table=str(result["table"]),
            files=[str(item) for item in result.get("files", [])],
            next_steps=[str(item) for item in result.get("next_steps", [])],
            metadata=dict(result.get("metadata") or {}),
        )
    except KeyError as exc:
        raise WorkflowAuthoringError(
            f"Workflow authoring provider returned no {exc.args[0]!r}."
        ) from exc

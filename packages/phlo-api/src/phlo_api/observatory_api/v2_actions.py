"""Guarded Observatory v2 action family dispatcher."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from phlo_api.observatory_api.v2_models import (
    V2Action,
    V2ActionRequest,
    V2ActionResult,
    V2Health,
    V2Operation,
)


@dataclass(frozen=True)
class _ActionFamily:
    prefix: str
    kind: str
    label: str
    reason: str
    risk_level: Literal["low", "medium", "high", "critical"] = "low"
    required_capability: str | None = None


_ACTION_FAMILIES = (
    _ActionFamily(
        prefix="quality:",
        kind="quality.rerun",
        label="Re-run quality check",
        reason="Quality re-runs need a provider-backed execution contract.",
        required_capability="quality_backend",
    ),
    _ActionFamily(
        prefix="branch:",
        kind="branch.workflow",
        label="Run branch workflow",
        reason="Branch workflows need a catalog provider write contract.",
        risk_level="medium",
        required_capability="catalog",
    ),
    _ActionFamily(
        prefix="storage:",
        kind="storage.maintenance",
        label="Run storage maintenance",
        reason="Storage maintenance needs a table storage provider write contract.",
        risk_level="medium",
        required_capability="table_store",
    ),
    _ActionFamily(
        prefix="metadata:",
        kind="metadata.sync",
        label="Sync metadata",
        reason="Metadata sync needs a metadata provider write contract.",
        required_capability="metadata_catalog",
    ),
    _ActionFamily(
        prefix="alert:",
        kind="alert.workflow",
        label="Run alert workflow",
        reason="Alert workflows need an alerting provider write contract.",
        required_capability="alert_sink",
    ),
    _ActionFamily(
        prefix="api:",
        kind="api.publish",
        label="Publish API",
        reason="API publishing needs an API gateway provider write contract.",
        risk_level="medium",
        required_capability="api_backend",
    ),
)


def _known_family_for_action(action_id: str) -> _ActionFamily | None:
    for family in _ACTION_FAMILIES:
        if not action_id.startswith(family.prefix):
            continue
        if family.kind == "quality.rerun" and not action_id.endswith(":rerun"):
            continue
        return family
    return None


def _skipped_action_result(request: V2ActionRequest, family: _ActionFamily) -> V2ActionResult:
    action = V2Action(
        id=request.action_id,
        label=family.label,
        kind=family.kind,
        enabled=False,
        requires_confirmation=True,
        reason=family.reason,
        risk_level=family.risk_level,
        required_capability=family.required_capability,
    )
    return V2ActionResult(
        action=action,
        status="skipped",
        message=family.reason,
    )


def _failed_action_result(request: V2ActionRequest) -> V2ActionResult:
    message = f"Unsupported Observatory v2 action: {request.action_id}"
    action = V2Action(
        id=request.action_id,
        label="Unsupported action",
        kind="unsupported",
        enabled=False,
        requires_confirmation=True,
        reason=message,
    )
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
        ),
    )


def execute_v2_action(request: V2ActionRequest) -> V2ActionResult:
    """Execute or decline a guarded Observatory v2 action."""
    family = _known_family_for_action(request.action_id)
    if family is not None:
        return _skipped_action_result(request, family)
    return _failed_action_result(request)

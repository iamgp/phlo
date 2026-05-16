"""Guarded Observatory v2 action family dispatcher."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Any, Literal

from phlo.capabilities.resolver import resolve_capability
from phlo.capabilities.runtime import RuntimeRouting

from phlo_api.observatory_api.v2_metadata import safe_metadata
from phlo_api.observatory_api.v2_models import (
    V2Action,
    V2ActionRequest,
    V2ActionResult,
    V2Health,
    V2Operation,
    V2ResourceRef,
)


@dataclass(frozen=True)
class _ActionFamily:
    prefix: str
    kind: str
    label: str
    reason: str
    risk_level: Literal["low", "medium", "high", "critical"] = "low"
    required_capability: str | None = None


@dataclass
class _ActionRuntimeContext:
    run_id: str | None = None
    partition_key: str | None = None
    tags: dict[str, str] = field(default_factory=dict)
    _resources: dict[str, Any] = field(default_factory=dict)

    @property
    def logger(self) -> Any:
        return logging.getLogger("phlo.observatory.v2.actions")

    @property
    def resources(self) -> dict[str, Any]:
        return self._resources

    @property
    def routing(self) -> RuntimeRouting:
        return RuntimeRouting(
            partition_key=self.partition_key,
            run_id=self.run_id,
            resources=self._resources,
        )

    def get_resource(self, name: str) -> Any:
        return self._resources[name]


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
        reason="No executable table storage provider is registered for this maintenance action.",
        risk_level="medium",
        required_capability="table_store",
    ),
    _ActionFamily(
        prefix="metadata:",
        kind="metadata.sync",
        label="Sync metadata",
        reason="No executable metadata provider is registered for this sync action.",
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


def _action_for_family(
    request: V2ActionRequest,
    family: _ActionFamily,
    *,
    enabled: bool,
    reason: str | None = None,
) -> V2Action:
    return V2Action(
        id=request.action_id,
        label=family.label,
        kind=family.kind,
        enabled=enabled,
        requires_confirmation=True,
        reason=reason,
        risk_level=family.risk_level,
        required_capability=family.required_capability,
    )


def _operation(
    request: V2ActionRequest,
    action: V2Action,
    *,
    status: Literal["succeeded", "failed", "skipped"],
    message: str,
    target: V2ResourceRef | None = None,
    metadata: dict[str, Any] | None = None,
) -> V2Operation:
    state: Literal["ok", "warning", "error"] = "ok"
    if status == "skipped":
        state = "warning"
    elif status == "failed":
        state = "error"
    return V2Operation(
        id=request.action_id,
        name=action.label,
        kind=action.kind,
        status=status,
        health=V2Health(state=state, message=message),
        target=target,
        metadata=safe_metadata(metadata or {}),
    )


def _check_for_action(action_id: str, registry: Any) -> Any | None:
    check_action_id = action_id.removeprefix("quality:")
    try:
        checks = registry.list_checks()
    except Exception:
        return None
    for check in checks:
        if f"{check.asset_key}:{check.name}:rerun" == check_action_id:
            return check
    return None


def _execute_quality_action(
    request: V2ActionRequest,
    family: _ActionFamily,
    registry: Any | None,
) -> V2ActionResult | None:
    if registry is None:
        return None

    check = _check_for_action(request.action_id, registry)
    if check is None:
        message = "Quality check is not registered in the capability registry."
        action = _action_for_family(request, family, enabled=False, reason=message)
        return V2ActionResult(
            action=action,
            status="skipped",
            message=message,
            operation=_operation(request, action, status="skipped", message=message),
        )

    if not callable(getattr(check, "fn", None)):
        message = "Quality check has no executable function."
        action = _action_for_family(request, family, enabled=False, reason=message)
        return V2ActionResult(
            action=action,
            status="skipped",
            message=message,
            operation=_operation(
                request,
                action,
                status="skipped",
                message=message,
                target=V2ResourceRef(
                    kind="quality",
                    id=f"{check.asset_key}:{check.name}",
                    label=check.name,
                ),
            ),
        )

    action = _action_for_family(request, family, enabled=True)
    context = _ActionRuntimeContext(tags={"phlo/action_id": request.action_id})
    try:
        result = check.fn(context)
    except Exception as exc:
        message = f"Quality check execution failed: {exc}"
        return V2ActionResult(
            action=action,
            status="failed",
            message=message,
            operation=_operation(
                request,
                action,
                status="failed",
                message=message,
                target=V2ResourceRef(
                    kind="quality",
                    id=f"{check.asset_key}:{check.name}",
                    label=check.name,
                ),
            ),
        )

    passed = bool(getattr(result, "passed", False))
    status: Literal["succeeded", "failed"] = "succeeded" if passed else "failed"
    message = (
        f"Quality check {check.name} passed." if passed else f"Quality check {check.name} failed."
    )
    metadata = {
        "asset_key": getattr(result, "asset_key", check.asset_key),
        "check_name": getattr(result, "check_name", check.name),
        "severity": getattr(result, "severity", getattr(check, "severity", None)),
        "metadata": getattr(result, "metadata", {}),
    }
    return V2ActionResult(
        action=action,
        status=status,
        message=message,
        operation=_operation(
            request,
            action,
            status=status,
            message=message,
            target=V2ResourceRef(
                kind="quality",
                id=f"{check.asset_key}:{check.name}",
                label=check.name,
            ),
            metadata=metadata,
        ),
    )


def _execute_alert_action(
    request: V2ActionRequest,
    family: _ActionFamily,
    registry: Any | None,
) -> V2ActionResult | None:
    if registry is None:
        return None

    resolution = resolve_capability("alert_sink", registry=registry)
    sink = resolution.provider if resolution is not None else None
    send_alert = getattr(sink, "send_alert", None)
    if not callable(send_alert):
        return None

    action = _action_for_family(request, family, enabled=True)
    try:
        sent = bool(
            send_alert(
                title="Observatory action requested",
                message=f"Observatory executed action {request.action_id}.",
                severity="warning",
            )
        )
    except Exception as exc:
        message = f"Alert workflow failed: {exc}"
        return V2ActionResult(
            action=action,
            status="failed",
            message=message,
            operation=_operation(request, action, status="failed", message=message),
        )

    status: Literal["succeeded", "failed"] = "succeeded" if sent else "failed"
    message = "Alert workflow sent." if sent else "Alert sink declined the alert."
    return V2ActionResult(
        action=action,
        status=status,
        message=message,
        operation=_operation(
            request,
            action,
            status=status,
            message=message,
            metadata={"provider": resolution.name if resolution is not None else None},
        ),
    )


def _provider_action_result(
    request: V2ActionRequest,
    family: _ActionFamily,
    registry: Any | None,
) -> V2ActionResult | None:
    if family.kind == "quality.rerun":
        return _execute_quality_action(request, family, registry)
    if family.kind == "alert.workflow":
        return _execute_alert_action(request, family, registry)
    return None


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


def execute_v2_action(request: V2ActionRequest, *, registry: Any | None = None) -> V2ActionResult:
    """Execute or decline a guarded Observatory v2 action."""
    family = _known_family_for_action(request.action_id)
    if family is not None:
        result = _provider_action_result(request, family, registry)
        if result is not None:
            return result
        return _skipped_action_result(request, family)
    return _failed_action_result(request)

"""Platform principal for the Dagster daemon.

The Dagster daemon (scheduler, sensor evaluator, auto-materializer) runs
without a human user. This module provides a named platform principal so
that daemon-initiated runs are attributed, authorized, and audited.

Usage:
    Call authorize_daemon_run() when the daemon is about to create a run.
    It calls enforce() with a platform principal, which emits an
    authorization audit event. If enforcement denies the run, it raises
    RuntimeError.

Run Tag Propagation:
    After authorization, add the PHLO_* tags to the run config so that
    downstream steps can read the principal and trigger metadata.
"""

from __future__ import annotations

from dagster._core.run_coordinator import QueuedRunCoordinator, SubmitRunContext
from dagster._core.storage.tags import (
    AUTOMATION_CONDITION_TAG,
    AUTO_MATERIALIZE_TAG,
    AUTO_RETRY_RUN_ID_TAG,
    RETRY_NUMBER_TAG,
    SCHEDULE_NAME_TAG,
    SENSOR_NAME_TAG,
)

from phlo.capabilities import AuthPrincipal, DecisionContext, ResourceRef
from phlo.logging import get_logger
from phlo.security import is_regulated
from phlo.security.enforcement import enforce

logger = get_logger(__name__)

DAEMON_SUBJECT = "platform:dagster-daemon"
DAEMON_PRINCIPAL_TYPE = "platform"

# Run tags for principal propagation through Dagster run storage
PHLO_PRINCIPAL_TAG = "phlo/executing_principal"
PHLO_TRIGGER_TAG = "phlo/trigger"
PHLO_INITIATOR_TAG = "phlo/initiating_principal"
PHLO_TRIGGER_KIND_TAG = "phlo/trigger_kind"
_DAEMON_AUTH_HEADERS = ("Authorization", "X-Dagster-User", "X-Dagster-Api-Token")


def create_daemon_principal(
    trigger_kind: str,
    trigger_name: str,
    initiating_user: str | None = None,
) -> AuthPrincipal:
    """Create an AuthPrincipal for the Dagster daemon.

    Args:
        trigger_kind: What caused the run — "schedule", "sensor",
            "auto_materialize", or "retry".
        trigger_name: Name of the schedule/sensor/asset that triggered it.
        initiating_user: Subject of the human who configured the trigger,
            if known (e.g., from schedule metadata).

    Returns:
        AuthPrincipal with principal_type="platform".
    """
    attributes: dict[str, str] = {
        "authentication_source": "daemon",
        "trigger_kind": trigger_kind,
        "trigger_name": trigger_name,
    }
    if initiating_user:
        attributes["initiating_principal"] = initiating_user

    return AuthPrincipal(
        subject=DAEMON_SUBJECT,
        principal_type=DAEMON_PRINCIPAL_TYPE,
        groups=("dagster-daemon",),
        attributes=attributes,
    )


def build_run_tags(
    trigger_kind: str,
    trigger_name: str,
    initiating_user: str | None = None,
) -> dict[str, str]:
    """Build Dagster run tags for principal propagation.

    These tags travel with the run through Dagster's run storage and are
    visible in the UI, logs, and downstream steps.

    Args:
        trigger_kind: "schedule", "sensor", "auto_materialize", or "retry".
        trigger_name: Name of the schedule/sensor/asset.
        initiating_user: Human who configured the trigger, if known.

    Returns:
        Dict of tag key → value suitable for Dagster run tags.
    """
    tags: dict[str, str] = {
        PHLO_PRINCIPAL_TAG: DAEMON_SUBJECT,
        PHLO_TRIGGER_TAG: trigger_name,
        PHLO_TRIGGER_KIND_TAG: trigger_kind,
    }
    if initiating_user:
        tags[PHLO_INITIATOR_TAG] = initiating_user
    return tags


def authorize_daemon_run(
    trigger_kind: str,
    trigger_name: str,
    asset_selection: list[str] | None = None,
    run_id: str | None = None,
    initiating_user: str | None = None,
) -> None:
    """Authorize and audit a daemon-initiated run.

    Call this when the daemon is about to create a run. It calls enforce()
    with the platform principal, which emits an authorization audit event.

    If enforcement denies the run, raises RuntimeError. The daemon should
    catch this and skip the run with an error log.

    In non-regulated mode, this is a no-op.

    Args:
        trigger_kind: "schedule", "sensor", "auto_materialize", or "retry".
        trigger_name: Name of the schedule/sensor/asset.
        asset_selection: List of asset keys being materialized, if known.
        run_id: Dagster run ID if already assigned.
        initiating_user: Human who configured the trigger, if known.

    Raises:
        RuntimeError: If enforcement denies the run.
    """
    if not is_regulated():
        return

    principal = create_daemon_principal(
        trigger_kind=trigger_kind,
        trigger_name=trigger_name,
        initiating_user=initiating_user,
    )

    resource_id = trigger_name
    if asset_selection:
        resource_id = ",".join(asset_selection[:5])

    context_attributes: dict[str, str] = {
        "trigger_kind": trigger_kind,
        "trigger_name": trigger_name,
    }
    if asset_selection:
        context_attributes["asset_selection"] = ",".join(asset_selection)

    result = enforce(
        principal=principal,
        action="run.execute",
        resource=ResourceRef(resource_type="run", resource_id=resource_id),
        context=DecisionContext(
            request_id=run_id,
            attributes=context_attributes,
        ),
        request_id=run_id,
        surface="dagster-daemon",
    )

    if not result.allowed:
        msg = (
            f"Daemon run denied: {result.reason_code or 'explicit_deny'} "
            f"(trigger={trigger_kind}:{trigger_name})"
        )
        logger.warning(
            "daemon_run_denied",
            trigger_kind=trigger_kind,
            trigger_name=trigger_name,
            reason_code=result.reason_code,
        )
        raise RuntimeError(msg)

    logger.info(
        "daemon_run_authorized",
        trigger_kind=trigger_kind,
        trigger_name=trigger_name,
        run_id=run_id,
    )


def _infer_daemon_trigger(run_tags: dict[str, str]) -> tuple[str, str] | None:
    """Infer daemon trigger kind and name from Dagster run tags."""
    if schedule_name := run_tags.get(SCHEDULE_NAME_TAG):
        return "schedule", schedule_name
    if sensor_name := run_tags.get(SENSOR_NAME_TAG):
        return "sensor", sensor_name
    if run_tags.get(AUTO_MATERIALIZE_TAG) or run_tags.get(AUTOMATION_CONDITION_TAG):
        return "auto_materialize", run_tags.get(PHLO_TRIGGER_TAG, "auto_materialize")
    if run_tags.get(AUTO_RETRY_RUN_ID_TAG) or run_tags.get(RETRY_NUMBER_TAG):
        retry_name = run_tags.get(AUTO_RETRY_RUN_ID_TAG) or run_tags.get(PHLO_TRIGGER_TAG, "retry")
        return "retry", retry_name
    return None


def _has_request_principal(context: SubmitRunContext) -> bool:
    """Return True when the run submission came from an authenticated request."""
    return any(context.get_request_header(header) for header in _DAEMON_AUTH_HEADERS)


class PhloQueuedRunCoordinator(QueuedRunCoordinator):
    """Queued run coordinator that audits daemon-initiated Dagster runs."""

    def submit_run(self, context: SubmitRunContext):
        dagster_run = context.dagster_run
        trigger = _infer_daemon_trigger(dagster_run.tags)

        if is_regulated() and trigger and not _has_request_principal(context):
            trigger_kind, trigger_name = trigger
            authorize_daemon_run(
                trigger_kind=trigger_kind,
                trigger_name=trigger_name,
                run_id=dagster_run.run_id,
            )
            self._instance.add_run_tags(
                dagster_run.run_id,
                build_run_tags(
                    trigger_kind=trigger_kind,
                    trigger_name=trigger_name,
                ),
            )

        return super().submit_run(context)

"""CLI command authorization wrappers.

Provides decorators and wrapper functions to enforce authorization
on mutation commands through the CLI regulated surface adapter.

Usage:
    from phlo.cli.authorization import require_mutation_authorization

    @click.command("start")
    @click.option(...)
    @require_mutation_authorization("services.start")
    def start_cmd(...):
        ...

Or use the enforce_mutation context manager for more control:
    from phlo.cli.authorization import enforce_mutation_context

    def some_mutation_handler():
        with enforce_mutation_context("services.start", resource_id="my-service"):
            # mutation logic
            pass
"""

from __future__ import annotations

import functools
import os
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

from phlo.logging import get_logger
from phlo.security.adapters import EnforcementResult
from phlo.security.enforcement import EnforcementContext

logger = get_logger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def require_mutation_authorization(
    command: str,
    resource_id: str | Callable[[Any], str] | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator that enforces authorization on a mutation command.

    Use this decorator on Click command functions that perform mutations.
    The decorator resolves the principal from the environment, enforces
    through core, and raises click exception on denial.

    Args:
        command: Command path (e.g., "services.start")
        resource_id: Optional resource ID extractor. Can be:
            - None: uses command as resource ID
            - str: static resource ID
            - Callable: function that receives the click.Context and returns resource ID

    Returns:
        Decorated command function

    Example:
        @click.command("start")
        @click.option("-d", "--detach", is_flag=True)
        @require_mutation_authorization("services.start", resource_id=lambda ctx: ctx.params.get("service"))
        def start_cmd(detach, service):
            ...
    """

    def decorator(fn: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            from phlo.cli.authorization import get_cli_adapter

            resolved_resource_id: str | None = None
            if resource_id is None:
                resolved_resource_id = None
            elif isinstance(resource_id, str):
                resolved_resource_id = resource_id
            else:
                try:
                    resolved_resource_id = resource_id(kwargs.get("ctx"))
                except Exception:
                    resolved_resource_id = command

            adapter = get_cli_adapter()
            result = adapter.enforce_mutation(command, resolved_resource_id)

            if not result.allowed:
                logger.warning(
                    "cli_command_authorization_denied",
                    command=command,
                    reason_code=result.reason_code,
                    explanation=result.explanation,
                )
                msg = f"Authorization denied for '{command}'"
                if result.explanation:
                    msg += f": {result.explanation}"
                raise SystemExit(1)

            return fn(*args, **kwargs)

        return wrapper

    return decorator


class MutationContext:
    """Context manager for enforcing mutation authorization around a block."""

    def __init__(
        self,
        command: str,
        resource_id: str | None = None,
        adapter=None,
    ) -> None:
        self.command = command
        self.resource_id = resource_id
        self.adapter = adapter
        self._result: EnforcementResult | None = None

    def __enter__(self) -> MutationContext:
        if self.adapter is None:
            from phlo.cli.authorization import get_cli_adapter

            self.adapter = get_cli_adapter()

        self._result = self.adapter.enforce_mutation(self.command, self.resource_id)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    @property
    def result(self) -> EnforcementResult | None:
        return self._result

    def is_allowed(self) -> bool:
        return self._result is not None and self._result.allowed


def enforce_mutation_context(
    command: str,
    resource_id: str | None = None,
) -> MutationContext:
    """Create a mutation context for use in a with statement.

    Args:
        command: Command path (e.g., "services.start")
        resource_id: Optional resource identifier

    Returns:
        MutationContext that can be used in a with statement

    Example:
        from phlo.cli.authorization import enforce_mutation_context

        def stop_service(service_name: str):
            with enforce_mutation_context("services.stop", resource_id=service_name) as ctx:
                if not ctx.is_allowed():
                    raise PermissionError("Not authorized")
                # perform stop
    """
    return MutationContext(command=command, resource_id=resource_id)


def emit_cli_audit_event(
    command: str,
    decision: str,
    subject: str,
    resource_type: str,
    resource_id: str,
    reason_code: str | None = None,
) -> None:
    """Emit a CLI-specific audit event for command execution.

    This is called by command wrappers after authorization decisions
    to emit audit events that capture CLI-specific context.

    Args:
        command: Full command path
        decision: "allowed" or "denied"
        subject: Principal subject
        resource_type: Type of resource affected
        resource_id: Specific resource identifier
        reason_code: Optional denial reason code
    """
    try:
        ctx = EnforcementContext.get_instance()
        ctx.audit_emitter.emit_authorization(
            surface="phlo-cli",
            action=f"cli.{command}",
            resource_type=resource_type,
            resource_id=resource_id,
            actor_subject=subject,
            actor_type="user",
            actor_roles=(),
            authentication_source=os.environ.get("PHLO_AUTH_TYPE", "unknown"),
            decision=decision,
            reason_code=reason_code or "",
            policy_id=None,
            request_id=os.environ.get("PHLO_REQUEST_ID"),
        )
    except Exception:
        logger.exception("cli_audit_event_emission_failed")


def check_cli_surface_active() -> bool:
    """Check if the CLI surface is active and regulated mode is enabled."""
    try:
        from phlo.security.mode import is_regulated

        return is_regulated()
    except Exception:
        return False

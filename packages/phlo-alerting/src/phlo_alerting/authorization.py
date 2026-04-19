"""Alerting regulated surface adapter.

This module provides the regulated surface adapter for the alerting CLI commands,
declaring which operations are mutations vs reads.

Alerting commands are all read-only operations (test, list, status) that do not
modify system state. They query configured destinations and display status.

Principal resolution strategy:
- Inherits from CLI principal resolver (see phlo.cli.authorization)

Read commands (no authorization required):
- alerts.test: Send test alert to configured destinations
- alerts.list: List configured alert destinations
- alerts.status: Show alert system status

Mutation commands: none - all alerting commands are reads.
"""

from __future__ import annotations

from typing import Any

from phlo.security.adapters import (
    EnforcementResult,
    SurfaceOperation,
)

SURFACE_NAME = "phlo-alerting"
FRAMEWORK_TYPE = "cli"

READ_COMMANDS: frozenset[str] = frozenset(
    {
        "alerts.test",
        "alerts.list",
        "alerts.status",
    }
)


class AlertingSurfaceAdapter:
    """Regulated surface adapter for Phlo alerting CLI.

    All alerting commands are read-only operations that query
    configured destinations without modifying system state.
    """

    _instance: "AlertingSurfaceAdapter | None" = None

    def __init__(self) -> None:
        pass

    @classmethod
    def get_instance(cls) -> "AlertingSurfaceAdapter":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def surface_name(self) -> str:
        return SURFACE_NAME

    @property
    def framework_type(self) -> str:
        return FRAMEWORK_TYPE

    def list_operations(self) -> list[SurfaceOperation]:
        return []

    def is_active(self, runtime: Any) -> bool:
        return True

    def install(self, runtime: Any) -> None:
        pass

    def check_command_authorization(self, command: str) -> EnforcementResult:
        if command in READ_COMMANDS:
            return EnforcementResult.allow()

        return EnforcementResult.deny(
            reason_code="unknown_command",
            explanation=f"Command '{command}' is not classified for alerting CLI",
        )


def get_alerting_adapter() -> AlertingSurfaceAdapter:
    return AlertingSurfaceAdapter.get_instance()

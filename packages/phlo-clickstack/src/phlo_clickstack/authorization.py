"""Regulated surface adapter for ClickStack CLI.

This module provides the regulated surface adapter for the ClickStack CLI,
declaring mutation commands that require authorization and enforcing
through core enforcement.

Mutation commands (require authorization):
- clickstack.query

Read commands (no authorization):
- (none currently)
"""

from __future__ import annotations

import os
import threading
from typing import Any

from phlo.cli.authorization import CliPrincipalResolver
from phlo.logging import get_logger
from phlo.security.adapters import (
    EnforcementResult,
    SurfaceOperation,
)
from phlo.security.enforcement import enforce

logger = get_logger(__name__)

SURFACE_NAME = "phlo-clickstack"
FRAMEWORK_TYPE = "cli"

MUTATION_COMMANDS: frozenset[str] = frozenset(
    {
        "clickstack.query",
    }
)

READ_COMMANDS: frozenset[str] = frozenset()

COMMAND_RESOURCE_MAP: dict[str, str] = {
    "clickstack.query": "dataset",
}

COMMAND_ACTION_MAP: dict[str, str] = {
    "clickstack.query": "dataset.write",
}


class ClickStackSurfaceAdapter:
    """Regulated surface adapter for ClickStack CLI.

    Declares mutation commands and enforces authorization through core
    enforcement for privileged operations.
    """

    _instance: ClickStackSurfaceAdapter | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._resolver = CliPrincipalResolver()

    @classmethod
    def get_instance(cls) -> ClickStackSurfaceAdapter:
        if cls._instance is None:
            with cls._lock:
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
        operations: list[SurfaceOperation] = []
        for command in MUTATION_COMMANDS:
            resource_type = COMMAND_RESOURCE_MAP.get(command, "dataset")
            action = COMMAND_ACTION_MAP.get(command, f"clickstack.{command}")
            operations.append(
                SurfaceOperation(
                    action=action,
                    resource_type=resource_type,
                    operation_name=command,
                    resource_id_strategy=None,
                    framework_metadata={"command": command},
                )
            )
        return operations

    def is_active(self, runtime: Any) -> bool:
        return True

    def install(self, runtime: Any) -> None:
        pass

    def enforce_mutation(self, command: str, resource_id: str | None = None) -> EnforcementResult:
        """Enforce authorization for a mutation command."""
        if command not in MUTATION_COMMANDS:
            return EnforcementResult.allow()

        action = COMMAND_ACTION_MAP.get(command, f"clickstack.{command}")
        resource_type = COMMAND_RESOURCE_MAP.get(command, "dataset")
        resource_id_final = resource_id or f"clickstack:{command}"

        principal = self._resolver.resolve()

        from phlo.capabilities.interfaces import ResourceRef

        resource = ResourceRef(
            resource_type=resource_type,
            resource_id=resource_id_final,
        )

        request_id = os.environ.get("PHLO_REQUEST_ID")

        result = enforce(
            principal=principal,
            action=action,
            resource=resource,
            context=None,
            request_id=request_id,
            surface=SURFACE_NAME,
        )

        logger.debug(
            "clickstack_mutation_enforcement_result",
            command=command,
            action=action,
            result=result.variant,
            subject=principal.subject,
        )

        return result

    def check_command_authorization(self, command_path: str) -> EnforcementResult:
        """Check if a command is authorized to run."""
        if command_path in READ_COMMANDS:
            return EnforcementResult.allow()

        if command_path in MUTATION_COMMANDS:
            return self.enforce_mutation(command_path)

        logger.warning(
            "clickstack_unknown_command_classification",
            command=command_path,
        )
        return EnforcementResult.deny(
            reason_code="unknown_command",
            explanation=f"Command '{command_path}' is not classified as read or mutation",
        )


_adapter: ClickStackSurfaceAdapter | None = None


def get_adapter() -> ClickStackSurfaceAdapter:
    """Get the singleton ClickStack surface adapter."""
    global _adapter
    if _adapter is None:
        _adapter = ClickStackSurfaceAdapter()
    return _adapter

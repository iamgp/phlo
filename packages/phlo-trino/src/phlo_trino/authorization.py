"""CLI regulated surface adapter for Trino.

This module provides the regulated surface adapter for the Trino CLI,
declaring mutation commands that require authorization and enforcing
through core enforcement.

Commands:
- trino query: Execute SQL queries (mutation - can be SELECT or DDL/DML)
- trino: Raw trino CLI passthrough (mutation - interactive shell)

Resource/Action mapping:
- dataset.query: Trino SQL execution
"""

from __future__ import annotations

import os
import threading
from typing import TYPE_CHECKING, Any

from phlo.logging import get_logger
from phlo.security.adapters import (
    EnforcementResult,
    SurfaceOperation,
)
from phlo.security.enforcement import enforce

if TYPE_CHECKING:
    from phlo.capabilities.interfaces import AuthPrincipal

logger = get_logger(__name__)

SURFACE_NAME = "phlo-trino-cli"
FRAMEWORK_TYPE = "cli"

MUTATION_COMMANDS: frozenset[str] = frozenset(
    {
        "trino.query",
        "trino",
    }
)

READ_COMMANDS: frozenset[str] = frozenset({})

COMMAND_RESOURCE_MAP: dict[str, str] = {
    "trino.query": "dataset",
    "trino": "dataset",
}

COMMAND_ACTION_MAP: dict[str, str] = {
    "trino.query": "dataset.query",
    "trino": "dataset.query",
}


class TrinoCliPrincipalResolver:
    """Resolves CLI principal from execution environment.

    Uses same strategy as core CLI adapter.
    """

    @staticmethod
    def resolve() -> AuthPrincipal:
        """Resolve AuthPrincipal from environment."""
        from phlo.capabilities.interfaces import AuthPrincipal

        service_account = os.environ.get("PHLO_SERVICE_ACCOUNT")
        if service_account:
            return AuthPrincipal(
                subject=service_account,
                principal_type="service",
                issuer="env:PHLO_SERVICE_ACCOUNT",
                groups=("operators",),
                attributes={"authentication_source": "service_account"},
            )

        subject = os.environ.get("PHLO_AUTH_SUBJECT")
        auth_type = os.environ.get("PHLO_AUTH_TYPE", "user")
        groups_raw = os.environ.get("PHLO_AUTH_GROUPS", "")

        if subject:
            groups = (
                tuple(g.strip() for g in groups_raw.split(",") if g.strip()) if groups_raw else ()
            )
            return AuthPrincipal(
                subject=subject,
                principal_type=auth_type,
                issuer="env:PHLO_AUTH_*",
                groups=groups,
                attributes={"authentication_source": "env"},
            )

        local_dev_fallback = os.environ.get("PHLO_DEV_MODE")
        if local_dev_fallback:
            logger.warning(
                "trino_cli_authorization_dev_fallback",
                message="Using dev fallback principal. Set PHLO_AUTH_SUBJECT for regulated mode.",
            )
            return AuthPrincipal(
                subject="local:root",
                principal_type="user",
                issuer="dev:PHLO_DEV_MODE",
                groups=("admin",),
                attributes={"authentication_source": "dev_fallback"},
            )

        return AuthPrincipal(
            subject="anonymous",
            principal_type="user",
            issuer="cli:default",
            groups=(),
            attributes={"authentication_source": "default"},
        )


class TrinoCliSurfaceAdapter:
    """Regulated surface adapter for Trino CLI.

    Declares mutation commands and enforces authorization through core
    enforcement for privileged operations.
    """

    _instance: TrinoCliSurfaceAdapter | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._resolver = TrinoCliPrincipalResolver()

    @classmethod
    def get_instance(cls) -> TrinoCliSurfaceAdapter:
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
            action = COMMAND_ACTION_MAP.get(command, "dataset.query")
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

        action = COMMAND_ACTION_MAP.get(command, "dataset.query")
        resource_type = COMMAND_RESOURCE_MAP.get(command, "dataset")
        resource_id_final = resource_id or f"trino:{command}"

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
            "trino_cli_mutation_enforcement_result",
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
            "trino_cli_unknown_command_classification",
            command=command_path,
        )
        return EnforcementResult.deny(
            reason_code="unknown_command",
            explanation=f"Command '{command_path}' is not classified as read or mutation",
        )


def get_trino_cli_adapter() -> TrinoCliSurfaceAdapter:
    """Get the singleton Trino CLI surface adapter."""
    return TrinoCliSurfaceAdapter.get_instance()

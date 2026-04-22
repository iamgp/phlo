"""CLI regulated surface adapter for PostgreSQL.

This module provides the regulated surface adapter for the PostgreSQL CLI,
declaring mutation commands that require authorization and enforcing
through core enforcement.

Commands:
- postgres query: Execute SQL (mutation - can be SELECT or DDL/DML)
- postgres dump: Create database dump (mutation)
- postgres restore: Restore from dump (mutation)
- postgres vacuum: Run vacuumdb maintenance (mutation)
- postgres: Raw psql passthrough (mutation)

Resource/Action mapping:
- dataset.query: SQL execution
- dataset.manage: Database maintenance operations
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

SURFACE_NAME = "phlo-postgres-cli"
FRAMEWORK_TYPE = "cli"

MUTATION_COMMANDS: frozenset[str] = frozenset(
    {
        "postgres.query",
        "postgres.dump",
        "postgres.restore",
        "postgres.vacuum",
        "postgres",
    }
)

READ_COMMANDS: frozenset[str] = frozenset({})

COMMAND_RESOURCE_MAP: dict[str, str] = {
    "postgres.query": "dataset",
    "postgres.dump": "dataset",
    "postgres.restore": "dataset",
    "postgres.vacuum": "dataset",
    "postgres": "dataset",
}

COMMAND_ACTION_MAP: dict[str, str] = {
    "postgres.query": "dataset.query",
    "postgres.dump": "dataset.manage",
    "postgres.restore": "dataset.manage",
    "postgres.vacuum": "dataset.manage",
    "postgres": "dataset.query",
}


class PostgresCliSurfaceAdapter:
    """Regulated surface adapter for PostgreSQL CLI."""

    _instance: PostgresCliSurfaceAdapter | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._resolver = CliPrincipalResolver()

    @classmethod
    def get_instance(cls) -> PostgresCliSurfaceAdapter:
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
        resource_id_final = resource_id or f"postgres:{command}"

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
            "postgres_cli_mutation_enforcement_result",
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
            "postgres_cli_unknown_command_classification",
            command=command_path,
        )
        return EnforcementResult.deny(
            reason_code="unknown_command",
            explanation=f"Command '{command_path}' is not classified as read or mutation",
        )


def get_postgres_cli_adapter() -> PostgresCliSurfaceAdapter:
    """Get the singleton PostgreSQL CLI surface adapter."""
    return PostgresCliSurfaceAdapter.get_instance()

"""Surface gating for regulated mode.

Categorizes services by regulatory boundary status:

- APPROVED_SERVICES: fully integrated regulated surfaces
- APPROVED_CLI_PACKAGES: approved CLI plugin packages with authorization adapters
- INGRESS_OPTIONAL_SERVICES: optional surfaces protected by ingress + upstream APIs
  (hasura, postgrest, superset: use their own permission models, require ingress protection)
- UNSUPPORTED_SERVICES: blocked surfaces not suitable for regulated deployments
- PENDING_ADAPTER_SERVICES: surfaces with adapters awaiting approval (currently empty)

CLI Plugin Packages (APPROVED_CLI_PACKAGES):
- phlo-alerting: alerting CLI (all read commands, no adapter needed)
- phlo-lineage: lineage CLI (has mutation: lineage.column.import-dbt)
- phlo-dlt: DLT CLI (has mutation: workflow.create)
- phlo-dbt: dbt CLI (has mutations: dbt.run, dbt.publishing.scaffold)
- phlo-pandera: Pandera CLI (all read commands, no adapter needed)

UI Surface Classifications (Phase 3):

- observatory: approved, inside regulated boundary via ingress + phlo-api
- superset: ingress_optional, requires ingress/IdP integration for regulated deployments
- pgweb: unsupported, blocked due to direct Postgres access without Phlo auth mediation
"""

from __future__ import annotations

from typing import Any

from phlo.logging import get_logger
from phlo.security.mode import is_regulated

logger = get_logger(__name__)

UNSUPPORTED_SERVICES: frozenset[str] = frozenset(
    {
        "pgweb",
        "openmetadata",
        "openmetadata-server",
        "openmetadata-ingestion",
    }
)

APPROVED_CLI_PACKAGES: frozenset[str] = frozenset(
    {
        "phlo-alerting",
        "phlo-lineage",
        "phlo-dlt",
        "phlo-dbt",
        "phlo-pandera",
        "phlo-clickhouse",
        "phlo-clickstack",
        "phlo-sling",
    }
)

PENDING_ADAPTER_SERVICES: frozenset[str] = frozenset()

INGRESS_OPTIONAL_SERVICES: frozenset[str] = frozenset(
    {
        "superset",
        "hasura",
        "postgrest",
    }
)

APPROVED_SERVICES: frozenset[str] = frozenset(
    {
        "phlo-api",
        "cli",
        "dagster-webserver",
        "dagster-daemon",
        "postgres",
        "minio",
        "minio-setup",
        "nessie",
        "trino",
        "observatory",
        "prometheus",
        "grafana",
        "loki",
        "alloy",
        "clickhouse",
        "clickhouse-setup",
        "phlo-trino-cli",
        "phlo-nessie-cli",
        "phlo-minio-cli",
        "phlo-postgres-cli",
    }
)


class UnsupportedSurfaceError(Exception):
    """Raised when an unsupported surface is accessed in regulated mode."""

    def __init__(self, surface: str, reason: str) -> None:
        self.surface = surface
        self.reason = reason
        super().__init__(f"Unsupported surface '{surface}' in regulated mode: {reason}")


def check_service_allowed(service_name: str, regulated: bool | None = None) -> None:
    """Check if a service is allowed in regulated mode."""
    if regulated is None:
        regulated = is_regulated()

    if not regulated:
        return

    normalized = service_name.lower().replace("_", "-").replace(" ", "-")

    if normalized in UNSUPPORTED_SERVICES:
        raise UnsupportedSurfaceError(
            surface=service_name,
            reason=f"'{service_name}' is not an approved regulated entry point. "
            "Use phlo-api or approved CLI paths instead.",
        )

    if normalized in PENDING_ADAPTER_SERVICES:
        raise UnsupportedSurfaceError(
            surface=service_name,
            reason=f"'{service_name}' adapter is pending approval. "
            "Direct access is forbidden until the adapter is approved.",
        )

    if normalized in INGRESS_OPTIONAL_SERVICES:
        logger.warning(
            "ingress_optional_service_in_regulated_mode",
            service=service_name,
            note="ingress protection and upstream auth required",
        )
        return

    if normalized in APPROVED_CLI_PACKAGES:
        return

    if normalized not in APPROVED_SERVICES:
        logger.warning(
            "unknown_service_in_regulated_mode",
            service=service_name,
            approved=sorted(APPROVED_SERVICES),
        )


def is_service_allowed(service_name: str, regulated: bool | None = None) -> bool:
    """Check if a service is allowed without raising."""
    try:
        check_service_allowed(service_name, regulated)
        return True
    except UnsupportedSurfaceError:
        return False


def get_blocked_services() -> list[str]:
    """Return sorted list of blocked service names."""
    return sorted(UNSUPPORTED_SERVICES | PENDING_ADAPTER_SERVICES)


def get_ingress_optional_services() -> list[str]:
    """Return sorted list of ingress-optional service names."""
    return sorted(INGRESS_OPTIONAL_SERVICES)


def get_approved_services() -> list[str]:
    """Return sorted list of approved service names."""
    return sorted(APPROVED_SERVICES)


def get_approved_cli_packages() -> list[str]:
    """Return sorted list of approved CLI plugin packages."""
    return sorted(APPROVED_CLI_PACKAGES)


def check_cli_package_allowed(package_name: str, regulated: bool | None = None) -> None:
    """Check if a CLI plugin package is allowed in regulated mode.

    CLI plugin packages (phlo-alerting, phlo-lineage, etc.) are authorized
    through their own regulated surface adapters. This function checks if
    the package is in the approved list.

    Args:
        package_name: Name of the CLI package (e.g., "phlo-alerting").
        regulated: Whether regulated mode is active.

    Raises:
        UnsupportedSurfaceError: If the package is not approved.
    """
    if regulated is None:
        regulated = is_regulated()

    if not regulated:
        return

    normalized = package_name.lower().replace("_", "-").replace(" ", "-")

    if normalized not in APPROVED_CLI_PACKAGES:
        raise UnsupportedSurfaceError(
            surface=package_name,
            reason=f"'{package_name}' is not an approved CLI package. "
            "Use only approved CLI plugin packages in regulated mode.",
        )


def is_cli_package_allowed(package_name: str, regulated: bool | None = None) -> bool:
    """Check if a CLI plugin package is allowed without raising."""
    try:
        check_cli_package_allowed(package_name, regulated)
        return True
    except UnsupportedSurfaceError:
        return False


def validate_service_selection(
    services: list[str],
    regulated: bool | None = None,
) -> dict[str, Any]:
    """Validate a selection of services for regulated mode."""
    if regulated is None:
        regulated = is_regulated()

    result: dict[str, Any] = {
        "allowed": [],
        "blocked": [],
        "unknown": [],
        "ingress_optional": [],
        "regulated": regulated,
    }

    for service in services:
        normalized = service.lower().replace("_", "-").replace(" ", "-")

        if normalized in UNSUPPORTED_SERVICES:
            result["blocked"].append(
                {"service": service, "reason": "Not an approved regulated entry point"}
            )
        elif normalized in PENDING_ADAPTER_SERVICES:
            result["blocked"].append({"service": service, "reason": "Adapter pending approval"})
        elif normalized in INGRESS_OPTIONAL_SERVICES:
            result["ingress_optional"].append(
                {"service": service, "reason": "Ingress protection required"}
            )
            result["allowed"].append(service)
        elif normalized in APPROVED_CLI_PACKAGES:
            result["allowed"].append(service)
        elif normalized not in APPROVED_SERVICES:
            result["unknown"].append(service)
            result["allowed"].append(service)
        else:
            result["allowed"].append(service)

    return result


def block_direct_dagster_access(
    request_source: str | None = None,
    regulated: bool | None = None,
) -> None:
    """Block direct Dagster access when adapter is not properly installed.

    This function is kept for backward compatibility but is a no-op
    since dagster-webserver now has a regulated surface adapter (Units 2 and 3 completed).
    The adapter enforces authorization at the GraphQL operation level.
    """
    if regulated is None:
        regulated = is_regulated()

    if not regulated:
        return

    logger.debug(
        "dagster_adapter_installed",
        message="Dagster regulated surface adapter is installed, direct blocking bypassed",
    )

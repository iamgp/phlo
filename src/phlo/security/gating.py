"""Surface gating for regulated mode.

Blocks unsupported surfaces in regulated mode deployments.

Unsupported surfaces (per spec):
    - pgweb
    - Superset
    - OpenMetadata UI
    - raw third-party consoles
    - direct Dagster access (until adapter is approved)
"""

from __future__ import annotations

from typing import Any

from phlo.logging import get_logger
from phlo.security.mode import is_regulated_mode_enabled

logger = get_logger(__name__)

UNSUPPORTED_SERVICES: frozenset[str] = frozenset(
    {
        "pgweb",
        "superset",
        "openmetadata",
        "openmetadata-server",
        "openmetadata-ingestion",
    }
)

PENDING_ADAPTER_SERVICES: frozenset[str] = frozenset(
    {
        "dagster-webserver",
        "dagster-daemon",
        "cli",
    }
)

APPROVED_SERVICES: frozenset[str] = frozenset(
    {
        "phlo-api",
        "postgres",
        "minio",
        "minio-setup",
        "nessie",
        "trino",
        "hasura",
        "postgrest",
        "observatory",
        "prometheus",
        "grafana",
        "loki",
        "alloy",
        "clickhouse",
        "clickhouse-setup",
    }
)


class UnsupportedSurfaceError(Exception):
    """Raised when an unsupported surface is accessed in regulated mode."""

    def __init__(self, surface: str, reason: str) -> None:
        self.surface = surface
        self.reason = reason
        super().__init__(f"Unsupported surface '{surface}' in regulated mode: {reason}")


def check_service_allowed(service_name: str, regulated_mode: bool | None = None) -> None:
    """Check if a service is allowed in regulated mode."""
    if regulated_mode is None:
        regulated_mode = is_regulated_mode_enabled()

    if not regulated_mode:
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

    if normalized not in APPROVED_SERVICES:
        logger.warning(
            "unknown_service_in_regulated_mode",
            service=service_name,
            approved=sorted(APPROVED_SERVICES),
        )


def is_service_allowed(service_name: str, regulated_mode: bool | None = None) -> bool:
    """Check if a service is allowed without raising."""
    try:
        check_service_allowed(service_name, regulated_mode)
        return True
    except UnsupportedSurfaceError:
        return False


def get_blocked_services() -> list[str]:
    """Return sorted list of blocked service names."""
    return sorted(UNSUPPORTED_SERVICES | PENDING_ADAPTER_SERVICES)


def get_approved_services() -> list[str]:
    """Return sorted list of approved service names."""
    return sorted(APPROVED_SERVICES)


def validate_service_selection(
    services: list[str],
    regulated_mode: bool | None = None,
) -> dict[str, Any]:
    """Validate a selection of services for regulated mode."""
    if regulated_mode is None:
        regulated_mode = is_regulated_mode_enabled()

    result: dict[str, Any] = {
        "allowed": [],
        "blocked": [],
        "unknown": [],
        "regulated_mode": regulated_mode,
    }

    for service in services:
        normalized = service.lower().replace("_", "-").replace(" ", "-")

        if normalized in UNSUPPORTED_SERVICES:
            result["blocked"].append(
                {"service": service, "reason": "Not an approved regulated entry point"}
            )
        elif normalized in PENDING_ADAPTER_SERVICES:
            result["blocked"].append({"service": service, "reason": "Adapter pending approval"})
        elif normalized not in APPROVED_SERVICES:
            result["unknown"].append(service)
            result["allowed"].append(service)
        else:
            result["allowed"].append(service)

    return result


def block_direct_dagster_access(
    request_source: str | None = None,
    regulated_mode: bool | None = None,
) -> None:
    """Block direct Dagster access in regulated mode."""
    if regulated_mode is None:
        regulated_mode = is_regulated_mode_enabled()

    if not regulated_mode:
        return

    raise UnsupportedSurfaceError(
        surface="dagster-webserver",
        reason=(
            "Direct Dagster access is forbidden in regulated mode. "
            "Use the phlo-api Dagster endpoints or approved CLI commands. "
            "The Dagster authorization adapter is pending approval."
        ),
    )

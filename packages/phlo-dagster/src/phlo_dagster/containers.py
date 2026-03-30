"""Docker container discovery for Dagster services.

This module provides utilities for finding and managing Dagster-related
Docker containers within a Docker Compose environment. It handles
candidate container name generation and resolution across different
naming conventions.

Naming Conventions:
    - Legacy: {project_name}-dagster-webserver-1
    - New: {project_name}-dagster-1
    - Configured: From infrastructure settings

The module attempts resolution in order: configured → new → legacy,
falling back through available patterns until a running container is found.

Example:
    Finding the Dagster container::

        from phlo_dagster.containers import find_dagster_container

        container_name = find_dagster_container("my_project")
        # Returns: "my_project-dagster-1" or similar

"""

import re
from dataclasses import dataclass

from phlo.infrastructure import (
    find_service_container,
    list_running_containers,
    resolve_container_name,
)
from phlo.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class DagsterContainerCandidates:
    """Candidate Dagster webserver container names.

    Attributes:
        configured: Name resolved from infrastructure config.
        new: Current compose naming pattern candidate.
        legacy: Legacy compose naming pattern candidate.

    """

    configured: str
    new: str
    legacy: str


def dagster_container_candidates(
    project_name: str, configured_name: str | None
) -> DagsterContainerCandidates:
    """Build candidate container names for a project.

    Args:
        project_name: Compose project name.
        configured_name: Optional configured container name override.

    Returns:
        Ordered candidate names for Dagster webserver discovery.

    """

    configured = configured_name or ""
    new = f"{project_name}-dagster-1"
    legacy = f"{project_name}-dagster-webserver-1"
    return DagsterContainerCandidates(configured=configured, new=new, legacy=legacy)


def _resolve_container_name(service_name: str, project_name: str) -> str:
    """Resolve container name for a service from infrastructure settings.

    Args:
        service_name: Service identifier in infrastructure config.
        project_name: Compose project name.

    Returns:
        Configured or derived container name for the service.

    """

    return resolve_container_name(service_name, project_name)


def _list_running_containers(project_name: str) -> list[str]:
    """List running compose container names for a project.

    Args:
        project_name: Compose project name.

    Returns:
        List of running container names.

    """
    return list_running_containers(project_name)


def find_dagster_container(project_name: str) -> str:
    """Find the running Dagster webserver container for a project.

    Args:
        project_name: Compose project name.

    Returns:
        Selected Dagster container name.

    Raises:
        RuntimeError: If no matching Dagster webserver container is running.

    """

    logger.info(
        "dagster_container_lookup_started",
        project_name=project_name,
    )
    try:
        chosen = find_service_container(
            project_name=project_name,
            service_name="dagster",
            legacy_names=(f"{project_name}-dagster-webserver-1",),
            include_pattern=rf"{re.escape(project_name)}.*dagster",
            exclude_substrings=("daemon",),
        )
        logger.info(
            "dagster_container_lookup_completed",
            project_name=project_name,
            selected_container=chosen,
        )
        return chosen
    except Exception as exc:
        logger.error(
            "dagster_container_lookup_failed",
            project_name=project_name,
            error=str(exc),
            exc_info=True,
        )
        raise

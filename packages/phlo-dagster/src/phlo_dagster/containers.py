from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass

from phlo.infrastructure import load_infrastructure_config
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


def select_first_existing(candidates: list[str], existing: list[str]) -> str | None:
    """Return the first candidate present in the existing container list.

    Args:
        candidates: Candidate container names in priority order.
        existing: Existing running container names.

    Returns:
        First matching candidate, or ``None`` when no match exists.
    """

    existing_set = set(existing)
    for candidate in candidates:
        if candidate and candidate in existing_set:
            return candidate
    return None


def _resolve_container_name(service_name: str, project_name: str) -> str:
    """Resolve container name for a service from infrastructure settings.

    Args:
        service_name: Service identifier in infrastructure config.
        project_name: Compose project name.

    Returns:
        Configured or derived container name for the service.
    """

    infra = load_infrastructure_config()
    configured = infra.get_container_name(service_name, project_name)
    if configured:
        return configured
    return infra.container_naming_pattern.format(project=project_name, service=service_name)


def _list_running_containers(project_name: str) -> list[str]:
    """List running compose container names for a project.

    Args:
        project_name: Compose project name.

    Returns:
        Running container names reported by Docker.
    """

    result = subprocess.run(
        [
            "docker",
            "ps",
            "--filter",
            f"label=com.docker.compose.project={project_name}",
            "--format",
            "{{.Names}}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.splitlines() if result.stdout else []


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
        configured_name = _resolve_container_name("dagster", project_name)
        candidates = dagster_container_candidates(project_name, configured_name)
        preferred = [candidates.configured, candidates.new, candidates.legacy]

        existing = _list_running_containers(project_name)
        chosen = select_first_existing(preferred, existing)
        if chosen:
            logger.info(
                "dagster_container_lookup_completed",
                project_name=project_name,
                selected_container=chosen,
                container_source="preferred_candidate",
                running_container_count=len(existing),
            )
            return chosen

        fallback_matches = [
            name
            for name in existing
            if re.search(rf"{re.escape(project_name)}.*dagster", name) and "daemon" not in name
        ]
        if fallback_matches:
            logger.info(
                "dagster_container_lookup_completed",
                project_name=project_name,
                selected_container=fallback_matches[0],
                container_source="fallback_match",
                running_container_count=len(existing),
            )
            return fallback_matches[0]

        error_message = (
            f"Could not find running Dagster webserver container for project '{project_name}'. "
            f"Expected container name: {candidates.new} or {candidates.legacy}"
        )
        raise RuntimeError(error_message)
    except Exception as exc:
        logger.error(
            "dagster_container_lookup_failed",
            project_name=project_name,
            error=str(exc),
            exc_info=True,
        )
        raise

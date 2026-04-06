"""Core helpers for resolving running service containers."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Iterable

from phlo.infrastructure.config import load_infrastructure_config
from phlo.logging import get_logger

logger = get_logger(__name__)


def resolve_container_name(service_name: str, project_name: str) -> str:
    """Resolve container name for a service from infrastructure settings."""
    infra = load_infrastructure_config()
    configured = infra.get_container_name(service_name, project_name)
    if configured:
        return configured
    return infra.container_naming_pattern.format(project=project_name, service=service_name)


def list_running_containers(project_name: str) -> list[str]:
    """List running compose container names for a project."""
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
    if result.returncode != 0:
        logger.warning(
            "docker_list_containers_failed",
            project=project_name,
            returncode=result.returncode,
            stderr=result.stderr.strip() if result.stderr else "",
        )
        return []
    return result.stdout.splitlines() if result.stdout else []


def select_first_existing(candidates: Iterable[str], existing: Iterable[str]) -> str | None:
    """Return the first candidate present in the existing container list."""
    existing_set = set(existing)
    for candidate in candidates:
        if candidate and candidate in existing_set:
            return candidate
    return None


def find_service_container(
    *,
    project_name: str,
    service_name: str,
    legacy_names: Iterable[str] = (),
    include_pattern: str | None = None,
    exclude_substrings: Iterable[str] = (),
) -> str:
    """Find a running service container for a compose project."""
    configured_name = resolve_container_name(service_name, project_name)
    default_name = f"{project_name}-{service_name}-1"
    preferred = [configured_name, default_name, *legacy_names]

    existing = list_running_containers(project_name)
    chosen = select_first_existing(preferred, existing)
    if chosen:
        return chosen

    pattern = include_pattern or rf"{re.escape(project_name)}.*{re.escape(service_name)}"
    for name in existing:
        if not re.search(pattern, name):
            continue
        if any(excluded in name for excluded in exclude_substrings):
            continue
        return name

    legacy_list = [name for name in legacy_names if name]
    expected = [default_name, *legacy_list]
    expected_rendered = " or ".join(expected) if expected else default_name
    raise RuntimeError(
        f"Could not find running {service_name} container for project '{project_name}'. "
        f"Expected container name: {expected_rendered}"
    )

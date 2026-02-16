from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass

from phlo.infrastructure import load_infrastructure_config


@dataclass(frozen=True, slots=True)
class DagsterContainerCandidates:
    configured: str
    new: str
    legacy: str


def dagster_container_candidates(
    project_name: str, configured_name: str | None
) -> DagsterContainerCandidates:
    configured = configured_name or ""
    new = f"{project_name}-dagster-1"
    legacy = f"{project_name}-dagster-webserver-1"
    return DagsterContainerCandidates(configured=configured, new=new, legacy=legacy)


def select_first_existing(candidates: list[str], existing: list[str]) -> str | None:
    existing_set = set(existing)
    for candidate in candidates:
        if candidate and candidate in existing_set:
            return candidate
    return None


def _resolve_container_name(service_name: str, project_name: str) -> str:
    infra = load_infrastructure_config()
    configured = infra.get_container_name(service_name, project_name)
    if configured:
        return configured
    return infra.container_naming_pattern.format(project=project_name, service=service_name)


def _list_running_containers(project_name: str) -> list[str]:
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
    configured_name = _resolve_container_name("dagster", project_name)
    candidates = dagster_container_candidates(project_name, configured_name)
    preferred = [candidates.configured, candidates.new, candidates.legacy]

    existing = _list_running_containers(project_name)
    chosen = select_first_existing(preferred, existing)
    if chosen:
        return chosen

    fallback_matches = [
        name
        for name in existing
        if re.search(rf"{re.escape(project_name)}.*dagster", name) and "daemon" not in name
    ]
    if fallback_matches:
        return fallback_matches[0]

    raise RuntimeError(
        f"Could not find running Dagster webserver container for project '{project_name}'. "
        f"Expected container name: {candidates.new} or {candidates.legacy}"
    )

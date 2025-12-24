"""Utility functions for CLI services that can be safely imported by plugins."""

import re
from pathlib import Path

import yaml

from phlo.cli._services.command import run_command
from phlo.cli._services.containers import dagster_container_candidates, select_first_existing


def get_project_config() -> dict:
    """Load phlo.yaml configuration."""
    config_path = Path.cwd() / "phlo.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}

    return {
        "name": Path.cwd().name.lower().replace(" ", "-").replace("_", "-"),
        "description": "Phlo data lakehouse",
    }


def get_project_name() -> str:
    """Get the project name for Docker Compose."""
    config = get_project_config()
    return config.get("name", Path.cwd().name.lower().replace(" ", "-").replace("_", "-"))


def _resolve_container_name(service_name: str, project_name: str) -> str:
    """Resolve a service's container name using infra config or default pattern."""
    from phlo.infrastructure import load_infrastructure_config

    infra = load_infrastructure_config()
    configured = infra.get_container_name(service_name, project_name)
    if configured:
        return configured
    return infra.container_naming_pattern.format(project=project_name, service=service_name)


def find_dagster_container(project_name: str) -> str:
    """Find the running Dagster webserver container for the project."""
    configured_name = _resolve_container_name("dagster", project_name)
    candidates = dagster_container_candidates(project_name, configured_name)
    preferred = [candidates.configured, candidates.new, candidates.legacy]

    existing = run_command(["docker", "ps", "--format", "{{.Names}}"]).stdout.splitlines()
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

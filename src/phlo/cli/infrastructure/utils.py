"""Utility functions for CLI services that can be safely imported by plugins."""

from collections.abc import Mapping
from pathlib import Path

import yaml

from phlo.logging import get_logger

logger = get_logger(__name__)


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a .env file into a dict of key=value pairs."""
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    try:
        for line in path.read_text().splitlines():
            trimmed = line.strip()
            if not trimmed or trimmed.startswith("#") or "=" not in trimmed:
                continue
            key, value = trimmed.split("=", 1)
            values[key] = value
    except OSError:
        logger.warning("env_file_read_failed", path=str(path), exc_info=True)
        return {}
    return values


def get_project_config() -> dict:
    """Load phlo.yaml configuration."""
    config_path = Path.cwd() / "phlo.yaml"
    if config_path.exists():
        try:
            with config_path.open() as f:
                config = yaml.safe_load(f) or {}
                if isinstance(config, Mapping):
                    return dict(config)
                logger.warning("project_config_invalid_type", path=str(config_path))
        except (OSError, yaml.YAMLError):
            logger.warning("project_config_load_failed", path=str(config_path), exc_info=True)

    fallback_name = Path.cwd().name.lower().replace(" ", "-").replace("_", "-")
    logger.debug("project_config_fallback_used", project_name=fallback_name)
    return {
        "name": fallback_name,
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

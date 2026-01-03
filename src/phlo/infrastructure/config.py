"""
Infrastructure Configuration Loader

Loads infrastructure configuration from phlo.yaml.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from phlo.config_schema import InfrastructureConfig, ServiceConfig
from phlo.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def load_infrastructure_config(project_root: Optional[Path] = None) -> InfrastructureConfig:
    """Load infrastructure configuration from phlo.yaml."""
    if project_root is None:
        project_root = Path.cwd()

    config_path = project_root / "phlo.yaml"

    if not config_path.exists():
        return InfrastructureConfig()

    try:
        with open(config_path) as f:
            project_config = yaml.safe_load(f)

        if not project_config:
            return InfrastructureConfig()

        infra_config_data = project_config.get("infrastructure", {})

        if not infra_config_data:
            return InfrastructureConfig()

        return InfrastructureConfig(**infra_config_data)

    except (yaml.YAMLError, ValidationError):
        return InfrastructureConfig()


def get_project_name_from_config(project_root: Optional[Path] = None) -> Optional[str]:
    """Get project name from phlo.yaml."""
    if project_root is None:
        project_root = Path.cwd()

    config_path = project_root / "phlo.yaml"

    if not config_path.exists():
        return None

    try:
        with open(config_path) as f:
            project_config = yaml.safe_load(f)
        return project_config.get("name") if project_config else None
    except Exception:
        return None


def get_service_config(
    service_key: str, project_root: Optional[Path] = None
) -> Optional[ServiceConfig]:
    """Get configuration for a specific service."""
    infra = load_infrastructure_config(project_root)
    return infra.get_service(service_key)


def get_container_name(
    service_key: str,
    project_name: str,
    project_root: Optional[Path] = None,
) -> Optional[str]:
    """Get container name for a service."""
    infra = load_infrastructure_config(project_root)
    return infra.get_container_name(service_key, project_name)


def clear_config_cache() -> None:
    """Clear the configuration cache."""
    load_infrastructure_config.cache_clear()

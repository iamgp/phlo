"""
Infrastructure Configuration Loader

Loads infrastructure configuration from phlo.yaml.
"""

from __future__ import annotations

import time
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import ValidationError

from phlo.config_schema import InfrastructureConfig, ServiceConfig
from phlo.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def load_infrastructure_config(project_root: Path | None = None) -> InfrastructureConfig:
    """Load infrastructure configuration from phlo.yaml."""
    started = time.perf_counter()
    if project_root is None:
        project_root = Path.cwd()

    config_path = project_root / "phlo.yaml"
    logger.debug(
        "infrastructure_config_load_started",
        project_root=str(project_root),
        path=str(config_path),
    )

    if not config_path.exists():
        logger.info(
            "infrastructure_config_load_completed",
            source="default",
            reason="missing_file",
            services_count=0,
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
        )
        return InfrastructureConfig()

    try:
        with config_path.open() as f:
            project_config = yaml.safe_load(f)

        if not project_config:
            logger.info(
                "infrastructure_config_load_completed",
                source="default",
                reason="empty_config",
                services_count=0,
                elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
            )
            return InfrastructureConfig()

        infra_config_data = project_config.get("infrastructure", {})

        if not infra_config_data:
            logger.info(
                "infrastructure_config_load_completed",
                source="default",
                reason="missing_infrastructure_section",
                services_count=0,
                elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
            )
            return InfrastructureConfig()
        config = InfrastructureConfig(**infra_config_data)
        logger.info(
            "infrastructure_config_load_completed",
            source="file",
            services_count=len(config.services),
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
        )
        return config

    except yaml.YAMLError as exc:
        logger.error("invalid_phlo_yaml", path=str(config_path), error=str(exc))
        raise
    except ValidationError as exc:
        logger.error("invalid_infrastructure_config", path=str(config_path), error=str(exc))
        raise


def get_project_name_from_config(project_root: Path | None = None) -> str | None:
    """Get project name from phlo.yaml."""
    if project_root is None:
        project_root = Path.cwd()

    config_path = project_root / "phlo.yaml"

    if not config_path.exists():
        return None

    try:
        with config_path.open() as f:
            project_config = yaml.safe_load(f)
        return project_config.get("name") if project_config else None
    except Exception:
        logger.warning("failed_to_read_project_name", path=str(config_path))
        return None


def get_service_config(service_key: str, project_root: Path | None = None) -> ServiceConfig | None:
    """Get configuration for a specific service."""
    infra = load_infrastructure_config(project_root)
    return infra.get_service(service_key)


def get_container_name(
    service_key: str,
    project_name: str,
    project_root: Path | None = None,
) -> str | None:
    """Get container name for a service."""
    infra = load_infrastructure_config(project_root)
    return infra.get_container_name(service_key, project_name)


def clear_config_cache() -> None:
    """Clear the configuration cache."""
    load_infrastructure_config.cache_clear()

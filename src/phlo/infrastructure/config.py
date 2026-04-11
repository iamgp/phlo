"""
Infrastructure Configuration Loader

Loads infrastructure configuration from phlo.yaml.
"""

from __future__ import annotations

import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from phlo.config_schema import (
    ApiAuthorizationConfig,
    ApiConfig,
    InfrastructureConfig,
    ServiceConfig,
)
from phlo.logging import get_logger

logger = get_logger(__name__)


def _default_project_root() -> Path:
    """Resolve the default project root from environment or current working directory."""
    project_root = os.environ.get("PHLO_PROJECT_PATH")
    if project_root:
        raw_path = Path(project_root)
        if ".." in raw_path.parts:
            logger.warning(
                "project_path_traversal_rejected",
                raw=project_root,
                reason="path_traversal_sequence",
            )
            raise ValueError(f"PHLO_PROJECT_PATH contains path traversal: {project_root}")
        return raw_path.resolve()
    return Path.cwd()


@lru_cache(maxsize=16)
def load_project_config(project_root: Path | None = None) -> dict[str, Any]:
    """Load raw project configuration from phlo.yaml."""
    started = time.perf_counter()
    if project_root is None:
        project_root = _default_project_root()

    config_path = project_root / "phlo.yaml"
    logger.debug(
        "project_config_load_started",
        project_root=str(project_root),
        path=str(config_path),
    )

    if not config_path.exists():
        logger.info(
            "project_config_load_completed",
            source="default",
            reason="missing_file",
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
        )
        return {}

    try:
        with config_path.open() as f:
            project_config = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        logger.error("invalid_phlo_yaml", path=str(config_path), error=str(exc))
        raise

    if not isinstance(project_config, dict):
        logger.info(
            "project_config_load_completed",
            source="default",
            reason="empty_or_non_mapping",
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
        )
        return {}

    logger.info(
        "project_config_load_completed",
        source="file",
        key_count=len(project_config),
        elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
    )
    return project_config


@lru_cache(maxsize=16)
def load_infrastructure_config(project_root: Path | None = None) -> InfrastructureConfig:
    """Load infrastructure configuration from phlo.yaml."""
    started = time.perf_counter()
    if project_root is None:
        project_root = _default_project_root()
    logger.debug("infrastructure_config_load_started", project_root=str(project_root))

    try:
        project_config = load_project_config(project_root)
        if not project_config:
            logger.info(
                "infrastructure_config_load_completed",
                source="default",
                reason="missing_project_config",
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

    except ValidationError as exc:
        logger.error(
            "invalid_infrastructure_config",
            path=str(project_root / "phlo.yaml"),
            error=str(exc),
        )
        raise


def get_project_name_from_config(project_root: Path | None = None) -> str | None:
    """Get project name from phlo.yaml."""
    if project_root is None:
        project_root = _default_project_root()

    try:
        project_config = load_project_config(project_root)
        return project_config.get("name") if project_config else None
    except Exception:
        logger.warning("failed_to_read_project_name", path=str(project_root / "phlo.yaml"))
        return None


def get_capability_defaults_from_config(project_root: Path | None = None) -> dict[str, str]:
    """Return capability defaults declared in phlo.yaml."""
    project_config = load_project_config(project_root)
    capabilities = project_config.get("capabilities", {})
    if not isinstance(capabilities, dict):
        return {}

    defaults = capabilities.get("defaults", {})
    if not isinstance(defaults, dict):
        return {}

    normalized: dict[str, str] = {}
    for key, value in defaults.items():
        if isinstance(key, str) and isinstance(value, str) and key and value:
            normalized[key] = value
    return normalized


def get_api_authorization_config(project_root: Path | None = None) -> ApiAuthorizationConfig | None:
    """Return validated phlo-api authorization settings from phlo.yaml.

    Precedence inside phlo.yaml is:
    1. services.phlo-api.authorization
    2. api.authorization
    """
    project_config = load_project_config(project_root)
    if not isinstance(project_config, dict) or not project_config:
        return None

    services = project_config.get("services", {})
    if isinstance(services, dict):
        phlo_api_service = services.get("phlo-api")
        if isinstance(phlo_api_service, dict):
            service_auth = phlo_api_service.get("authorization")
            if isinstance(service_auth, dict):
                return ApiAuthorizationConfig(**service_auth)

    api_config = project_config.get("api")
    if isinstance(api_config, dict):
        validated = ApiConfig(**api_config)
        return validated.authorization

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
    load_project_config.cache_clear()
    load_infrastructure_config.cache_clear()

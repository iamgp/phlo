"""Auto-generate Sling connections from Phlo capability metadata."""

from __future__ import annotations

import os
from collections.abc import MutableMapping
from typing import Any

from phlo.capabilities import list_capabilities, resolve_capability
from phlo.capabilities.discovery import discover_capabilities
from phlo.logging import get_logger
from phlo_sling.settings import get_settings

logger = get_logger(__name__)


def resolve_phlo_connections() -> dict[str, dict[str, Any]]:
    """Build Sling connection definitions from installed Phlo package settings.

    Inspects known Phlo capability providers (phlo-postgres, phlo-minio, etc.)
    and generates Sling-compatible connection dicts.

    Returns:
        Dict mapping connection name to Sling connection config.
    """
    if not get_settings().sling_auto_connections:
        logger.debug("sling_auto_connections_disabled")
        return {}

    connections: dict[str, dict[str, Any]] = {}

    connections.update(_resolve_postgres_connection())
    connections.update(_resolve_s3_connection())

    return connections


def _resolve_postgres_connection() -> dict[str, dict[str, Any]]:
    """Resolve Postgres connection from phlo-postgres settings."""
    try:
        from phlo_postgres.settings import get_settings as get_pg_settings

        pg = get_pg_settings()
        return {
            "PHLO_POSTGRES": {
                "type": "postgres",
                "host": pg.postgres_host,
                "port": pg.postgres_port,
                "database": pg.postgres_db,
                "user": pg.postgres_user,
                "password": pg.postgres_password,
                "schema": getattr(pg, "postgres_schema", "public"),
            }
        }
    except (ImportError, Exception) as exc:
        logger.debug("postgres_connection_skipped", error=str(exc))
        return {}


def _resolve_s3_connection() -> dict[str, dict[str, Any]]:
    """Resolve S3 connection from the active object-store capability."""
    discover_capabilities()
    requested_name = os.environ.get("PHLO_OBJECT_STORE")
    resolution = resolve_capability("object_store", requested_name)
    if resolution is None:
        available = list_capabilities("object_store")
        logger.debug(
            "object_store_connection_skipped",
            requested_name=requested_name,
            available=available,
        )
        return {}

    provider = resolution.provider
    if hasattr(provider, "to_sling_connection"):
        config = provider.to_sling_connection()
    else:
        config = {
            key: value
            for key, value in resolution.metadata.items()
            if key in {"type", "endpoint", "access_key_id", "secret_access_key", "region"}
        }

    if not config:
        logger.debug(
            "object_store_connection_missing_config",
            capability_name=resolution.name,
        )
        return {}

    return {"PHLO_S3": config}


def export_sling_env(connections: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Convert connection dicts to Sling environment variable format.

    Sling expects connections as environment variables with JSON values.

    Args:
        connections: Dict of connection name → connection config.

    Returns:
        Dict of environment variable name → JSON string value.
    """
    import json

    env_vars: dict[str, str] = {}
    for name, config in connections.items():
        env_vars[name] = json.dumps(config)
    return env_vars


def apply_sling_connection_env(environ: MutableMapping[str, str] | None = None) -> dict[str, str]:
    """Inject resolved Sling connections into an environment mapping.

    Existing variables win over auto-generated values.

    Args:
        environ: Environment mapping to mutate. Defaults to ``os.environ``.

    Returns:
        Dict of injected environment variables.
    """
    target_env = os.environ if environ is None else environ
    env_vars = export_sling_env(resolve_phlo_connections())
    for name, value in env_vars.items():
        target_env.setdefault(name, value)
    return env_vars

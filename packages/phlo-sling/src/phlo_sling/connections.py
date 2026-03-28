"""Auto-generate Sling connections from Phlo capability metadata.

This module provides functionality to automatically discover and configure
Sling connections based on installed Phlo package capabilities. It resolves
connections for Postgres, Iceberg, and S3-compatible object stores by inspecting
the configuration of related Phlo packages.

Functions:
    resolve_phlo_connections: Build Sling connection definitions from
        Phlo package settings.
    export_sling_env: Convert connection dicts to Sling environment
        variable format.
    apply_sling_connection_env: Inject resolved connections into the
        environment.
"""

from __future__ import annotations

import os
from collections.abc import MutableMapping
from typing import Any

from phlo.capabilities import list_capabilities, resolve_capability
from phlo.infrastructure.config import load_project_config
from phlo.logging import get_logger
from phlo_sling.settings import get_settings

logger = get_logger(__name__)


def resolve_phlo_connections() -> dict[str, dict[str, Any]]:
    """Build Sling connection definitions from installed Phlo package settings.

    Inspects known Phlo capability providers (phlo-postgres, phlo-minio, etc.)
    and generates Sling-compatible connection dicts. This enables seamless
    integration between Phlo-managed infrastructure and Sling replication
    without manual connection configuration.

    Returns:
        Dict mapping connection name to Sling connection config. Each config
        contains connection-specific parameters like host, port, credentials,
        and endpoint URLs.

    Example:
        Get auto-discovered connections::

            connections = resolve_phlo_connections()
            # {"PHLO_POSTGRES": {"type": "postgres", "host": "...", ...}}

    """
    if not get_settings().sling_auto_connections:
        logger.debug("sling_auto_connections_disabled")
        return {}

    connections: dict[str, dict[str, Any]] = {}

    connections.update(_resolve_postgres_connection())
    connections.update(_resolve_iceberg_connection())
    connections.update(_resolve_s3_connection())

    return connections


def _project_env_value(name: str) -> str | None:
    """Read a non-secret default from phlo.yaml env: when host os.environ lacks it.

    This helper function provides a fallback mechanism for retrieving
    environment variable values from the project configuration file when
    they are not set in the actual environment.

    Args:
        name: The environment variable name to look up.

    Returns:
        The value from phlo.yaml if found and valid, otherwise None.

    """
    try:
        project_config = load_project_config()
    except Exception as exc:
        logger.debug("project_env_lookup_failed", name=name, error=str(exc))
        return None

    env_config = project_config.get("env", {})
    if not isinstance(env_config, dict):
        return None

    value = env_config.get(name)
    return value if isinstance(value, str) and value else None


def _ensure_capabilities_discovered(*kinds: str) -> None:
    """Populate the capability registry only when the requested kinds are absent.

    Lazily discovers capabilities from installed Phlo packages when the
    requested capability kinds are not already registered.

    Args:
        *kinds: Capability type strings to check for and potentially discover.

    Returns:
        None

    """
    if any(list_capabilities(kind) for kind in kinds):
        return

    from phlo.capabilities.discovery import discover_capabilities

    discover_capabilities()


def _get_iceberg_settings():
    """Import phlo-iceberg settings lazily for optional package installs.

    This helper provides lazy importing of phlo-iceberg settings to avoid
    import errors when the package is not installed.

    Returns:
        The phlo-iceberg settings instance.

    Raises:
        ImportError: If phlo-iceberg is not installed.

    """
    from phlo_iceberg.settings import get_settings as get_iceberg_settings

    return get_iceberg_settings()


def _resolve_postgres_connection() -> dict[str, dict[str, Any]]:
    """Resolve Postgres connection from phlo-postgres settings.

    Builds a Sling-compatible connection configuration from the installed
    phlo-postgres package settings if available.

    Returns:
        Dict with "PHLO_POSTGRES" key containing connection configuration,
        or empty dict if phlo-postgres is not installed or configured.

    """
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


def _resolve_iceberg_connection() -> dict[str, dict[str, Any]]:
    """Resolve an Iceberg REST catalog connection from phlo-iceberg settings.

    Builds a Sling-compatible connection configuration for Iceberg REST
    catalog access from the installed phlo-iceberg package settings.

    Returns:
        Dict with "PHLO_ICEBERG" key containing connection configuration,
        or empty dict if phlo-iceberg is not installed or configured.

    """
    try:
        settings = _get_iceberg_settings()
        ref = settings.iceberg_default_ref
        config = settings.get_pyiceberg_catalog_config(ref)
        return {
            "PHLO_ICEBERG": {
                "type": "iceberg",
                "catalog_type": "rest",
                "rest_uri": config["uri"],
                "rest_warehouse": config["warehouse"],
                "s3_endpoint": config["s3.endpoint"],
                "s3_access_key_id": config["s3.access-key-id"],
                "s3_secret_access_key": config["s3.secret-access-key"],
                "s3_region": config["s3.region"],
                "schema": settings.iceberg_default_namespace,
            }
        }
    except (ImportError, Exception) as exc:
        logger.debug("iceberg_connection_skipped", error=str(exc))
        return {}


def _resolve_s3_connection() -> dict[str, dict[str, Any]]:
    """Resolve S3 connection from the active object-store capability.

    Discovers and builds a Sling-compatible S3 connection configuration
    from the active object-store capability provider (e.g., phlo-minio).

    Returns:
        Dict with "PHLO_S3" key containing connection configuration,
        or empty dict if no object-store capability is available.

    """
    _ensure_capabilities_discovered("object_store")
    requested_name = os.environ.get("PHLO_OBJECT_STORE") or _project_env_value("PHLO_OBJECT_STORE")
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
    This function transforms the internal connection dictionary format
    into the environment variable format required by Sling.

    Args:
        connections: Dict of connection name → connection config.

    Returns:
        Dict of environment variable name → JSON string value.

    Example:
        Export connections for environment setup::

            conns = resolve_phlo_connections()
            env_vars = export_sling_env(conns)
            # {"PHLO_POSTGRES": '{"type": "postgres", ...}'}

    """
    import json

    env_vars: dict[str, str] = {}
    for name, config in connections.items():
        env_vars[name] = json.dumps(config)
    return env_vars


def apply_sling_connection_env(environ: MutableMapping[str, str] | None = None) -> dict[str, str]:
    """Inject resolved Sling connections into an environment mapping.

    Applies auto-discovered Sling connections to the environment. Existing
    variables are preserved and not overwritten by auto-generated values.

    Args:
        environ: Environment mapping to mutate. Defaults to ``os.environ``.

    Returns:
        Dict of injected environment variables that were added.

    Example:
        Apply connections before running Sling::

            apply_sling_connection_env()
            # Now os.environ contains PHLO_POSTGRES, PHLO_S3, etc.

    """
    target_env = os.environ if environ is None else environ
    env_vars = export_sling_env(resolve_phlo_connections())
    for name, value in env_vars.items():
        target_env.setdefault(name, value)
    return env_vars

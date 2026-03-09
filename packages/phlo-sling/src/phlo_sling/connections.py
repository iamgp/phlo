"""Auto-generate Sling connections from Phlo capability metadata."""

from __future__ import annotations

from typing import Any

from phlo.logging import get_logger

logger = get_logger(__name__)


def resolve_phlo_connections() -> dict[str, dict[str, Any]]:
    """Build Sling connection definitions from installed Phlo package settings.

    Inspects known Phlo capability providers (phlo-postgres, phlo-minio, etc.)
    and generates Sling-compatible connection dicts.

    Returns:
        Dict mapping connection name to Sling connection config.
    """
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
    """Resolve S3 connection from phlo-minio or phlo-rustfs settings."""
    try:
        from phlo_minio.settings import get_settings as get_minio_settings

        minio = get_minio_settings()
        return {
            "PHLO_S3": {
                "type": "s3",
                "endpoint": f"http://{minio.minio_endpoint()}",
                "access_key_id": minio.minio_access_key,
                "secret_access_key": minio.minio_secret_key,
                "region": minio.s3_region,
            }
        }
    except (ImportError, Exception):
        pass

    try:
        from phlo_rustfs.settings import get_settings as get_rustfs_settings

        rustfs = get_rustfs_settings()
        return {
            "PHLO_S3": {
                "type": "s3",
                "endpoint": f"http://{rustfs.rustfs_endpoint()}",
                "access_key_id": rustfs.rustfs_access_key,
                "secret_access_key": rustfs.rustfs_secret_key,
                "region": rustfs.s3_region,
            }
        }
    except (ImportError, Exception) as exc:
        logger.debug("s3_connection_skipped", error=str(exc))
        return {}


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

"""Superset hooks for auto-configuration."""

from __future__ import annotations

import os
import time

import requests

from phlo.capabilities import resolve_capability
from phlo.capabilities.discovery import discover_capabilities
from phlo.logging import get_logger, setup_logging

logger = get_logger(__name__)


def _superset_auth_provider() -> str:
    """Return the configured Superset auth provider for API logins."""
    return os.environ.get("SUPERSET_AUTH_PROVIDER", "db")


def _superset_database_name() -> str:
    """Return the configured logical database name shown in Superset."""
    configured = os.environ.get("SUPERSET_DATABASE_NAME")
    if configured:
        return configured

    discover_capabilities()
    resolution = resolve_capability("query_engine", _query_engine_name())
    if resolution is not None:
        for key in ("default_catalog", "catalog", "catalog_name"):
            value = resolution.metadata.get(key)
            if isinstance(value, str) and value:
                return value

    raise RuntimeError(
        "SUPERSET_DATABASE_NAME is not configured and no query_engine capability "
        "declares a default catalog."
    )


def _query_engine_name() -> str | None:
    """Return the configured query_engine capability name for Superset integration."""
    return os.environ.get("SUPERSET_QUERY_ENGINE")


def _configured_database_uri() -> str | None:
    """Return an explicit SQLAlchemy URI override when configured."""
    uri = os.environ.get("SUPERSET_DATABASE_URI")
    if uri:
        return uri
    return None


def _discover_query_engine_database_uri() -> str:
    """Resolve a SQLAlchemy URI from query_engine capability metadata."""
    discover_capabilities()
    resolution = resolve_capability("query_engine", _query_engine_name())
    if resolution is None:
        target = _query_engine_name() or "query_engine"
        raise RuntimeError(
            "Superset database URI is not configured. Set SUPERSET_DATABASE_URI or "
            f"install/configure capability '{target}'."
        )

    metadata = resolution.metadata
    direct_uri = metadata.get("sqlalchemy_uri")
    if isinstance(direct_uri, str) and direct_uri:
        return direct_uri

    template = metadata.get("sqlalchemy_uri_template")
    if isinstance(template, str) and template:
        try:
            return template.format(**metadata)
        except KeyError as exc:
            missing = exc.args[0]
            raise RuntimeError(
                f"Query engine metadata is missing '{missing}' required for Superset SQLAlchemy URI."
            ) from exc

    raise RuntimeError(
        "Superset requires SUPERSET_DATABASE_URI or query_engine capability metadata "
        "with sqlalchemy_uri/sqlalchemy_uri_template."
    )


def add_query_engine_database() -> None:
    """Add the configured query-engine database connection to Superset."""
    start = time.perf_counter()
    superset_url = os.environ.get("SUPERSET_URL", "http://localhost:8088")
    admin_user = os.environ.get("SUPERSET_ADMIN_USER", "admin")
    admin_password = os.environ.get("SUPERSET_ADMIN_PASSWORD", "admin")
    logger.info(
        "superset_add_query_engine_database_started",
        superset_url=superset_url,
    )

    # Wait for Superset to be ready
    for attempt in range(30):
        try:
            resp = requests.get(f"{superset_url}/health", timeout=5)
            if resp.status_code == 200:
                logger.info(
                    "superset_health_check_ready",
                    superset_url=superset_url,
                    attempts=attempt + 1,
                )
                break
        except requests.RequestException:
            pass
        logger.debug(
            "superset_health_check_retry",
            superset_url=superset_url,
            attempt=attempt + 1,
            max_attempts=30,
        )
        time.sleep(2)
    else:
        logger.error(
            "superset_health_check_failed",
            superset_url=superset_url,
            attempts=30,
            elapsed_ms=round((time.perf_counter() - start) * 1000, 2),
        )
        return

    session = requests.Session()

    # Login to get CSRF token and session
    try:
        logger.info("superset_login_started", superset_url=superset_url, username=admin_user)
        login_resp = session.post(
            f"{superset_url}/api/v1/security/login",
            json={
                "username": admin_user,
                "password": admin_password,
                "provider": _superset_auth_provider(),
            },
            timeout=10,
        )
        login_resp.raise_for_status()
        access_token = login_resp.json().get("access_token")
        session.headers["Authorization"] = f"Bearer {access_token}"
        logger.info("superset_login_completed", superset_url=superset_url)
    except requests.RequestException as exc:
        logger.error(
            "superset_login_failed",
            superset_url=superset_url,
            error=str(exc),
        )
        return

    # Get CSRF token
    try:
        csrf_resp = session.get(f"{superset_url}/api/v1/security/csrf_token/", timeout=10)
        csrf_token = csrf_resp.json().get("result")
        session.headers["X-CSRFToken"] = csrf_token
        logger.info("superset_csrf_token_loaded", superset_url=superset_url)
    except requests.RequestException as exc:
        logger.warning(
            "superset_csrf_token_load_failed",
            superset_url=superset_url,
            error=str(exc),
        )

    # Check if query-engine database already exists
    try:
        database_name = _superset_database_name()
    except RuntimeError as exc:
        logger.error("superset_database_name_resolution_failed", error=str(exc))
        return

    try:
        dbs_resp = session.get(f"{superset_url}/api/v1/database/", timeout=10)
        existing_dbs = dbs_resp.json().get("result", [])
        for db in existing_dbs:
            if db.get("database_name") == database_name:
                logger.info(
                    "superset_query_engine_database_exists",
                    superset_url=superset_url,
                    database_name=database_name,
                    elapsed_ms=round((time.perf_counter() - start) * 1000, 2),
                )
                return
    except requests.RequestException as exc:
        logger.warning(
            "superset_database_list_failed",
            superset_url=superset_url,
            error=str(exc),
        )

    database_uri = _configured_database_uri() or _discover_query_engine_database_uri()

    database_payload = {
        "database_name": database_name,
        "sqlalchemy_uri": database_uri,
        "expose_in_sqllab": True,
        "allow_run_async": True,
        "allow_ctas": True,
        "allow_cvas": True,
        "allow_dml": True,
        "extra": '{"allows_virtual_table_explore": true}',
    }

    try:
        logger.info(
            "superset_query_engine_database_create_started",
            superset_url=superset_url,
            database_name=database_name,
            sqlalchemy_uri=database_uri,
        )
        resp = session.post(
            f"{superset_url}/api/v1/database/",
            json=database_payload,
            timeout=30,
        )
        resp.raise_for_status()
        logger.info(
            "superset_query_engine_database_create_completed",
            superset_url=superset_url,
            database_name=database_name,
            elapsed_ms=round((time.perf_counter() - start) * 1000, 2),
        )
    except requests.RequestException as exc:
        logger.error(
            "superset_query_engine_database_create_failed",
            superset_url=superset_url,
            database_name=database_name,
            error=str(exc),
            elapsed_ms=round((time.perf_counter() - start) * 1000, 2),
        )


if __name__ == "__main__":
    import sys

    setup_logging()

    if len(sys.argv) > 1 and sys.argv[1] == "add-database":
        add_query_engine_database()
    else:
        logger.info("Usage: python -m phlo_superset.hooks add-database")

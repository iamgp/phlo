"""Superset hooks for auto-configuration."""

from __future__ import annotations

import os
import time

import requests

from phlo.logging import get_logger, setup_logging

logger = get_logger(__name__)


def _superset_auth_provider() -> str:
    """Return the configured Superset auth provider for API logins."""
    return os.environ.get("SUPERSET_AUTH_PROVIDER", "db")


def _superset_database_name() -> str:
    """Return the configured logical database name shown in Superset."""
    return os.environ.get("SUPERSET_DATABASE_NAME", "query_engine")


def add_trino_database() -> None:
    """Add Trino database connection to Superset."""
    start = time.perf_counter()
    superset_url = os.environ.get("SUPERSET_URL", "http://localhost:8088")
    admin_user = os.environ.get("SUPERSET_ADMIN_USER", "admin")
    admin_password = os.environ.get("SUPERSET_ADMIN_PASSWORD", "admin")
    logger.info(
        "superset_add_trino_database_started",
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

    # Check if Trino database already exists
    try:
        dbs_resp = session.get(f"{superset_url}/api/v1/database/", timeout=10)
        existing_dbs = dbs_resp.json().get("result", [])
        database_name = _superset_database_name()
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

    # Add Trino database
    trino_host = os.environ.get("TRINO_HOST", "trino")
    trino_port = os.environ.get("TRINO_PORT", "8080")
    trino_catalog = os.environ.get("TRINO_CATALOG", "iceberg")
    database_name = _superset_database_name()

    database_payload = {
        "database_name": database_name,
        "sqlalchemy_uri": f"trino://{trino_host}:{trino_port}/{trino_catalog}",
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
            trino_host=trino_host,
            trino_port=trino_port,
            trino_catalog=trino_catalog,
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
        add_trino_database()
    else:
        logger.info("Usage: python -m phlo_superset.hooks add-database")

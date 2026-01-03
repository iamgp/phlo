"""Superset hooks for auto-configuration."""

from __future__ import annotations

import os
import time

import requests

from phlo.logging import get_logger, setup_logging

logger = get_logger(__name__)


def add_trino_database() -> None:
    """Add Trino database connection to Superset."""
    superset_url = os.environ.get("SUPERSET_URL", "http://localhost:8088")
    admin_user = os.environ.get("SUPERSET_ADMIN_USER", "admin")
    admin_password = os.environ.get("SUPERSET_ADMIN_PASSWORD", "admin")

    # Wait for Superset to be ready
    for attempt in range(30):
        try:
            resp = requests.get(f"{superset_url}/health", timeout=5)
            if resp.status_code == 200:
                break
        except requests.RequestException:
            pass
        logger.info("Waiting for Superset... (attempt %d/30)", attempt + 1)
        time.sleep(2)
    else:
        logger.error("Superset not ready after 60s")
        return

    session = requests.Session()

    # Login to get CSRF token and session
    try:
        login_resp = session.post(
            f"{superset_url}/api/v1/security/login",
            json={
                "username": admin_user,
                "password": admin_password,
                "provider": "db",
            },
            timeout=10,
        )
        login_resp.raise_for_status()
        access_token = login_resp.json().get("access_token")
        session.headers["Authorization"] = f"Bearer {access_token}"
    except requests.RequestException as exc:
        logger.error("Failed to login to Superset: %s", exc)
        return

    # Get CSRF token
    try:
        csrf_resp = session.get(f"{superset_url}/api/v1/security/csrf_token/", timeout=10)
        csrf_token = csrf_resp.json().get("result")
        session.headers["X-CSRFToken"] = csrf_token
    except requests.RequestException as exc:
        logger.warning("Failed to get CSRF token: %s", exc)

    # Check if Trino database already exists
    try:
        dbs_resp = session.get(f"{superset_url}/api/v1/database/", timeout=10)
        existing_dbs = dbs_resp.json().get("result", [])
        for db in existing_dbs:
            if db.get("database_name") == "Trino":
                logger.info("Trino database already exists in Superset")
                return
    except requests.RequestException as exc:
        logger.warning("Failed to list databases: %s", exc)

    # Add Trino database
    trino_host = os.environ.get("TRINO_HOST", "trino")
    trino_port = os.environ.get("TRINO_PORT", "8080")
    trino_catalog = os.environ.get("TRINO_CATALOG", "iceberg")

    database_payload = {
        "database_name": "Trino",
        "sqlalchemy_uri": f"trino://{trino_host}:{trino_port}/{trino_catalog}",
        "expose_in_sqllab": True,
        "allow_run_async": True,
        "allow_ctas": True,
        "allow_cvas": True,
        "allow_dml": True,
        "extra": '{"allows_virtual_table_explore": true}',
    }

    try:
        resp = session.post(
            f"{superset_url}/api/v1/database/",
            json=database_payload,
            timeout=30,
        )
        resp.raise_for_status()
        logger.info("Successfully added Trino database to Superset")
    except requests.RequestException as exc:
        logger.error("Failed to add Trino database: %s", exc)


if __name__ == "__main__":
    import sys

    setup_logging()

    if len(sys.argv) > 1 and sys.argv[1] == "add-database":
        add_trino_database()
    else:
        logger.info("Usage: python -m phlo_superset.hooks add-database")

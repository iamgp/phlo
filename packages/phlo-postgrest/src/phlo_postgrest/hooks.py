"""PostgREST hooks for auto-configuration."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

import psycopg2

logger = logging.getLogger(__name__)


def _load_env_files() -> None:
    """Load environment variables from .phlo/.env and .phlo/.env.local."""
    try:
        from dotenv import load_dotenv

        phlo_dir = Path.cwd() / ".phlo"
        env_file = phlo_dir / ".env"
        env_local = phlo_dir / ".env.local"

        if env_file.exists():
            load_dotenv(env_file)
        if env_local.exists():
            load_dotenv(env_local, override=True)
    except ImportError:
        # dotenv not available, try manual parsing
        phlo_dir = Path.cwd() / ".phlo"
        for env_file in [phlo_dir / ".env", phlo_dir / ".env.local"]:
            if env_file.exists():
                with open(env_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, _, value = line.partition("=")
                            value = value.strip().strip('"').strip("'")
                            os.environ.setdefault(key.strip(), value)


def _get_db_connection():
    """Get PostgreSQL connection using environment variables."""
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = int(os.environ.get("POSTGRES_PORT", "5432"))
    db = os.environ.get("POSTGRES_DB", "lakehouse")
    user = os.environ.get("POSTGRES_USER", "phlo")
    password = os.environ.get("POSTGRES_PASSWORD", "phlo")

    return psycopg2.connect(
        host=host,
        port=port,
        database=db,
        user=user,
        password=password,
    )


def discover_schemas() -> list[str]:
    """Discover all user schemas that contain tables.

    Returns:
        List of schema names
    """
    conn = _get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT DISTINCT table_schema
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
              AND table_schema NOT LIKE 'pg_%%'
              AND table_schema != 'information_schema'
            ORDER BY table_schema
            """
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def configure_schemas() -> None:
    """Auto-configure PostgREST to expose all discovered schemas.

    This function:
    1. Discovers all user schemas in PostgreSQL
    2. Updates the .phlo/.env file with PGRST_DB_SCHEMAS
    3. Restarts the PostgREST container to pick up the change
    """
    logger.info("Discovering user schemas for PostgREST...")

    try:
        schemas = discover_schemas()
    except Exception as e:
        logger.error("Failed to discover schemas: %s", e)
        raise

    if not schemas:
        logger.warning("No user schemas found")
        return

    schemas_str = ",".join(schemas)
    logger.info("Discovered schemas: %s", schemas_str)

    # Update .env file
    phlo_dir = Path.cwd() / ".phlo"
    env_file = phlo_dir / ".env"

    if env_file.exists():
        # Read existing content
        content = env_file.read_text()
        lines = content.splitlines()

        # Update or add PGRST_DB_SCHEMAS
        updated = False
        new_lines = []
        for line in lines:
            if line.startswith("PGRST_DB_SCHEMAS="):
                new_lines.append(f"PGRST_DB_SCHEMAS={schemas_str}")
                updated = True
            else:
                new_lines.append(line)

        if not updated:
            new_lines.append(f"PGRST_DB_SCHEMAS={schemas_str}")

        env_file.write_text("\n".join(new_lines) + "\n")
        logger.info("Updated %s with PGRST_DB_SCHEMAS=%s", env_file, schemas_str)
    else:
        logger.warning(".env file not found at %s", env_file)

    # Recreate PostgREST container to pick up new config from .env
    # docker restart doesn't re-read env files, we need docker compose up
    phlo_dir = Path.cwd() / ".phlo"
    project_name = os.environ.get("COMPOSE_PROJECT_NAME", Path.cwd().name)
    container_name = f"{project_name}-postgrest-1"

    logger.info("Recreating PostgREST container to apply new schema config...")
    try:
        result = subprocess.run(
            ["docker", "compose", "-f", str(phlo_dir / "docker-compose.yml"), "up", "-d", "--force-recreate", "postgrest"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=phlo_dir,
        )
        if result.returncode == 0:
            logger.info("PostgREST recreated, waiting for healthy status...")
            _wait_for_healthy(container_name, timeout=30)
        else:
            logger.warning("Failed to recreate PostgREST: %s", result.stderr)
    except Exception as e:
        logger.warning("Could not recreate PostgREST container: %s", e)


def _wait_for_healthy(container_name: str, timeout: int = 30) -> None:
    """Wait for a Docker container to become healthy."""
    import time

    start = time.time()
    while time.time() - start < timeout:
        try:
            result = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Health.Status}}", container_name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            status = result.stdout.strip()
            if status == "healthy":
                logger.info("PostgREST container is healthy")
                return
            if status in ("unhealthy", ""):
                # No health check or unhealthy, just wait a bit
                time.sleep(2)
                logger.info("PostgREST container ready (no healthcheck)")
                return
        except Exception:
            pass
        time.sleep(1)
    logger.warning("Timeout waiting for PostgREST to become healthy")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Load env files before running hooks
    _load_env_files()

    if len(sys.argv) > 1 and sys.argv[1] == "configure-schemas":
        configure_schemas()
    else:
        print("Usage: python -m phlo_postgrest.hooks configure-schemas")

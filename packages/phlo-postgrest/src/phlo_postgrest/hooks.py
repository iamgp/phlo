"""PostgREST hooks for auto-configuration."""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from phlo.infrastructure.config import get_project_name_from_config, load_infrastructure_config

logger = logging.getLogger(__name__)


def _get_config_file() -> Path:
    """Return the PostgREST config file path."""
    phlo_dir = Path.cwd() / ".phlo"
    return phlo_dir / "postgrest" / "conf" / "postgrest.conf"


def _read_config_values(config_file: Path) -> dict[str, str]:
    """Parse PostgREST config file into a dict of key/value pairs."""
    values: dict[str, str] = {}
    if not config_file.exists():
        return values

    for raw_line in config_file.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "#" in line:
            line = line.split("#", 1)[0].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        values[key] = value

    return values


def _parse_db_uri(db_uri: str) -> dict[str, str]:
    """Parse db-uri into connection parts."""
    parsed = urlparse(db_uri)
    username = unquote(parsed.username or "")
    password = unquote(parsed.password or "")
    database = parsed.path.lstrip("/")
    return {
        "username": username,
        "password": password,
        "database": database,
    }


def _resolve_container_name(service_name: str) -> str:
    """Resolve a Docker container name using infrastructure config or default pattern."""
    project_name = get_project_name_from_config() or Path.cwd().name
    infra = load_infrastructure_config()
    service = infra.get_service(service_name)
    if service:
        return service.get_container_name(project_name, infra.container_naming_pattern)
    return infra.container_naming_pattern.format(project=project_name, service=service_name)


def _discover_schemas_via_docker(db_uri: str) -> list[str]:
    """Discover schemas by running psql inside the Postgres container."""
    db_parts = _parse_db_uri(db_uri)
    if not db_parts["username"] or not db_parts["database"]:
        raise ValueError("db-uri must include username and database")

    sql = (
        "SELECT DISTINCT table_schema "
        "FROM information_schema.tables "
        "WHERE table_type = 'BASE TABLE' "
        "AND table_schema NOT LIKE 'pg_%' "
        "AND table_schema != 'information_schema' "
        "AND table_schema != 'hdb_catalog' "
        "ORDER BY table_schema;"
    )

    postgres_container = _resolve_container_name("postgres")
    cmd = [
        "docker",
        "exec",
    ]
    if db_parts["password"]:
        cmd.extend(["-e", f"PGPASSWORD={db_parts['password']}"])
    cmd.extend(
        [
            postgres_container,
            "psql",
            "-t",
            "-A",
            "-U",
            db_parts["username"],
            "-d",
            db_parts["database"],
            "-c",
            sql,
        ]
    )

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"psql failed: {result.stderr.strip()}")

    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def discover_schemas() -> list[str]:
    """Discover all user schemas that contain tables.

    Returns:
        List of schema names
    """
    config_file = _get_config_file()
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found at {config_file}")

    config_values = _read_config_values(config_file)
    db_uri = config_values.get("db-uri")
    if not db_uri:
        raise ValueError("db-uri not found in PostgREST config")

    return _discover_schemas_via_docker(db_uri)


def configure_schemas() -> None:
    """Auto-configure PostgREST to expose all discovered schemas.

    This function:
    1. Discovers all user schemas in PostgreSQL
    2. Updates the PostgREST config file with db-schemas
    3. Restarts the PostgREST container to pick up the change
    """
    logger.info("Discovering user schemas for PostgREST...")

    try:
        schemas = discover_schemas()
    except Exception as e:
        logger.error("Failed to discover schemas: %s", e)
        raise

    if not schemas:
        logger.warning("No user schemas found, using default 'public'")
        schemas = ["public"]
    elif "marts" in schemas:
        schemas = ["marts"] + [schema for schema in schemas if schema != "marts"]

    schemas_str = ",".join(schemas)
    logger.info("Discovered schemas: %s", schemas_str)

    # Update PostgREST config file
    config_file = _get_config_file()

    if not config_file.exists():
        logger.warning("Config file not found at %s", config_file)
        return

    # Read existing config
    content = config_file.read_text()
    lines = content.splitlines()

    # Update db-schemas line
    updated = False
    new_lines = []
    for line in lines:
        if line.startswith("db-schemas"):
            new_lines.append(f'db-schemas = "{schemas_str}"')
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        # Add db-schemas line after db-anon-role
        for i, line in enumerate(new_lines):
            if line.startswith("db-anon-role"):
                new_lines.insert(i + 1, f'db-schemas = "{schemas_str}"')
                break

    config_file.write_text("\n".join(new_lines) + "\n")
    logger.info("Updated %s with db-schemas=%s", config_file, schemas_str)

    # Restart PostgREST container to pick up new config
    container_name = _resolve_container_name("postgrest")

    logger.info("Restarting PostgREST container to apply new schema config...")
    try:
        result = subprocess.run(
            ["docker", "restart", container_name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            logger.info("PostgREST restarted, waiting for healthy status...")
            _wait_for_healthy(container_name, timeout=30)
        else:
            logger.warning("Failed to restart PostgREST: %s", result.stderr)
    except Exception as e:
        logger.warning("Could not restart PostgREST container: %s", e)


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

    if len(sys.argv) > 1 and sys.argv[1] == "configure-schemas":
        configure_schemas()
    else:
        print("Usage: python -m phlo_postgrest.hooks configure-schemas")

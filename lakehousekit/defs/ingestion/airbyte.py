from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import requests
from dagster import AssetsDefinition, get_dagster_logger
from dagster_airbyte import build_airbyte_assets
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

from lakehousekit.config import config


@dataclass(frozen=True)
class AirbyteConnectionConfig:
    """
    Configuration for an Airbyte connection.

    Use connection_name for resilient lookups that survive Docker restarts.
    Falls back to connection_id if name lookup fails.
    """

    connection_name: str
    destination_tables: Sequence[str] | None = None
    group_name: str | None = None
    connection_id: str | None = None  # Optional fallback


def _get_airbyte_url(path: str) -> str:
    """Build Airbyte API URL."""
    return f"{config.get_airbyte_base_url()}{path}"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _post_airbyte(path: str, payload: Mapping[str, Any]) -> requests.Response:
    """Call Airbyte API with retries and consistent settings."""
    response = requests.post(
        _get_airbyte_url(path),
        json=payload,
        timeout=10,
    )
    response.raise_for_status()
    return response


def _get_workspace_id() -> str | None:
    """Get the first available workspace ID."""
    logger = get_dagster_logger()
    try:
        response = _post_airbyte("/api/v1/workspaces/list", {})
        workspaces = response.json().get("workspaces", [])
    except RetryError as exc:
        logger.exception(
            "Failed to retrieve Airbyte workspace list after multiple attempts: %s",
            exc.last_attempt.exception() if exc.last_attempt else exc,
        )
        return None
    except requests.RequestException as exc:
        logger.exception("Error calling Airbyte workspaces API: %s", exc)
        return None
    except ValueError as exc:
        logger.exception("Invalid JSON response from Airbyte workspace API: %s", exc)
        return None

    if not workspaces:
        logger.warning("Airbyte workspace list is empty")
        return None

    workspace_id = workspaces[0].get("workspaceId")
    if not workspace_id:
        logger.warning("Workspace payload missing 'workspaceId' field")
        return None

    return workspace_id


def _lookup_connection_by_name(connection_name: str) -> str | None:
    """
    Look up an Airbyte connection ID by name.

    This allows connections to be referenced by name rather than ID,
    making them resilient to Docker restarts and workspace recreation.
    """
    logger = get_dagster_logger()

    workspace_id: str | None = None

    try:
        workspace_id = _get_workspace_id()
        if not workspace_id:
            logger.warning("Could not get Airbyte workspace ID")
            return None

        response = _post_airbyte(
            "/api/v1/connections/list", {"workspaceId": workspace_id}
        )

        connections = response.json().get("connections", [])
        for conn in connections:
            if conn.get("name") == connection_name:
                return conn.get("connectionId")

        logger.info(
            f"Airbyte connection '{connection_name}' not found. "
            f"Available connections: {[c.get('name') for c in connections]}"
        )
        return None

    except RetryError as exc:
        logger.exception(
            "Failed to list Airbyte connections for workspace %s after retries: %s",
            workspace_id or "unknown",
            exc.last_attempt.exception() if exc.last_attempt else exc,
        )
        return None
    except requests.RequestException as exc:
        logger.exception("Error calling Airbyte connections API: %s", exc)
        return None
    except ValueError as exc:
        logger.exception("Invalid JSON response from Airbyte connections API: %s", exc)
        return None


def _resolve_connection_id(config: AirbyteConnectionConfig) -> str | None:
    """
    Resolve a connection ID from the config.

    Tries in order:
    1. Lookup by connection_name
    2. Use connection_id if provided
    """
    logger = get_dagster_logger()

    # Try name lookup first (preferred)
    connection_id = _lookup_connection_by_name(config.connection_name)
    if connection_id:
        logger.info(
            f"Found Airbyte connection '{config.connection_name}' with ID {connection_id}"
        )
        return connection_id

    # Fall back to provided ID
    if config.connection_id:
        logger.info(
            f"Using provided connection ID {config.connection_id} for '{config.connection_name}'"
        )
        return config.connection_id

    return None


def build_assets_from_configs(
    configs: Iterable[AirbyteConnectionConfig],
) -> list[AssetsDefinition]:
    """
    Build Airbyte assets from connection configurations.

    Connections are looked up by name, making them resilient to Docker restarts.
    If a connection doesn't exist, it's skipped with a warning.
    """
    assets: list[AssetsDefinition] = []
    logger = get_dagster_logger()

    for conn_config in configs:
        # Resolve connection ID from name or fallback
        connection_id = _resolve_connection_id(conn_config)

        if not connection_id:
            logger.warning(
                f"Could not find Airbyte connection '{conn_config.connection_name}'. "
                "Skipping asset creation."
            )
            continue

        try:
            connection_assets = build_airbyte_assets(
                connection_id=connection_id,
                destination_tables=list(conn_config.destination_tables or []),
                group_name=conn_config.group_name,
            )
            assets.extend(connection_assets)
            logger.info(
                "Successfully created assets for Airbyte connection '%s'",
                conn_config.connection_name,
            )
        except Exception as exc:
            logger.exception(
                "Failed to build assets for connection '%s': %s. Skipping this connection.",
                conn_config.connection_name,
                exc,
            )

    return assets

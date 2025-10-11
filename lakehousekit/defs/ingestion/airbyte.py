from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Sequence

import requests
from dagster import AssetsDefinition, get_dagster_logger
from dagster_airbyte import build_airbyte_assets


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
    airbyte_host = os.getenv("AIRBYTE_HOST", "airbyte-server")
    airbyte_port = os.getenv("AIRBYTE_API_PORT", "8001")
    return f"http://{airbyte_host}:{airbyte_port}{path}"


def _get_workspace_id() -> str | None:
    """Get the first available workspace ID."""
    try:
        response = requests.post(
            _get_airbyte_url("/api/v1/workspaces/list"),
            json={},
            timeout=5,
        )
        if response.status_code == 200:
            workspaces = response.json().get("workspaces", [])
            if workspaces:
                return workspaces[0]["workspaceId"]
    except Exception:
        pass
    return None


def _lookup_connection_by_name(connection_name: str) -> str | None:
    """
    Look up an Airbyte connection ID by name.

    This allows connections to be referenced by name rather than ID,
    making them resilient to Docker restarts and workspace recreation.
    """
    logger = get_dagster_logger()

    try:
        workspace_id = _get_workspace_id()
        if not workspace_id:
            logger.warning("Could not get Airbyte workspace ID")
            return None

        response = requests.post(
            _get_airbyte_url("/api/v1/connections/list"),
            json={"workspaceId": workspace_id},
            timeout=5,
        )

        if response.status_code != 200:
            return None

        connections = response.json().get("connections", [])
        for conn in connections:
            if conn.get("name") == connection_name:
                return conn.get("connectionId")

        logger.info(
            f"Airbyte connection '{connection_name}' not found. "
            f"Available connections: {[c.get('name') for c in connections]}"
        )
        return None

    except Exception as e:
        logger.warning(f"Error looking up Airbyte connection '{connection_name}': {e}")
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

    for config in configs:
        # Resolve connection ID from name or fallback
        connection_id = _resolve_connection_id(config)

        if not connection_id:
            logger.warning(
                f"Could not find Airbyte connection '{config.connection_name}'. "
                "Skipping asset creation."
            )
            continue

        try:
            connection_assets = build_airbyte_assets(
                connection_id=connection_id,
                destination_tables=list(config.destination_tables or []),
                group_name=config.group_name,
            )
            assets.extend(connection_assets)
            logger.info(
                f"Successfully created assets for Airbyte connection '{config.connection_name}'"
            )
        except Exception as e:
            logger.warning(
                f"Failed to build assets for connection '{config.connection_name}': {e}. "
                "Skipping this connection."
            )

    return assets

"""Observatory extension settings endpoints.

Provides CRUD operations for per-extension settings storage.
Settings are persisted via the settings service and validated
against extension-defined schemas.

Key Endpoints:
    GET /api/observatory/extensions/{name}/settings: Get extension settings.
    PUT /api/observatory/extensions/{name}/settings: Update extension settings.

Example:
    Retrieving extension settings:

    .. code-block:: bash

        curl http://localhost:4000/api/observatory/extensions/my-extension/settings

    Response:

    .. code-block:: json

        {
            "settings": {"theme": "dark", "refreshInterval": 5000},
            "updated_at": "2024-01-15T10:30:00"
        }

"""

from __future__ import annotations

from typing import Any

from anyio.to_thread import run_sync
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from phlo.logging import get_logger
from phlo.plugins.observatory import get_observatory_extension
from phlo.plugins.observatory_settings import SettingsScope, get_settings_service


logger = get_logger(__name__)

router = APIRouter(prefix="/api/observatory", tags=["observatory"])


class ExtensionSettingsPayload(BaseModel):
    """Request payload for extension settings updates."""

    settings: dict[str, Any]


class ExtensionSettingsResponse(BaseModel):
    """Response payload for extension settings endpoints."""

    settings: dict[str, Any] | None
    updated_at: str | None


def _get_extension(name: str) -> Any | None:
    """Return an Observatory extension plugin by name.

    Args:
        name: Registered extension name.

    Returns:
        ObservatoryExtensionPlugin | None: Matched extension, if present.

    """
    return get_observatory_extension(name)


def _get_extension_scope_schema_defaults(
    name: str,
) -> tuple[SettingsScope, dict[str, Any] | None, dict[str, Any] | None]:
    """Resolve settings scope, schema, and defaults for an extension.

    Args:
        name: Registered extension name.

    Returns:
        tuple[SettingsScope, dict[str, Any] | None, dict[str, Any] | None]:
            Storage scope, validation schema, and default settings.

    Raises:
        HTTPException: If the extension is not found.

    """
    extension = _get_extension(name)
    if not extension:
        raise HTTPException(status_code=404, detail=f"Observatory extension not found: {name}")
    manifest = extension.get_manifest()
    if not manifest.settings:
        return SettingsScope.EXTENSION, None, None
    scope = SettingsScope(manifest.settings.scope)
    return scope, manifest.settings.settings_schema, manifest.settings.defaults


def _extension_namespace(name: str) -> str:
    """Build the settings namespace key for an extension.

    Args:
        name: Registered extension name.

    Returns:
        str: Namespaced storage key.

    """
    return f"observatory.extension.{name}"


def _fetch_settings_sync(name: str) -> ExtensionSettingsResponse:
    """Fetch extension settings for one extension name.

    Args:
        name: Registered extension name.

    Returns:
        ExtensionSettingsResponse: Stored settings or manifest defaults.

    """
    scope, _schema, defaults = _get_extension_scope_schema_defaults(name)
    service = get_settings_service()
    record = service.get(scope, _extension_namespace(name))
    if not record:
        return ExtensionSettingsResponse(settings=defaults, updated_at=None)
    return ExtensionSettingsResponse(settings=record.settings, updated_at=record.updated_at)


def _upsert_settings_sync(
    name: str, payload: ExtensionSettingsPayload
) -> ExtensionSettingsResponse:
    """Persist extension settings for one extension name.

    Args:
        name: Registered extension name.
        payload: Incoming extension settings.

    Returns:
        ExtensionSettingsResponse: Saved settings and update timestamp.

    Raises:
        HTTPException: If validation fails.

    """
    scope, schema, _defaults = _get_extension_scope_schema_defaults(name)
    service = get_settings_service()
    try:
        record = service.put(
            scope,
            _extension_namespace(name),
            payload.settings,
            schema=schema,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ExtensionSettingsResponse(settings=record.settings, updated_at=record.updated_at)


@router.get("/extensions/{name}/settings", response_model=ExtensionSettingsResponse)
async def get_extension_settings(name: str) -> ExtensionSettingsResponse:
    """Fetch settings for a single extension.

    Args:
        name: Registered extension name.

    Returns:
        ExtensionSettingsResponse with current settings and update timestamp.

    Raises:
        HTTPException: If extension not found (404), settings service unavailable (503),
            or on other errors (500).

    """
    try:
        return await run_sync(_fetch_settings_sync, name)
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to fetch extension settings")
        raise HTTPException(status_code=500, detail="Failed to fetch settings") from exc


@router.put("/extensions/{name}/settings", response_model=ExtensionSettingsResponse)
async def put_extension_settings(
    name: str, payload: ExtensionSettingsPayload
) -> ExtensionSettingsResponse:
    """Replace settings for a single extension.

    Args:
        name: Registered extension name.
        payload: ExtensionSettingsPayload with new settings values.

    Returns:
        ExtensionSettingsResponse with saved settings and update timestamp.

    Raises:
        HTTPException: If extension not found (404), validation fails (422),
            settings service unavailable (503), or on other errors (500).

    """
    try:
        return await run_sync(_upsert_settings_sync, name, payload)
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to update extension settings")
        raise HTTPException(status_code=500, detail="Failed to update settings") from exc

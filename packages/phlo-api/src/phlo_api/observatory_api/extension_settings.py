"""Observatory extension settings endpoints."""

from __future__ import annotations

from typing import Any

from anyio.to_thread import run_sync
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from phlo.discovery import discover_plugins, get_global_registry
from phlo.logging import get_logger
from phlo.plugins.base import ObservatoryExtensionPlugin
from phlo.settings import SettingsScope, get_settings_service

logger = get_logger(__name__)

router = APIRouter(prefix="/api/observatory", tags=["observatory"])

_plugins_discovered = False


class ExtensionSettingsPayload(BaseModel):
    settings: dict[str, Any]


class ExtensionSettingsResponse(BaseModel):
    settings: dict[str, Any] | None
    updated_at: str | None


def _get_extension(name: str) -> ObservatoryExtensionPlugin | None:
    _ensure_plugins_discovered()
    registry = get_global_registry()
    return registry.get_observatory_extension(name)


def _ensure_plugins_discovered() -> None:
    global _plugins_discovered
    if _plugins_discovered:
        return
    discover_plugins(plugin_type="observatory_extensions", auto_register=True)
    _plugins_discovered = True


def _get_extension_scope_schema_defaults(
    name: str,
) -> tuple[SettingsScope, dict[str, Any] | None, dict[str, Any] | None]:
    extension = _get_extension(name)
    if not extension:
        raise HTTPException(status_code=404, detail=f"Observatory extension not found: {name}")
    manifest = extension.get_manifest()
    if not manifest.settings:
        return SettingsScope.EXTENSION, None, None
    scope = SettingsScope(manifest.settings.scope)
    return scope, manifest.settings.schema, manifest.settings.defaults


def _extension_namespace(name: str) -> str:
    return f"observatory.extension.{name}"


def _fetch_settings_sync(name: str) -> ExtensionSettingsResponse:
    scope, _schema, defaults = _get_extension_scope_schema_defaults(name)
    service = get_settings_service()
    record = service.get(scope, _extension_namespace(name))
    if not record:
        return ExtensionSettingsResponse(settings=defaults, updated_at=None)
    return ExtensionSettingsResponse(settings=record.settings, updated_at=record.updated_at)


def _upsert_settings_sync(
    name: str, payload: ExtensionSettingsPayload
) -> ExtensionSettingsResponse:
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
    """Fetch settings for a single extension."""
    try:
        return await run_sync(_fetch_settings_sync, name)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch extension settings")
        raise HTTPException(status_code=500, detail="Failed to fetch settings") from exc


@router.put("/extensions/{name}/settings", response_model=ExtensionSettingsResponse)
async def put_extension_settings(
    name: str, payload: ExtensionSettingsPayload
) -> ExtensionSettingsResponse:
    """Replace settings for a single extension."""
    try:
        return await run_sync(_upsert_settings_sync, name, payload)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to update extension settings")
        raise HTTPException(status_code=500, detail="Failed to update settings") from exc

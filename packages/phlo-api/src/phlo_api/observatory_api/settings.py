"""Server-wide Observatory settings endpoints."""

from __future__ import annotations

from typing import Any

from anyio.to_thread import run_sync
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from phlo.logging import get_logger
from phlo.settings import SettingsScope, get_settings_service

logger = get_logger(__name__)

router = APIRouter(prefix="/api/observatory", tags=["observatory"])


class ObservatorySettingsPayload(BaseModel):
    settings: dict[str, Any]


class ObservatorySettingsResponse(BaseModel):
    settings: dict[str, Any] | None
    updated_at: str | None


OBSERVATORY_SETTINGS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["version", "connections", "defaults", "query", "ui"],
    "properties": {
        "version": {"type": "integer", "enum": [1]},
        "connections": {
            "type": "object",
            "additionalProperties": False,
            "required": ["dagsterGraphqlUrl", "trinoUrl", "nessieUrl"],
            "properties": {
                "dagsterGraphqlUrl": {"type": "string", "minLength": 1},
                "trinoUrl": {"type": "string", "minLength": 1},
                "nessieUrl": {"type": "string", "minLength": 1},
            },
        },
        "defaults": {
            "type": "object",
            "additionalProperties": False,
            "required": ["branch", "catalog", "schema"],
            "properties": {
                "branch": {"type": "string", "minLength": 1},
                "catalog": {"type": "string", "minLength": 1},
                "schema": {"type": "string", "minLength": 1},
            },
        },
        "query": {
            "type": "object",
            "additionalProperties": False,
            "required": ["readOnlyMode", "defaultLimit", "maxLimit", "timeoutMs"],
            "properties": {
                "readOnlyMode": {"type": "boolean"},
                "defaultLimit": {"type": "integer", "minimum": 1, "maximum": 100000},
                "maxLimit": {"type": "integer", "minimum": 1, "maximum": 100000},
                "timeoutMs": {"type": "integer", "minimum": 1000, "maximum": 300000},
            },
        },
        "ui": {
            "type": "object",
            "additionalProperties": False,
            "required": ["density", "dateFormat"],
            "properties": {
                "density": {"type": "string", "enum": ["comfortable", "compact"]},
                "dateFormat": {"type": "string", "enum": ["iso", "local"]},
            },
        },
        "auth": {
            "type": "object",
            "additionalProperties": False,
            "properties": {"token": {"type": "string"}},
        },
        "realtime": {
            "type": "object",
            "additionalProperties": False,
            "required": ["enabled", "intervalMs"],
            "properties": {
                "enabled": {"type": "boolean"},
                "intervalMs": {"type": "integer", "minimum": 1000, "maximum": 60000},
            },
        },
    },
}

OBSERVATORY_SETTINGS_NAMESPACE = "observatory.core"


def _fetch_settings_sync() -> ObservatorySettingsResponse:
    service = get_settings_service()
    record = service.get(SettingsScope.GLOBAL, OBSERVATORY_SETTINGS_NAMESPACE)
    if not record:
        return ObservatorySettingsResponse(settings=None, updated_at=None)
    return ObservatorySettingsResponse(
        settings=record.settings,
        updated_at=record.updated_at,
    )


def _upsert_settings_sync(payload: ObservatorySettingsPayload) -> ObservatorySettingsResponse:
    service = get_settings_service()
    record = service.put(
        SettingsScope.GLOBAL,
        OBSERVATORY_SETTINGS_NAMESPACE,
        payload.settings,
        schema=OBSERVATORY_SETTINGS_SCHEMA,
    )
    return ObservatorySettingsResponse(
        settings=record.settings,
        updated_at=record.updated_at,
    )


@router.get("/settings", response_model=ObservatorySettingsResponse)
async def get_observatory_settings() -> ObservatorySettingsResponse:
    """Fetch server-wide Observatory settings."""
    try:
        return await run_sync(_fetch_settings_sync)
    except Exception as exc:
        logger.exception("Failed to fetch Observatory settings")
        raise HTTPException(status_code=500, detail="Failed to fetch settings") from exc


@router.put("/settings", response_model=ObservatorySettingsResponse)
async def put_observatory_settings(
    payload: ObservatorySettingsPayload,
) -> ObservatorySettingsResponse:
    """Replace server-wide Observatory settings."""
    try:
        return await run_sync(_upsert_settings_sync, payload)
    except Exception as exc:
        logger.exception("Failed to update Observatory settings")
        raise HTTPException(status_code=500, detail="Failed to update settings") from exc

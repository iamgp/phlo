"""Server-wide Observatory settings endpoints."""

from __future__ import annotations

from typing import Any

import psycopg2
from anyio.to_thread import run_sync
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from phlo.config import get_settings
from phlo.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/observatory", tags=["observatory"])


class ObservatorySettingsPayload(BaseModel):
    settings: dict[str, Any]


class ObservatorySettingsResponse(BaseModel):
    settings: dict[str, Any] | None
    updated_at: str | None


def _settings_db_url() -> str:
    settings = get_settings()
    return settings.observatory_settings_db_url or settings.get_postgres_connection_string()


def _ensure_table(conn) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS observatory_settings (
                id INTEGER PRIMARY KEY,
                settings JSONB NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        conn.commit()


def _fetch_settings_sync() -> ObservatorySettingsResponse:
    with psycopg2.connect(_settings_db_url()) as conn:
        _ensure_table(conn)
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT settings, updated_at
                FROM observatory_settings
                WHERE id = 1
                """
            )
            row = cursor.fetchone()
            if not row:
                return ObservatorySettingsResponse(settings=None, updated_at=None)
            settings, updated_at = row
            return ObservatorySettingsResponse(
                settings=settings,
                updated_at=updated_at.isoformat() if updated_at else None,
            )


def _upsert_settings_sync(payload: ObservatorySettingsPayload) -> ObservatorySettingsResponse:
    with psycopg2.connect(_settings_db_url()) as conn:
        _ensure_table(conn)
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO observatory_settings (id, settings, updated_at)
                VALUES (1, %s, NOW())
                ON CONFLICT (id)
                DO UPDATE SET settings = EXCLUDED.settings, updated_at = NOW()
                RETURNING settings, updated_at
                """,
                (payload.settings,),
            )
            settings, updated_at = cursor.fetchone()
            conn.commit()
            return ObservatorySettingsResponse(
                settings=settings,
                updated_at=updated_at.isoformat() if updated_at else None,
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

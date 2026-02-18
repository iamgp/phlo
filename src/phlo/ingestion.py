"""Ingestion public API for Phlo."""

from __future__ import annotations

from phlo.logging import get_logger

logger = get_logger(__name__)

try:
    from phlo_dlt import get_ingestion_assets, phlo_ingestion
except ModuleNotFoundError as exc:  # pragma: no cover - exercised via optional extras
    logger.warning("phlo_dlt_not_installed", exc_info=True)
    raise ModuleNotFoundError(
        "phlo.ingestion requires phlo-dlt. Install phlo[defaults] or phlo-dlt."
    ) from exc

__all__ = ["get_ingestion_assets", "phlo_ingestion"]

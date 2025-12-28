"""Hasura hooks for auto-configuration."""

from __future__ import annotations

import logging
import sys

logger = logging.getLogger(__name__)


def track_tables(schema: str = "api") -> None:
    """Auto-track tables in the specified schema."""
    from phlo_hasura.track import auto_track

    logger.info("Auto-tracking tables in schema: %s", schema)
    try:
        result = auto_track(schema=schema, verbose=True)
        logger.info("Tracking complete: %s", result)
    except Exception as e:
        logger.error("Failed to auto-track tables in schema %s: %s", schema, e)
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1 and sys.argv[1] == "track-tables":
        schema = sys.argv[2] if len(sys.argv) > 2 else "api"
        track_tables(schema=schema)
    else:
        print("Usage: python -m phlo_hasura.hooks track-tables [schema]")

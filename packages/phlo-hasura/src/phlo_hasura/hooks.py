"""Hasura hooks for auto-configuration."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

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
                            # Remove quotes if present
                            value = value.strip().strip('"').strip("'")
                            os.environ.setdefault(key.strip(), value)


def track_tables(schemas: str = "api") -> None:
    """Auto-track tables in the specified schema(s).

    Args:
        schemas: Comma-separated list of schemas to track (e.g., "marts,api"),
                 or "auto" to discover all user schemas automatically
    """
    from phlo_hasura.track import auto_track, auto_track_all

    if schemas == "auto":
        logger.info("Auto-discovering all user schemas...")
        try:
            result = auto_track_all(verbose=True)
            logger.info("Auto-discovery complete: %d schemas processed", len(result))
        except Exception as e:
            logger.error("Failed to auto-track tables: %s", e)
            raise
    else:
        schema_list = [s.strip() for s in schemas.split(",") if s.strip()]
        for schema in schema_list:
            logger.info("Auto-tracking tables in schema: %s", schema)
            try:
                result = auto_track(schema=schema, verbose=True)
                logger.info("Tracking complete for %s: %s", schema, result)
            except Exception as e:
                logger.error("Failed to auto-track tables in schema %s: %s", schema, e)
                # Continue with other schemas even if one fails


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Load env files before running hooks
    _load_env_files()

    if len(sys.argv) > 1 and sys.argv[1] == "track-tables":
        schemas = sys.argv[2] if len(sys.argv) > 2 else "auto"
        track_tables(schemas=schemas)
    else:
        print("Usage: python -m phlo_hasura.hooks track-tables [schemas]")
        print("  schemas: comma-separated list (e.g., 'marts,api'), or 'auto' to discover")

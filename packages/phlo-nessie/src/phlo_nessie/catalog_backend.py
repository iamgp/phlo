"""Nessie-owned PyIceberg catalog helpers."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from phlo.logging import get_logger
from phlo_nessie.settings import get_settings

logger = get_logger(__name__)


def _pyiceberg_catalog_config(ref: str) -> dict[str, Any]:
    settings = get_settings()
    return {
        "type": "rest",
        "uri": f"{settings.nessie_iceberg_rest_uri()}/{ref}",
        "warehouse": os.environ.get("ICEBERG_WAREHOUSE_PATH", "s3://lake/warehouse"),
        "s3.endpoint": os.environ.get("ICEBERG_S3_ENDPOINT")
        or os.environ.get("S3_ENDPOINT", "http://minio:10001"),
        "s3.access-key-id": os.environ.get("ICEBERG_S3_ACCESS_KEY", "minio"),
        "s3.secret-access-key": os.environ.get("ICEBERG_S3_SECRET_KEY", "minio123"),
        "s3.path-style-access": "true",
        "s3.region": os.environ.get("ICEBERG_S3_REGION", "us-east-1"),
    }


@lru_cache(maxsize=16)
def load_pyiceberg_catalog(ref: str = "main"):
    """Load the PyIceberg catalog using Nessie-owned catalog settings."""
    try:
        from pyiceberg.catalog import load_catalog
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Iceberg catalog support is not installed. Install `phlo-nessie[iceberg-cli]`."
        ) from exc

    logger.debug("nessie_pyiceberg_catalog_load_requested", ref=ref)
    return load_catalog(name=f"iceberg_{ref}", **_pyiceberg_catalog_config(ref))

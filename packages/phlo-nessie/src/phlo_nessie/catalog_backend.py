"""Nessie-owned PyIceberg catalog helpers.

This module provides utilities for loading and configuring PyIceberg catalogs
backed by Nessie. It handles S3 configuration, warehouse paths, and reference
branch management.

Example:
    >>> from phlo_nessie.catalog_backend import load_pyiceberg_catalog
    >>> catalog = load_pyiceberg_catalog(ref="main")

Functions:
    load_pyiceberg_catalog: Load a cached PyIceberg catalog instance.
    _pyiceberg_catalog_config: Build configuration dictionary for PyIceberg.

"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from phlo.config.network import resolve_url
from phlo.logging import get_logger
from phlo_nessie.settings import get_settings

logger = get_logger(__name__)


def _pyiceberg_catalog_config(ref: str) -> dict[str, Any]:
    """Build PyIceberg catalog configuration for Nessie backend.

    Constructs the configuration dictionary required by PyIceberg to connect
    to Nessie REST catalog with S3/MinIO storage backend.

    Args:
        ref: Nessie reference (branch/tag) to use as catalog prefix.

    Returns:
        dict[str, Any]: PyIceberg catalog configuration dictionary.

    Example:
        >>> config = _pyiceberg_catalog_config("main")
        >>> config['type']
        'rest'

    """
    settings = get_settings()
    return {
        "type": "rest",
        "uri": f"{settings.nessie_iceberg_rest_uri()}/{ref}",
        "warehouse": os.environ.get("ICEBERG_WAREHOUSE_PATH", "s3://lake/warehouse"),
        "s3.endpoint": resolve_url(
            os.environ.get("ICEBERG_S3_ENDPOINT")
            or os.environ.get("S3_ENDPOINT", "http://minio:10001"),
            port_env_var="MINIO_API_PORT",
        ),
        "s3.access-key-id": os.environ.get("ICEBERG_S3_ACCESS_KEY", "minio"),
        "s3.secret-access-key": os.environ.get("ICEBERG_S3_SECRET_KEY", "minio123"),
        "s3.path-style-access": "true",
        "s3.region": os.environ.get("ICEBERG_S3_REGION", "us-east-1"),
    }


@lru_cache(maxsize=16)
def load_pyiceberg_catalog(ref: str = "main"):
    """Load the PyIceberg catalog using Nessie-owned catalog settings.

    Returns a cached PyIceberg catalog instance configured to connect to
    the Nessie REST catalog for the specified reference. Uses LRU cache
    to avoid redundant catalog initialization.

    Args:
        ref: Nessie reference (branch or tag) to use. Defaults to "main".

    Returns:
        Catalog: PyIceberg catalog instance for the specified reference.

    Raises:
        RuntimeError: If PyIceberg is not installed.

    Example:
        >>> catalog = load_pyiceberg_catalog("main")
        >>> tables = catalog.list_tables("raw")

    Note:
        Maximum of 16 cached catalogs are retained. Least recently used
        entries are evicted when cache is full.

    """
    try:
        from pyiceberg.catalog import load_catalog
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Iceberg catalog support is not installed. Install `phlo-nessie[iceberg-cli]`."
        ) from exc

    logger.debug("nessie_pyiceberg_catalog_load_requested", ref=ref)
    return load_catalog(name=f"iceberg_{ref}", **_pyiceberg_catalog_config(ref))

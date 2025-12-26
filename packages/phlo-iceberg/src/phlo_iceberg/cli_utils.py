"""CLI helper utilities for Iceberg."""

from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def get_iceberg_catalog(ref: str = "main"):
    """
    Get configured Iceberg catalog instance.

    Args:
        ref: Nessie branch/tag reference

    Returns:
        PyIceberg Catalog instance
    """
    from phlo_iceberg.catalog import get_catalog

    return get_catalog(ref=ref)

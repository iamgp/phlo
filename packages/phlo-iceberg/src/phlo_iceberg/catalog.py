"""
Iceberg catalog management using Nessie REST catalog.
"""

from __future__ import annotations

from functools import lru_cache

from pyiceberg.catalog import load_catalog

from phlo.logging import get_logger
from phlo_iceberg.settings import get_settings

logger = get_logger(__name__)


@lru_cache(maxsize=None)
def get_catalog(ref: str = "main"):
    """
    Get PyIceberg catalog configured for Nessie.

    Args:
        ref: Nessie branch/tag reference (default: main)
    """
    logger.debug(
        "iceberg_catalog_get_requested",
        ref=ref,
    )
    catalog_config = get_settings().get_pyiceberg_catalog_config(ref=ref)
    try:
        catalog = load_catalog(name=f"nessie_{ref}", **catalog_config)
    except Exception:
        logger.error(
            "iceberg_catalog_get_failed",
            ref=ref,
            exc_info=True,
        )
        raise
    logger.debug(
        "iceberg_catalog_get_succeeded",
        ref=ref,
    )
    return catalog


def reset_catalog_cache() -> None:
    """Clear cached catalog instances."""
    get_catalog.cache_clear()
    logger.debug("iceberg_catalog_cache_cleared")


def list_tables(namespace: str | None = None, ref: str = "main") -> list[str]:
    """List tables in a namespace (or all namespaces)."""
    logger.info(
        "iceberg_catalog_list_tables_requested",
        namespace=namespace,
        ref=ref,
    )
    catalog = get_catalog(ref=ref)

    try:
        if namespace:
            tables = [str(table) for table in catalog.list_tables(namespace)]
            logger.info(
                "iceberg_catalog_list_tables_succeeded",
                namespace=namespace,
                ref=ref,
                table_count=len(tables),
            )
            return tables

        all_tables: list[str] = []
        for ns in catalog.list_namespaces():
            ns_name = ".".join(ns)
            all_tables.extend([str(table) for table in catalog.list_tables(ns_name)])
        logger.info(
            "iceberg_catalog_list_tables_succeeded",
            namespace=namespace,
            ref=ref,
            table_count=len(all_tables),
        )
        return all_tables
    except Exception:
        logger.error(
            "iceberg_catalog_list_tables_failed",
            namespace=namespace,
            ref=ref,
            exc_info=True,
        )
        raise


def create_namespace(namespace: str, ref: str = "main") -> None:
    """Create a namespace if it doesn't exist."""
    logger.info(
        "iceberg_catalog_create_namespace_requested",
        namespace=namespace,
        ref=ref,
    )
    catalog = get_catalog(ref=ref)
    try:
        catalog.create_namespace(namespace)
        logger.info(
            "iceberg_catalog_create_namespace_succeeded",
            namespace=namespace,
            ref=ref,
        )
    except Exception:
        # Namespace might already exist
        logger.warning(
            "iceberg_catalog_create_namespace_skipped",
            namespace=namespace,
            ref=ref,
            exc_info=True,
        )
        return None

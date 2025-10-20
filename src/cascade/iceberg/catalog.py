# catalog.py - Iceberg catalog management utilities using Nessie as the REST catalog backend
# Provides functions to connect to the catalog, list tables, and manage namespaces
# Handles branch-aware operations for Git-like versioning of data schemas

"""
Iceberg catalog management using Nessie REST catalog.
"""

from functools import lru_cache

from pyiceberg.catalog import load_catalog

from cascade.config import config


# --- Catalog Connection Functions ---
# Functions for connecting to and interacting with the Iceberg catalog
@lru_cache
def get_catalog(ref: str = "main"):
    """
    Get PyIceberg catalog configured for Nessie.

    Args:
        ref: Nessie branch/tag reference (default: main)

    Returns:
        PyIceberg Catalog instance

    Example:
        catalog = get_catalog()
        catalog.load_table("raw.nightscout_entries")

        # Use dev branch
        dev_catalog = get_catalog("dev")
        dev_catalog.load_table("raw.entries")
    """
    catalog_config = config.get_pyiceberg_catalog_config(ref=ref)
    return load_catalog(name=f"nessie_{ref}", **catalog_config)


# --- Table Listing Functions ---
# Functions for discovering tables and namespaces in the catalog
def list_tables(namespace: str | None = None, ref: str = "main") -> list[str]:
    """
    List all tables in a namespace or all namespaces.

    Args:
        namespace: Namespace to list tables from (None for all namespaces)
        ref: Nessie branch/tag reference

    Returns:
        List of table identifiers

    Example:
        tables = list_tables("raw")
        # ['raw.nightscout_entries', 'raw.nightscout_treatments']
    """
    catalog = get_catalog(ref=ref)

    if namespace:
        return [str(table) for table in catalog.list_tables(namespace)]
    else:
        all_tables = []
        for ns in catalog.list_namespaces():
            ns_name = ".".join(ns)
            all_tables.extend([str(table) for table in catalog.list_tables(ns_name)])
        return all_tables


# --- Namespace Management ---
# Functions for creating and managing Iceberg namespaces (databases/schemas)
def create_namespace(namespace: str, ref: str = "main") -> None:
    """
    Create a namespace if it doesn't exist.

    Args:
        namespace: Namespace name (e.g., "raw", "bronze")
        ref: Nessie branch/tag reference

    Example:
        create_namespace("raw")
    """
    catalog = get_catalog(ref=ref)
    try:
        catalog.create_namespace(namespace)
    except Exception:
        # Namespace might already exist
        pass

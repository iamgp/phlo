"""
Iceberg catalog management using Nessie REST catalog.
"""

from functools import lru_cache

from pyiceberg.catalog import load_catalog

from cascade.config import config


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
    """
    return load_catalog(
        name="nessie",
        **{
            "type": "rest",
            "uri": f"http://{config.nessie_host}:{config.nessie_port}/iceberg/{ref}",
            "warehouse": "warehouse",
            # S3/MinIO configuration
            "s3.endpoint": f"http://{config.minio_host}:{config.minio_api_port}",
            "s3.access-key-id": config.minio_root_user,
            "s3.secret-access-key": config.minio_root_password,
            "s3.path-style-access": "true",
            "s3.region": "us-east-1",
        },
    )


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

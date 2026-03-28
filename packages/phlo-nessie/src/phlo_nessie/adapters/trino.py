"""Trino catalog plugins for Nessie-backed Iceberg catalogs.

This module provides Trino catalog plugins that configure Iceberg connections
backed by Nessie's REST catalog API. Supports both production and development
Nessie references.

Example:
    >>> from phlo_nessie.adapters.trino import TrinoNessieIcebergCatalogPlugin
    >>> plugin = TrinoNessieIcebergCatalogPlugin()
    >>> props = plugin.get_properties()

Classes:
    TrinoNessieIcebergCatalogPlugin: Main production catalog.
    TrinoNessieIcebergDevCatalogPlugin: Development branch catalog.

"""

from __future__ import annotations

import os

from phlo.plugins.base import CatalogPlugin, PluginMetadata


def _nessie_iceberg_rest_uri() -> str:
    """Build the Nessie Iceberg REST URI from environment settings.

    Constructs the URI using NESSIE_HOST and NESSIE_PORT environment variables,
    with sensible defaults if not set.

    Returns:
        str: Full Nessie Iceberg REST catalog URI.

    Example:
        >>> uri = _nessie_iceberg_rest_uri()
        'http://nessie:19120/iceberg'

    """
    host = os.environ.get("NESSIE_HOST", "nessie")
    port = os.environ.get("NESSIE_PORT", "19120")
    return f"http://{host}:{port}/iceberg"


def _base_iceberg_catalog_properties(*, prefix: str | None = None) -> dict[str, str]:
    """Build shared Trino Iceberg catalog properties for a Nessie backend.

    Configures Trino connector properties for Iceberg REST catalog backed by
    Nessie. Includes S3/MinIO configuration for warehouse storage.

    Args:
        prefix: Optional catalog prefix for namespacing (e.g., 'dev' for dev branch).

    Returns:
        dict[str, str]: Trino catalog configuration properties.

    Example:
        >>> props = _base_iceberg_catalog_properties()
        >>> props['iceberg.catalog.type']
        'rest'

    """
    minio_endpoint = os.environ.get("S3_ENDPOINT", "http://minio:9000")
    s3_region = os.environ.get("AWS_REGION", "us-east-1")

    props: dict[str, str] = {
        "connector.name": "iceberg",
        "iceberg.catalog.type": "rest",
        "iceberg.rest-catalog.uri": _nessie_iceberg_rest_uri(),
        "iceberg.rest-catalog.warehouse": "warehouse",
        "fs.native-s3.enabled": "true",
        "s3.endpoint": minio_endpoint,
        "s3.path-style-access": "true",
        "s3.region": s3_region,
    }
    if prefix is not None:
        props["iceberg.rest-catalog.prefix"] = prefix
    return props


class TrinoNessieIcebergCatalogPlugin(CatalogPlugin):
    """Main Trino catalog backed by Nessie Iceberg REST.

    This plugin provides the primary production catalog for Trino queries
    against Iceberg tables stored in Nessie. Uses the default Nessie reference
    (usually 'main').

    Attributes:
        metadata: Plugin identity and description.
        targets: List of target systems (['trino']).
        catalog_name: Trino catalog name ('iceberg').

    Example:
        >>> plugin = TrinoNessieIcebergCatalogPlugin()
        >>> props = plugin.get_properties()
        >>> print(props['iceberg.rest-catalog.uri'])

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for catalog registration.

        Returns:
            PluginMetadata: Name, version, description, and tags.

        """
        return PluginMetadata(
            name="iceberg",
            version="0.1.0",
            description="Trino Iceberg catalog backed by Nessie REST",
            tags=["trino", "iceberg", "nessie", "lakehouse"],
        )

    @property
    def targets(self) -> list[str]:
        """Return target systems for this plugin.

        Returns:
            list[str]: ['trino'] indicating Trino compatibility.

        """
        return ["trino"]

    @property
    def catalog_name(self) -> str:
        """Return the Trino catalog name.

        Returns:
            str: 'iceberg' - the catalog name in Trino.

        """
        return "iceberg"

    def get_properties(self) -> dict[str, str]:
        """Return Trino catalog configuration properties.

        Returns:
            dict[str, str]: Properties for Trino Iceberg connector.

        """
        return _base_iceberg_catalog_properties()


class TrinoNessieIcebergDevCatalogPlugin(CatalogPlugin):
    """Dev Trino catalog backed by the Nessie dev ref.

    This plugin provides a separate catalog for Trino queries against the
    'dev' branch in Nessie. Useful for development and testing without
    affecting production data.

    Attributes:
        metadata: Plugin identity and description.
        targets: List of target systems (['trino']).
        catalog_name: Trino catalog name ('iceberg_dev').

    Example:
        >>> plugin = TrinoNessieIcebergDevCatalogPlugin()
        >>> props = plugin.get_properties()
        >>> print(props['iceberg.rest-catalog.prefix'])
        'dev'

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for catalog registration.

        Returns:
            PluginMetadata: Name, version, description, and tags.

        """
        return PluginMetadata(
            name="iceberg_dev",
            version="0.1.0",
            description="Trino Iceberg catalog for the Nessie dev ref",
            tags=["trino", "iceberg", "nessie", "dev"],
        )

    @property
    def targets(self) -> list[str]:
        """Return target systems for this plugin.

        Returns:
            list[str]: ['trino'] indicating Trino compatibility.

        """
        return ["trino"]

    @property
    def catalog_name(self) -> str:
        """Return the Trino catalog name.

        Returns:
            str: 'iceberg_dev' - the catalog name in Trino.

        """
        return "iceberg_dev"

    def get_properties(self) -> dict[str, str]:
        """Return Trino catalog configuration properties with dev prefix.

        Returns:
            dict[str, str]: Properties for Trino Iceberg connector,
                including 'iceberg.rest-catalog.prefix' set to 'dev'.

        """
        return _base_iceberg_catalog_properties(prefix="dev")

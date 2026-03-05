"""Iceberg catalog plugin for Trino."""

from __future__ import annotations

import os

from phlo.plugins.base import CatalogPlugin, PluginMetadata


def _base_iceberg_catalog_properties(
    *,
    prefix: str | None = None,
) -> dict[str, str]:
    """Build shared Iceberg catalog properties from environment."""
    nessie_host = os.environ.get("NESSIE_HOST", "nessie")
    nessie_port = os.environ.get("NESSIE_PORT", "19120")
    minio_endpoint = os.environ.get("S3_ENDPOINT", "http://minio:9000")
    s3_region = os.environ.get("AWS_REGION", "us-east-1")

    props: dict[str, str] = {
        "connector.name": "iceberg",
        "iceberg.catalog.type": "rest",
        "iceberg.rest-catalog.uri": f"http://{nessie_host}:{nessie_port}/iceberg",
        "iceberg.rest-catalog.warehouse": "warehouse",
        "fs.native-s3.enabled": "true",
        "s3.endpoint": minio_endpoint,
        "s3.path-style-access": "true",
        "s3.region": s3_region,
    }
    if prefix is not None:
        props["iceberg.rest-catalog.prefix"] = prefix
    return props


class IcebergCatalogPlugin(CatalogPlugin):
    """Iceberg catalog with Nessie REST backend for Trino."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        Returns:
            PluginMetadata: Static metadata for the Iceberg catalog plugin.
        """
        return PluginMetadata(
            name="iceberg",
            version="0.1.0",
            description="Iceberg catalog with Nessie REST backend",
            tags=["iceberg", "nessie", "lakehouse"],
        )

    @property
    def targets(self) -> list[str]:
        """Return supported orchestration targets.

        Returns:
            list[str]: Target systems supported by this catalog plugin.
        """
        return ["trino"]

    @property
    def catalog_name(self) -> str:
        """Return the Trino catalog name.

        Returns:
            str: Catalog identifier exposed to Trino.
        """
        return "iceberg"

    def get_properties(self) -> dict[str, str]:
        """Generate Iceberg catalog properties from environment."""
        return _base_iceberg_catalog_properties()


class IcebergDevCatalogPlugin(CatalogPlugin):
    """Dev branch Iceberg catalog for Trino."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        Returns:
            PluginMetadata: Static metadata for the dev Iceberg catalog plugin.
        """
        return PluginMetadata(
            name="iceberg_dev",
            version="0.1.0",
            description="Iceberg dev branch catalog",
            tags=["iceberg", "nessie", "dev"],
        )

    @property
    def targets(self) -> list[str]:
        """Return supported orchestration targets.

        Returns:
            list[str]: Target systems supported by this catalog plugin.
        """
        return ["trino"]

    @property
    def catalog_name(self) -> str:
        """Return the Trino catalog name.

        Returns:
            str: Catalog identifier exposed to Trino.
        """
        return "iceberg_dev"

    def get_properties(self) -> dict[str, str]:
        """Generate dev Iceberg catalog properties."""
        return _base_iceberg_catalog_properties(prefix="dev")

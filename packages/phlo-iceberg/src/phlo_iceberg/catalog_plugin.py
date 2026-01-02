"""Iceberg catalog plugin for Trino."""

from __future__ import annotations

import os

from phlo.plugins.base import PluginMetadata, TrinoCatalogPlugin


class IcebergCatalogPlugin(TrinoCatalogPlugin):
    """Iceberg catalog with Nessie REST backend for Trino."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="iceberg",
            version="0.1.0",
            description="Iceberg catalog with Nessie REST backend",
            tags=["iceberg", "nessie", "lakehouse"],
        )

    @property
    def catalog_name(self) -> str:
        return "iceberg"

    def get_properties(self) -> dict[str, str]:
        """Generate Iceberg catalog properties from environment."""
        nessie_host = os.environ.get("NESSIE_HOST", "nessie")
        nessie_port = os.environ.get("NESSIE_PORT", "19120")
        minio_endpoint = os.environ.get("S3_ENDPOINT", "http://minio:9000")
        s3_region = os.environ.get("AWS_REGION", "us-east-1")

        return {
            "connector.name": "iceberg",
            "iceberg.catalog.type": "rest",
            "iceberg.rest-catalog.uri": f"http://{nessie_host}:{nessie_port}/iceberg",
            "iceberg.rest-catalog.warehouse": "warehouse",
            "fs.native-s3.enabled": "true",
            "s3.endpoint": minio_endpoint,
            "s3.path-style-access": "true",
            "s3.region": s3_region,
        }


class IcebergDevCatalogPlugin(TrinoCatalogPlugin):
    """Dev branch Iceberg catalog for Trino."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="iceberg_dev",
            version="0.1.0",
            description="Iceberg dev branch catalog",
            tags=["iceberg", "nessie", "dev"],
        )

    @property
    def catalog_name(self) -> str:
        return "iceberg_dev"

    def get_properties(self) -> dict[str, str]:
        """Generate dev Iceberg catalog properties."""
        nessie_host = os.environ.get("NESSIE_HOST", "nessie")
        nessie_port = os.environ.get("NESSIE_PORT", "19120")
        minio_endpoint = os.environ.get("S3_ENDPOINT", "http://minio:9000")
        s3_region = os.environ.get("AWS_REGION", "us-east-1")

        return {
            "connector.name": "iceberg",
            "iceberg.catalog.type": "rest",
            "iceberg.rest-catalog.uri": f"http://{nessie_host}:{nessie_port}/iceberg",
            "iceberg.rest-catalog.warehouse": "warehouse",
            "iceberg.rest-catalog.prefix": "dev",
            "fs.native-s3.enabled": "true",
            "s3.endpoint": minio_endpoint,
            "s3.path-style-access": "true",
            "s3.region": s3_region,
        }

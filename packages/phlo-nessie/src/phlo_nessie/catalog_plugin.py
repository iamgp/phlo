"""Catalog plugins for Nessie-backed Trino catalogs."""

from __future__ import annotations

import os

from phlo.plugins.base import CatalogPlugin, PluginMetadata

from phlo_nessie.settings import get_settings


def _base_iceberg_catalog_properties(*, prefix: str | None = None) -> dict[str, str]:
    """Build shared Trino Iceberg catalog properties for a Nessie backend."""
    settings = get_settings()
    minio_endpoint = os.environ.get("S3_ENDPOINT", "http://minio:9000")
    s3_region = os.environ.get("AWS_REGION", "us-east-1")

    props: dict[str, str] = {
        "connector.name": "iceberg",
        "iceberg.catalog.type": "rest",
        "iceberg.rest-catalog.uri": settings.nessie_iceberg_rest_uri(),
        "iceberg.rest-catalog.warehouse": "warehouse",
        "fs.native-s3.enabled": "true",
        "s3.endpoint": minio_endpoint,
        "s3.path-style-access": "true",
        "s3.region": s3_region,
    }
    if prefix is not None:
        props["iceberg.rest-catalog.prefix"] = prefix
    return props


class NessieIcebergCatalogPlugin(CatalogPlugin):
    """Main Trino catalog backed by Nessie Iceberg REST."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="iceberg",
            version="0.1.0",
            description="Iceberg catalog with Nessie REST backend",
            tags=["iceberg", "nessie", "lakehouse"],
        )

    @property
    def targets(self) -> list[str]:
        return ["trino"]

    @property
    def catalog_name(self) -> str:
        return "iceberg"

    def get_properties(self) -> dict[str, str]:
        return _base_iceberg_catalog_properties()


class NessieIcebergDevCatalogPlugin(CatalogPlugin):
    """Dev Trino catalog backed by the Nessie dev ref."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="iceberg_dev",
            version="0.1.0",
            description="Iceberg dev branch catalog",
            tags=["iceberg", "nessie", "dev"],
        )

    @property
    def targets(self) -> list[str]:
        return ["trino"]

    @property
    def catalog_name(self) -> str:
        return "iceberg_dev"

    def get_properties(self) -> dict[str, str]:
        return _base_iceberg_catalog_properties(prefix="dev")

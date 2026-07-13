"""Iceberg settings configuration.

This module provides configuration management for Iceberg connections,
including warehouse paths, S3 storage settings, and Nessie catalog endpoints.

Settings are loaded from environment variables and ``.phlo/.env`` files,
following Phlo's standard configuration pattern.

Configuration precedence:
    1. Environment variables (``PHLO_ICEBERG_*``)
    2. ``.phlo/.env.local`` (local overrides)
    3. ``.phlo/.env`` (project defaults)
    4. Default values defined in this module

Example:
    Basic settings usage::

        from phlo_iceberg.settings import get_settings

        settings = get_settings()
        print(f"Warehouse: {settings.iceberg_warehouse_path}")
        print(f"Default branch: {settings.iceberg_default_ref}")

        # Get catalog config for PyIceberg
        catalog_config = settings.get_pyiceberg_catalog_config(ref="main")

    Environment variables::

        export PHLO_ICEBERG_WAREHOUSE_PATH=s3://my-bucket/warehouse
        export PHLO_ICEBERG_DEFAULT_REF=main
        export PHLO_ICEBERG_S3_ACCESS_KEY=mykey
        export PHLO_ICEBERG_S3_SECRET_KEY=mysecret

"""

from __future__ import annotations

from pathlib import Path

from pydantic import AliasChoices, Field

from phlo.config.base import BaseConfig
from phlo.config.cache import project_root_cached
from phlo.config.network import resolve_url as _resolve_service_url
from phlo_iceberg.compatibility import validate_pyiceberg_rest_catalog_config


class IcebergSettings(BaseConfig):
    """Iceberg catalog and storage configuration.

    Defines all configuration parameters for connecting to Iceberg via
    Nessie REST catalog and S3-compatible storage (MinIO).

    Attributes:
        iceberg_warehouse_path: S3 path for the Iceberg warehouse.
            Default: ``s3://lake/warehouse``.
        iceberg_staging_path: S3 path for staging Parquet files.
            Default: ``s3://lake/stage``.
        iceberg_default_namespace: Default namespace for new tables.
            Default: ``raw``.
        iceberg_default_ref: Default Nessie branch/tag reference.
            Default: ``main``.
        iceberg_s3_endpoint: S3-compatible endpoint URL (MinIO).
            Default: ``http://minio:10001``.
        iceberg_s3_access_key: S3 access key for storage operations.
            Default: ``minio``.
        iceberg_s3_secret_key: S3 secret key for storage operations.
            Default: ``minio123``.
        iceberg_s3_region: AWS-style region for S3 operations.
            Default: ``us-east-1``.
        iceberg_catalog_uri: Nessie REST catalog endpoint base URI.
            Default: ``http://nessie:19120/iceberg``.

    Example:
        Configure via environment::

            export PHLO_ICEBERG_WAREHOUSE_PATH=s3://production/warehouse
            export PHLO_ICEBERG_CATALOG_URI=http://nessie.prod:19120/iceberg
            export PHLO_ICEBERG_S3_ACCESS_KEY=prod-key
            export PHLO_ICEBERG_S3_SECRET_KEY=prod-secret

        Access in code::

            from phlo_iceberg.settings import get_settings

            settings = get_settings()
            config = settings.get_pyiceberg_catalog_config(ref="main")
            catalog = load_catalog(**config)

    """

    iceberg_warehouse_path: str = Field(
        default="s3://lake/warehouse",
        validation_alias=AliasChoices(
            "iceberg_warehouse_path", "PHLO_ICEBERG_WAREHOUSE_PATH", "ICEBERG_WAREHOUSE_PATH"
        ),
        description="S3 path for Iceberg warehouse",
    )
    iceberg_staging_path: str = Field(
        default="s3://lake/stage", description="S3 path for staging parquet files"
    )
    iceberg_default_namespace: str = Field(
        default="raw", description="Default namespace/schema for Iceberg tables"
    )
    iceberg_default_ref: str = Field(
        default="main", description="Default catalog ref/branch for Iceberg operations"
    )
    iceberg_s3_endpoint: str | None = Field(
        default="http://minio:10001",
        validation_alias=AliasChoices(
            "iceberg_s3_endpoint", "PHLO_ICEBERG_S3_ENDPOINT", "ICEBERG_S3_ENDPOINT"
        ),
        description="S3 endpoint URL for Iceberg I/O",
    )
    iceberg_s3_access_key: str = Field(
        default="minio",
        validation_alias=AliasChoices(
            "iceberg_s3_access_key",
            "PHLO_ICEBERG_S3_ACCESS_KEY",
            "ICEBERG_S3_ACCESS_KEY",
            "AWS_ACCESS_KEY_ID",
        ),
        description="S3 access key for Iceberg I/O",
    )
    iceberg_s3_secret_key: str = Field(
        default="minio123",
        validation_alias=AliasChoices(
            "iceberg_s3_secret_key",
            "PHLO_ICEBERG_S3_SECRET_KEY",
            "ICEBERG_S3_SECRET_KEY",
            "AWS_SECRET_ACCESS_KEY",
        ),
        description="S3 secret key for Iceberg I/O",
    )
    iceberg_s3_region: str = Field(
        default="us-east-1",
        validation_alias=AliasChoices(
            "iceberg_s3_region",
            "PHLO_ICEBERG_S3_REGION",
            "ICEBERG_S3_REGION",
            "AWS_REGION",
            "AWS_DEFAULT_REGION",
        ),
        description="S3 region for Iceberg I/O",
    )
    iceberg_catalog_uri: str = Field(
        default="http://nessie:19120/iceberg",
        validation_alias=AliasChoices(
            "iceberg_catalog_uri", "PHLO_ICEBERG_CATALOG_URI", "ICEBERG_CATALOG_URI"
        ),
        description="Iceberg REST catalog endpoint base URI",
    )

    def get_iceberg_warehouse_for_branch(self, branch: str = "main") -> str:
        """Get the warehouse path for a specific branch.

        Currently returns the same warehouse path for all branches.
        Future versions may support branch-specific warehouse locations.

        Args:
            branch: Nessie branch name.

        Returns:
            str: Warehouse path for the requested branch.

        Example:
            Get warehouse path::

                settings = get_settings()
                path = settings.get_iceberg_warehouse_for_branch("main")
                print(f"Warehouse: {path}")  # s3://lake/warehouse

        """
        return self.iceberg_warehouse_path

    def get_pyiceberg_catalog_config(self, ref: str = "main") -> dict:
        """Build PyIceberg REST catalog configuration dictionary.

        Constructs a configuration dict suitable for passing to
        ``pyiceberg.catalog.load_catalog()``. Resolves service URLs
        dynamically based on environment configuration.

        Args:
            ref: Nessie reference (branch or tag) to target.

        Returns:
            dict: PyIceberg catalog configuration with keys:
                - ``type``: Always "rest"
                - ``uri``: Full catalog URI including ref path
                - ``warehouse``: Warehouse path
                - ``s3.endpoint``: S3 endpoint URL
                - ``s3.access-key-id``: S3 access key
                - ``s3.secret-access-key``: S3 secret key
                - ``s3.path-style-access``: Always "true" (MinIO compatibility)
                - ``s3.region``: S3 region

        Example:
            Configure PyIceberg catalog::

                from pyiceberg.catalog import load_catalog
                from phlo_iceberg.settings import get_settings

                settings = get_settings()
                config = settings.get_pyiceberg_catalog_config(ref="dev")
                catalog = load_catalog("dev_catalog", **config)

                # Now use catalog
                tables = catalog.list_tables("raw")

        """
        catalog_uri = _resolve_service_url(self.iceberg_catalog_uri, port_env_var="NESSIE_PORT")
        s3_endpoint = _resolve_service_url(self.iceberg_s3_endpoint, port_env_var="MINIO_API_PORT")
        config = {
            "type": "rest",
            "uri": f"{catalog_uri}/{ref}",
            "warehouse": self.get_iceberg_warehouse_for_branch(ref),
            "s3.endpoint": s3_endpoint,
            "s3.access-key-id": self.iceberg_s3_access_key,
            "s3.secret-access-key": self.iceberg_s3_secret_key,
            "s3.path-style-access": "true",
            "s3.region": self.iceberg_s3_region,
        }
        validate_pyiceberg_rest_catalog_config(config)
        return config


@project_root_cached
def get_settings(project_root: Path) -> IcebergSettings:
    """Get cached Iceberg settings for the selected project root.

    Settings are cached per resolved project root, with up to 16 entries,
    to avoid repeatedly loading and parsing configuration.

    Args:
        project_root: Resolved project root used for cache selection.

    Returns:
        IcebergSettings: Cached settings with all
            configuration values resolved from environment and files.

    Example:
        Get settings::

            from phlo_iceberg.settings import get_settings

            settings = get_settings()
            print(f"Warehouse: {settings.iceberg_warehouse_path}")
            print(f"Default namespace: {settings.iceberg_default_namespace}")

    Note:
        Settings are cached per project root. To force a reload after
        configuration changes, clear the cache with::

            get_settings.cache_clear()

    """
    return IcebergSettings()

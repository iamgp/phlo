"""Phlo OpenMetadata integration package.

This package provides the OpenMetadata catalog integration for Phlo,
enabling metadata synchronization, lineage tracking, and quality
check publishing to an OpenMetadata data catalog.

Key components:
    - OpenMetadataClient: REST API client for OpenMetadata
    - OpenMetadataSettings: Configuration management
    - QualityCheckPublisher: Publishes quality checks to OM
    - DbtManifestParser: Syncs dbt documentation to OM
    - LineageExtractor: Extracts and publishes lineage

Example:
    >>> from phlo_openmetadata import OpenMetadataClient, get_settings
    >>> settings = get_settings()
    >>> client = OpenMetadataClient(
    ...     base_url=settings.openmetadata_uri(),
    ...     username=settings.openmetadata_username,
    ...     password=settings.openmetadata_password,
    ... )
    >>> client.health_check()
    True

"""

from phlo_openmetadata.dbt_sync import DbtManifestParser
from phlo_openmetadata.openmetadata import (
    OpenMetadataClient,
    OpenMetadataColumn,
    OpenMetadataLineageEdge,
    OpenMetadataTable,
)
from phlo_openmetadata.settings import OpenMetadataSettings, get_settings

__all__ = [
    "DbtManifestParser",
    "OpenMetadataSettings",
    "OpenMetadataClient",
    "OpenMetadataColumn",
    "OpenMetadataLineageEdge",
    "OpenMetadataTable",
    "get_settings",
]

"""
Phlo Catalog Module - OpenMetadata Integration.

Provides metadata synchronization, lineage tracking, and data catalog integration
with OpenMetadata.

Submodules:
    - openmetadata: REST API client
    - nessie: Iceberg table metadata extraction
    - dbt_sync: dbt manifest parsing and syncing
    - lineage: Lineage graph construction and publishing
    - quality_sync: Quality check synchronization to OpenMetadata
    - sensors: Dagster sensors for automatic metadata sync
"""

from phlo.catalog.openmetadata import (
    OpenMetadataClient,
    OpenMetadataColumn,
    OpenMetadataLineageEdge,
    OpenMetadataTable,
)
from phlo.catalog.quality_sync import (
    QualityCheckMapper,
    QualityCheckPublisher,
)

__all__ = [
    "OpenMetadataClient",
    "OpenMetadataTable",
    "OpenMetadataColumn",
    "OpenMetadataLineageEdge",
    "QualityCheckMapper",
    "QualityCheckPublisher",
]

__version__ = "1.0.0"

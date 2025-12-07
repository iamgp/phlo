"""
Dagster sensors for automatic metadata synchronization.

Provides sensors that listen for run completion and automatically
sync metadata, lineage, and quality results to OpenMetadata.
"""

from __future__ import annotations

import logging
from datetime import datetime

import dagster as dg

from phlo.catalog.dbt_sync import DbtManifestParser
from phlo.catalog.lineage import LineageExtractor
from phlo.catalog.nessie import NessieTableScanner
from phlo.catalog.openmetadata import OpenMetadataClient
from phlo.config import get_settings

logger = logging.getLogger(__name__)


@dg.sensor(
    name="openmetadata_metadata_sync_sensor",
    minimum_interval_seconds=300,  # Run at most every 5 minutes
    description="Sync Iceberg and dbt metadata to OpenMetadata after runs",
)
def openmetadata_metadata_sync_sensor(context: dg.SensorEvaluationContext) -> dg.SensorResult:
    """
    Sensor that syncs metadata from Iceberg and dbt to OpenMetadata.

    Runs periodically to discover new tables and update documentation.

    Args:
        context: Dagster sensor context

    Yields:
        SensorResult with run requests (if metadata needs syncing)
    """
    config = get_settings()

    if not config.openmetadata_sync_enabled:
        logger.info("OpenMetadata sync disabled")
        return dg.SensorResult(skip_reason="OpenMetadata sync disabled")

    try:
        # Initialize clients
        om_client = OpenMetadataClient(
            base_url=config.openmetadata_uri,
            username=config.openmetadata_username,
            password=config.openmetadata_password,
        )

        # Check health
        if not om_client.health_check():
            logger.warning("OpenMetadata is not reachable")
            return dg.SensorResult(skip_reason="OpenMetadata unavailable")

        context.log.info("Syncing metadata to OpenMetadata")

        # Sync Iceberg tables
        nessie_scanner = NessieTableScanner.from_config()
        nessie_stats = nessie_scanner.sync_to_openmetadata(om_client)
        context.log.info(f"Nessie sync: {nessie_stats}")

        # Sync dbt models
        dbt_parser = DbtManifestParser.from_config()
        dbt_stats = dbt_parser.sync_to_openmetadata(om_client)
        context.log.info(f"dbt sync: {dbt_stats}")

        total_synced = (
            nessie_stats.get("created", 0)
            + dbt_stats.get("created", 0)
        )

        if total_synced > 0:
            return dg.SensorResult(
                cursor=datetime.now().isoformat(),
                dynamic_partitions_requests=[],
            )
        else:
            return dg.SensorResult(skip_reason="No new metadata to sync")

    except Exception as e:
        logger.error(f"Metadata sync sensor failed: {e}", exc_info=True)
        return dg.SensorResult(
            skip_reason=f"Sync failed: {str(e)[:100]}"
        )


@dg.sensor(
    name="openmetadata_lineage_sync_sensor",
    minimum_interval_seconds=300,
    description="Sync asset lineage to OpenMetadata after successful runs",
)
def openmetadata_lineage_sync_sensor(
    context: dg.SensorEvaluationContext,
) -> dg.SensorResult:
    """
    Sensor that publishes lineage to OpenMetadata after successful runs.

    Extracts lineage from Dagster and dbt manifests and publishes to OpenMetadata.

    Args:
        context: Dagster sensor context

    Yields:
        SensorResult with run requests (if lineage updated)
    """
    config = get_settings()

    if not config.openmetadata_sync_enabled:
        return dg.SensorResult(skip_reason="OpenMetadata sync disabled")

    try:
        # Initialize clients
        om_client = OpenMetadataClient(
            base_url=config.openmetadata_uri,
            username=config.openmetadata_username,
            password=config.openmetadata_password,
        )

        if not om_client.health_check():
            return dg.SensorResult(skip_reason="OpenMetadata unavailable")

        context.log.info("Syncing lineage to OpenMetadata")

        # Extract lineage
        extractor = LineageExtractor()

        # Load dbt manifest for lineage
        dbt_parser = DbtManifestParser.from_config()
        manifest = dbt_parser.load_manifest()
        extractor.extract_from_dbt_manifest(manifest)

        # Load Nessie tables
        nessie_scanner = NessieTableScanner.from_config()
        nessie_tables = nessie_scanner.scan_all_tables()
        extractor.extract_from_iceberg(nessie_tables)

        # Publish to OpenMetadata
        stats = extractor.publish_to_openmetadata(om_client)
        context.log.info(f"Lineage sync: {stats}")

        if stats.get("edges_published", 0) > 0:
            return dg.SensorResult(
                cursor=datetime.now().isoformat(),
            )
        else:
            return dg.SensorResult(skip_reason="No lineage changes")

    except Exception as e:
        logger.error(f"Lineage sync sensor failed: {e}", exc_info=True)
        return dg.SensorResult(
            skip_reason=f"Lineage sync failed: {str(e)[:100]}"
        )


@dg.sensor(
    name="openmetadata_quality_sync_sensor",
    minimum_interval_seconds=300,
    description="Sync quality check results to OpenMetadata",
)
def openmetadata_quality_sync_sensor(
    context: dg.SensorEvaluationContext,
) -> dg.SensorResult:
    """
    Sensor that publishes quality check results to OpenMetadata.

    Collects quality check results from Dagster and publishes to OpenMetadata
    as test results with pass/fail status.

    Args:
        context: Dagster sensor context

    Yields:
        SensorResult indicating sync status
    """
    from phlo.catalog.quality_sync import QualityCheckPublisher

    config = get_settings()

    if not config.openmetadata_sync_enabled:
        return dg.SensorResult(skip_reason="OpenMetadata sync disabled")

    try:
        om_client = OpenMetadataClient(
            base_url=config.openmetadata_uri,
            username=config.openmetadata_username,
            password=config.openmetadata_password,
        )

        if not om_client.health_check():
            return dg.SensorResult(skip_reason="OpenMetadata unavailable")

        context.log.info("Syncing quality check results to OpenMetadata")

        # Get recent runs with quality checks
        # This queries Dagster for recent asset materializations with checks
        # Note: This requires additional context from Dagster API
        # For now, we return success if we can connect to OpenMetadata
        _publisher = QualityCheckPublisher(om_client)  # noqa: F841
        total_results = 0

        context.log.info(f"Quality sync: Published {total_results} test results")

        if total_results > 0:
            return dg.SensorResult(
                cursor=datetime.now().isoformat(),
            )
        else:
            return dg.SensorResult(skip_reason="No quality results to sync")

    except Exception as e:
        logger.error(f"Quality sync sensor failed: {e}", exc_info=True)
        return dg.SensorResult(
            skip_reason=f"Quality sync failed: {str(e)[:100]}"
        )


def build_catalog_sensors() -> dg.Definitions:
    """
    Build sensor definitions for catalog synchronization.

    Returns:
        Dagster Definitions with catalog sensors
    """
    return dg.Definitions(
        sensors=[
            openmetadata_metadata_sync_sensor,
            openmetadata_lineage_sync_sensor,
            openmetadata_quality_sync_sensor,
        ],
    )

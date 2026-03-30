"""Freshness check plugin for validating data timeliness.

This module provides the FreshnessCheckPlugin, which enables validation of
data freshness based on timestamp columns. It helps ensure that data is
being updated within acceptable timeframes, critical for time-sensitive
analytics and operational dashboards.

Example:
    Using the freshness check plugin::

        from datetime import datetime, timedelta
        from phlo_core.quality.freshness_check import FreshnessCheckPlugin

        # Create the plugin
        plugin = FreshnessCheckPlugin()

        # Check that data is no more than 24 hours old
        check = plugin.create_check(
            timestamp_column="updated_at",
            max_age_hours=24.0
        )

        # Check against a specific reference time
        reference = datetime.now() - timedelta(hours=12)
        check_with_ref = plugin.create_check(
            timestamp_column="created_at",
            max_age_hours=6.0,
            reference_time=reference
        )

"""

from datetime import datetime
from typing import Any

from phlo.plugins import PluginMetadata, QualityCheckPlugin


class FreshnessCheckPlugin(QualityCheckPlugin[Any]):
    """Plugin for performing freshness validation on timestamped data.

    This plugin creates freshness check instances that validate whether data
    is within an acceptable age based on a timestamp column. It compares
    the maximum timestamp value in the data against a reference time (defaults
    to current time) to ensure data is fresh enough for use.

    The freshness check is particularly useful for:
        - Monitoring data pipeline latency
        - Ensuring dashboards show current data
        - Detecting stale data sources
        - Validating ETL job success

    Attributes:
        metadata: PluginMetadata containing name, version, description,
            author, and tags for this plugin.

    Example:
        Basic freshness check with current time as reference::

            from phlo_core.quality.freshness_check import FreshnessCheckPlugin

            plugin = FreshnessCheckPlugin()
            check = plugin.create_check(
                timestamp_column="event_time",
                max_age_hours=2.0
            )

        Freshness check with custom reference time::

            from datetime import datetime, timedelta

            yesterday = datetime.now() - timedelta(days=1)
            check = plugin.create_check(
                timestamp_column="ingested_at",
                max_age_hours=1.0,
                reference_time=yesterday
            )

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the freshness-check plugin.

        Returns:
            PluginMetadata: Metadata including name ("freshness_check"),
                version ("0.1.0"), description ("Freshness checks for timestamped data"),
                author ("Phlo Team"), and tags (["quality", "freshness"]).

        """
        return PluginMetadata(
            name="freshness_check",
            version="0.1.0",
            description="Freshness checks for timestamped data",
            author="Phlo Team",
            tags=["quality", "freshness"],
        )

    def create_check(
        self,
        timestamp_column: str,
        max_age_hours: float,
        reference_time: datetime | None = None,
    ) -> Any:
        """Create a freshness check instance.

        Creates and returns a configured FreshnessCheck instance from phlo_pandera
        that validates data freshness based on timestamps.

        Args:
            timestamp_column: Name of the timestamp column used for freshness
                calculations. This column must exist in the data and contain
                datetime values.
            max_age_hours: Maximum allowed age of data in hours. If the data's
                newest timestamp is older than this threshold relative to the
                reference time, the check fails.
            reference_time: Optional reference datetime for age evaluation.
                If None, uses the current time. Useful for testing or when
                validating against a specific point in time.

        Returns:
            Any: Configured FreshnessCheck instance ready to validate data.
            The returned object can be used with Pandera schemas or called
            directly with DataFrames.

        Example:
            Create a freshness check for recent data::

                from phlo_core.quality.freshness_check import FreshnessCheckPlugin

                plugin = FreshnessCheckPlugin()
                check = plugin.create_check(
                    timestamp_column="created_at",
                    max_age_hours=24.0
                )

            Create a freshness check with custom reference::

                from datetime import datetime, timedelta

                check_time = datetime.now() - timedelta(hours=12)
                check = plugin.create_check(
                    timestamp_column="updated_at",
                    max_age_hours=6.0,
                    reference_time=check_time
                )

        """
        from phlo_pandera.checks import FreshnessCheck

        return FreshnessCheck(
            timestamp_column=timestamp_column,
            max_age_hours=max_age_hours,
            reference_time=reference_time,
        )

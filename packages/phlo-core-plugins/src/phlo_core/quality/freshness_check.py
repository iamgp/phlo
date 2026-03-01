"""Freshness check plugin."""

from datetime import datetime
from typing import Any

from phlo.plugins import PluginMetadata, QualityCheckPlugin


class FreshnessCheckPlugin(QualityCheckPlugin[Any]):
    """Plugin for freshness checks."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the freshness-check plugin."""
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

        Args:
            timestamp_column: Timestamp column used for freshness calculations.
            max_age_hours: Maximum allowed age in hours.
            reference_time: Optional reference time for age evaluation.

        Returns:
            Configured freshness-check instance.
        """
        from phlo_pandera.checks import FreshnessCheck

        return FreshnessCheck(
            timestamp_column=timestamp_column,
            max_age_hours=max_age_hours,
            reference_time=reference_time,
        )

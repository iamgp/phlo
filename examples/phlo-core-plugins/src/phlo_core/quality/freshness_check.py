"""Freshness check plugin."""

from datetime import datetime

from phlo.plugins import PluginMetadata, QualityCheckPlugin
from phlo.quality.checks import FreshnessCheck


class FreshnessCheckPlugin(QualityCheckPlugin):
    """Plugin for freshness checks."""

    @property
    def metadata(self) -> PluginMetadata:
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
    ) -> FreshnessCheck:
        return FreshnessCheck(
            timestamp_column=timestamp_column,
            max_age_hours=max_age_hours,
            reference_time=reference_time,
        )

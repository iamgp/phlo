"""
Freshness Validator Resource for checking data freshness.

This module provides a Dagster resource for validating data freshness based on
configured thresholds.
"""

from datetime import datetime
from typing import Any

import dagster as dg
from dagster import (
    AssetExecutionContext,
    AssetKey,
    DagsterEventType,
    EventRecordsFilter,
)


class FreshnessValidatorResource(dg.ConfigurableResource):
    """Validates data freshness based on configured thresholds."""

    blocks_promotion: bool = False
    default_freshness_hours: int = 24

    def check_asset_freshness(
        self,
        context: AssetExecutionContext,
        asset_key: str,
        threshold_hours: int | None = None,
    ) -> dict[str, Any]:
        """
        Check freshness of a single asset.

        Args:
            context: Asset execution context
            asset_key: Asset key to check
            threshold_hours: Freshness threshold in hours (defaults to default_freshness_hours)

        Returns:
            {
                "fresh": bool,
                "age_hours": float or None,
                "threshold_hours": int,
                "last_updated": ISO timestamp or None
            }
        """
        threshold = threshold_hours or self.default_freshness_hours
        last_materialization = self._get_last_materialization(context, asset_key)

        if last_materialization is None:
            return {
                "fresh": False,
                "age_hours": float("inf"),
                "threshold_hours": threshold,
                "last_updated": None,
            }

        age = datetime.now() - last_materialization
        age_hours = age.total_seconds() / 3600
        fresh = age_hours <= threshold

        return {
            "fresh": fresh,
            "age_hours": round(age_hours, 2),
            "threshold_hours": threshold,
            "last_updated": last_materialization.isoformat(),
        }

    def _get_last_materialization(
        self, context: AssetExecutionContext, asset_key: str
    ) -> datetime | None:
        """Get timestamp of last materialization for asset."""
        instance = context.instance

        events = instance.get_event_records(
            event_records_filter=EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                asset_key=AssetKey([asset_key]),
            ),
            limit=1,
        )

        if not events:
            return None

        event_record = events[0]
        return datetime.fromtimestamp(event_record.timestamp)

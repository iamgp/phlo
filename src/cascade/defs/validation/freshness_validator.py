"""
Freshness Validator Resource for checking data freshness.

This module provides a Dagster resource for validating data freshness based on
Dagster FreshnessPolicy and configured thresholds.
"""

from datetime import datetime, timedelta
from typing import Any

import dagster as dg
from dagster import AssetKey, AssetExecutionContext, DagsterEventType, EventRecordsFilter


class FreshnessValidatorResource(dg.ConfigurableResource):
    """Validates data freshness based on FreshnessPolicy and config."""

    blocks_promotion: bool
    glucose_freshness_hours: int
    github_events_freshness_hours: int
    github_stats_freshness_hours: int

    def _get_threshold_for_asset(self, asset_key: str) -> int | None:
        """Get freshness threshold for an asset."""
        asset_to_threshold = {
            "dlt_glucose_entries": self.glucose_freshness_hours,
            "dlt_github_user_events": self.github_events_freshness_hours,
            "dlt_github_repo_stats": self.github_stats_freshness_hours,
        }
        return asset_to_threshold.get(asset_key)

    def check_asset_freshness(
        self,
        context,
        asset_key: str
    ) -> dict[str, Any]:
        """
        Check freshness of a single asset.

        Args:
            context: Asset execution context
            asset_key: Asset key to check (e.g., "dlt_glucose_entries")

        Returns:
            {
                "fresh": bool,
                "age_hours": float or None,
                "threshold_hours": int,
                "last_updated": ISO timestamp or None
            }
        """
        threshold_hours = self._get_threshold_for_asset(asset_key)
        if threshold_hours is None:
            return {
                "fresh": True,  # Unknown assets pass by default
                "age_hours": None,
                "threshold_hours": 0,
                "last_updated": None,
                "note": f"No freshness threshold configured for {asset_key}"
            }
        last_materialization = self._get_last_materialization(context, asset_key)

        if last_materialization is None:
            return {
                "fresh": False,
                "age_hours": float("inf"),
                "threshold_hours": threshold_hours,
                "last_updated": None
            }

        age = datetime.now() - last_materialization
        age_hours = age.total_seconds() / 3600
        fresh = age_hours <= threshold_hours

        return {
            "fresh": fresh,
            "age_hours": round(age_hours, 2),
            "threshold_hours": threshold_hours,
            "last_updated": last_materialization.isoformat()
        }

    def check_freshness(
        self,
        context
    ) -> dict[str, Any]:
        """
        Check Dagster FreshnessPolicy status for all assets.

        Args:
            context: Asset execution context

        Returns:
            {
                "all_fresh": bool,
                "blocks_promotion": bool,
                "violations": [
                    {
                        "asset": "dlt_glucose_entries",
                        "last_updated": ISO timestamp,
                        "age_hours": 36,
                        "threshold_hours": 24,
                        "severity": "fail"|"warn"
                    }
                ]
            }
        """
        assets_to_check = [
            ("dlt_glucose_entries", self.glucose_freshness_hours),
            ("dlt_github_user_events", self.github_events_freshness_hours),
            ("dlt_github_repo_stats", self.github_stats_freshness_hours),
        ]

        violations = []

        for asset_key, threshold_hours in assets_to_check:
            last_materialization = self._get_last_materialization(context, asset_key)

            if last_materialization is None:
                violations.append({
                    "asset": asset_key,
                    "last_updated": None,
                    "age_hours": float("inf"),
                    "threshold_hours": threshold_hours,
                    "severity": "fail" if self.blocks_promotion else "warn"
                })
                continue

            age = datetime.now() - last_materialization
            age_hours = age.total_seconds() / 3600

            if age_hours > threshold_hours:
                violations.append({
                    "asset": asset_key,
                    "last_updated": last_materialization.isoformat(),
                    "age_hours": round(age_hours, 2),
                    "threshold_hours": threshold_hours,
                    "severity": "fail" if self.blocks_promotion else "warn"
                })

        all_fresh = len(violations) == 0

        return {
            "all_fresh": all_fresh,
            "blocks_promotion": self.blocks_promotion,
            "violations": violations
        }

    def _get_last_materialization(
        self,
        context: AssetExecutionContext,
        asset_key: str
    ) -> datetime | None:
        """Get timestamp of last materialization for asset."""
        instance = context.instance

        events = instance.get_event_records(
            event_records_filter=EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                asset_key=AssetKey([asset_key])
            ),
            limit=1
        )

        if not events:
            return None

        # Get timestamp from event
        event_record = events[0]
        return datetime.fromtimestamp(event_record.timestamp)

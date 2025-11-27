"""Metrics collection from Prometheus, Iceberg, and Postgres."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

import psycopg2
import psycopg2.extras
import requests
from cachetools import TTLCache

from phlo.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class RunMetrics:
    """Metrics for a single asset run."""

    asset_name: str
    run_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    status: str = "running"  # running, success, failure
    rows_processed: int = 0
    bytes_written: int = 0


@dataclass
class AssetMetrics:
    """Aggregated metrics for an asset."""

    asset_name: str
    last_run: Optional[RunMetrics] = None
    last_10_runs: list[RunMetrics] = field(default_factory=list)
    average_duration: float = 0.0
    failure_rate: float = 0.0
    average_rows_per_run: float = 0.0
    data_growth_bytes: int = 0


@dataclass
class SummaryMetrics:
    """Summary metrics for the entire platform."""

    total_runs_24h: int = 0
    successful_runs_24h: int = 0
    failed_runs_24h: int = 0
    total_rows_processed_24h: int = 0
    total_bytes_written_24h: int = 0
    p50_duration_seconds: float = 0.0
    p95_duration_seconds: float = 0.0
    p99_duration_seconds: float = 0.0
    active_assets_count: int = 0
    assets_by_status: dict[str, int] = field(
        default_factory=lambda: {"success": 0, "warning": 0, "failure": 0}
    )


class MetricsCollector:
    """Collects metrics from Prometheus, Iceberg, and Postgres."""

    def __init__(self):
        """Initialize metrics collector."""
        self.config = get_settings()
        self._cache = TTLCache(maxsize=100, ttl=30)  # 30 second cache
        self._prometheus_url: Optional[str] = None

    @property
    def prometheus_url(self) -> Optional[str]:
        """Get Prometheus URL from config or environment."""
        if self._prometheus_url is None:
            # Try to get from environment or docker-compose discovery
            self._prometheus_url = "http://prometheus:9090"
        return self._prometheus_url

    def collect_summary(self, period_hours: int = 24) -> SummaryMetrics:
        """
        Collect summary metrics for the platform.

        Args:
            period_hours: Hours to look back (default: 24)

        Returns:
            SummaryMetrics with platform-wide metrics
        """
        cache_key = f"summary_{period_hours}h"
        if cache_key in self._cache:
            return self._cache[cache_key]

        metrics = SummaryMetrics()

        # Try to get Prometheus metrics
        try:
            metrics = self._collect_from_prometheus(period_hours)
        except Exception as e:
            logger.warning(f"Failed to collect from Prometheus: {e}")

        # Supplement with Postgres metrics
        try:
            postgres_metrics = self._collect_from_postgres(period_hours)
            metrics.total_rows_processed_24h = (
                postgres_metrics.get("rows_processed", 0)
            )
            metrics.total_bytes_written_24h = postgres_metrics.get("bytes_written", 0)
        except Exception as e:
            logger.warning(f"Failed to collect from Postgres: {e}")

        # Supplement with Iceberg stats
        try:
            iceberg_metrics = self._collect_from_iceberg()
            metrics.active_assets_count = iceberg_metrics.get("table_count", 0)
            metrics.data_growth_bytes = iceberg_metrics.get("total_bytes", 0)
        except Exception as e:
            logger.warning(f"Failed to collect from Iceberg: {e}")

        self._cache[cache_key] = metrics
        return metrics

    def collect_asset(self, asset_name: str, runs: int = 10) -> AssetMetrics:
        """
        Collect metrics for a specific asset.

        Args:
            asset_name: Name of the asset
            runs: Number of past runs to retrieve (default: 10)

        Returns:
            AssetMetrics with per-asset metrics
        """
        cache_key = f"asset_{asset_name}_{runs}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        metrics = AssetMetrics(asset_name=asset_name)

        # Collect from Postgres (Dagster event log)
        try:
            run_records = self._get_asset_runs_from_postgres(asset_name, limit=runs)
            if run_records:
                metrics.last_10_runs = run_records
                if run_records:
                    metrics.last_run = run_records[0]

                # Calculate averages
                durations = [
                    r.duration_seconds
                    for r in run_records
                    if r.duration_seconds is not None
                ]
                if durations:
                    metrics.average_duration = sum(durations) / len(durations)

                successful = sum(1 for r in run_records if r.status == "success")
                metrics.failure_rate = 1.0 - (successful / len(run_records))

                total_rows = sum(r.rows_processed for r in run_records)
                metrics.average_rows_per_run = total_rows / len(run_records)

        except Exception as e:
            logger.warning(f"Failed to collect asset metrics for {asset_name}: {e}")

        # Collect from Iceberg (table stats)
        try:
            iceberg_metrics = self._get_iceberg_table_stats(asset_name)
            metrics.data_growth_bytes = iceberg_metrics.get("total_bytes", 0)
        except Exception as e:
            logger.warning(f"Failed to get Iceberg stats for {asset_name}: {e}")

        self._cache[cache_key] = metrics
        return metrics

    def _collect_from_prometheus(self, period_hours: int) -> SummaryMetrics:
        """Collect metrics from Prometheus."""
        metrics = SummaryMetrics()

        if not self.prometheus_url:
            return metrics

        try:
            # Query for run counts
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={
                    "query": f'increase(dagster_runs_total{{status="success"}}[{period_hours}h])'
                },
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("data", {}).get("result"):
                    value = data["data"]["result"][0].get("value", [None, "0"])
                    metrics.successful_runs_24h = int(float(value[1]))

            # Query for failed runs
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={
                    "query": f'increase(dagster_runs_total{{status="failure"}}[{period_hours}h])'
                },
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("data", {}).get("result"):
                    value = data["data"]["result"][0].get("value", [None, "0"])
                    metrics.failed_runs_24h = int(float(value[1]))

            metrics.total_runs_24h = (
                metrics.successful_runs_24h + metrics.failed_runs_24h
            )

            # Query for latency percentiles
            for percentile in ["0.5", "0.95", "0.99"]:
                response = requests.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={
                        "query": f'histogram_quantile({percentile}, dagster_run_duration_seconds[{period_hours}h])'
                    },
                    timeout=5,
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("data", {}).get("result"):
                        value = data["data"]["result"][0].get("value", [None, "0"])
                        duration = float(value[1])
                        if percentile == "0.5":
                            metrics.p50_duration_seconds = duration
                        elif percentile == "0.95":
                            metrics.p95_duration_seconds = duration
                        elif percentile == "0.99":
                            metrics.p99_duration_seconds = duration

        except Exception as e:
            logger.debug(f"Prometheus collection failed: {e}")

        return metrics

    def _collect_from_postgres(self, period_hours: int) -> dict[str, Any]:
        """Collect metrics from Postgres."""
        metrics: dict[str, Any] = {}

        try:
            conn = psycopg2.connect(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                database=self.config.postgres_db,
                user=self.config.postgres_user,
                password=self.config.postgres_password,
            )
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            # Query Dagster events for metrics
            since = datetime.utcnow() - timedelta(hours=period_hours)
            cur.execute(
                """
                SELECT 
                    COUNT(*) as run_count,
                    SUM(CASE WHEN event_type = 'PIPELINE_SUCCESS' THEN 1 ELSE 0 END) as success_count
                FROM dagster_event_logs
                WHERE timestamp > %s
            """,
                (since,),
            )

            row = cur.fetchone()
            if row:
                metrics["runs"] = row["run_count"] or 0
                metrics["successful_runs"] = row["success_count"] or 0

            conn.close()

        except Exception as e:
            logger.debug(f"Postgres metrics collection failed: {e}")

        return metrics

    def _collect_from_iceberg(self) -> dict[str, Any]:
        """Collect metrics from Iceberg/Nessie."""
        metrics: dict[str, Any] = {}

        try:
            # Query Nessie for table listing
            nessie_url = self.config.nessie_api_v1_uri
            response = requests.get(f"{nessie_url}/trees", timeout=5)

            if response.status_code == 200:
                data = response.json()
                # Get table count from all namespaces
                tables_count = 0
                total_bytes = 0

                # Try to query each namespace
                namespaces = data.get("trees", [])
                for namespace in namespaces:
                    ns_name = namespace.get("name")
                    if ns_name:
                        try:
                            ns_response = requests.get(
                                f"{nessie_url}/namespaces/{ns_name}/tables",
                                timeout=5,
                            )
                            if ns_response.status_code == 200:
                                ns_data = ns_response.json()
                                tables_count += len(ns_data.get("tables", []))
                        except Exception:
                            pass

                metrics["table_count"] = tables_count
                metrics["total_bytes"] = total_bytes

        except Exception as e:
            logger.debug(f"Iceberg metrics collection failed: {e}")

        return metrics

    def _get_asset_runs_from_postgres(
        self, asset_name: str, limit: int = 10
    ) -> list[RunMetrics]:
        """Get past runs for an asset from Postgres."""
        runs = []

        try:
            conn = psycopg2.connect(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                database=self.config.postgres_db,
                user=self.config.postgres_user,
                password=self.config.postgres_password,
            )
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            # Mock implementation - actual query depends on Dagster schema
            # This is a placeholder for the actual implementation
            cur.execute(
                """
                SELECT run_id, start_time, end_time, status
                FROM dagster_runs
                WHERE asset_name = %s
                ORDER BY start_time DESC
                LIMIT %s
            """,
                (asset_name, limit),
            )

            for row in cur.fetchall():
                if row:
                    start = row.get("start_time")
                    end = row.get("end_time")
                    duration = None
                    if start and end:
                        duration = (end - start).total_seconds()

                    runs.append(
                        RunMetrics(
                            asset_name=asset_name,
                            run_id=row.get("run_id", ""),
                            start_time=start,
                            end_time=end,
                            duration_seconds=duration,
                            status=row.get("status", "unknown"),
                        )
                    )

            conn.close()

        except Exception as e:
            logger.debug(f"Failed to get asset runs from Postgres: {e}")

        return runs

    def _get_iceberg_table_stats(self, table_name: str) -> dict[str, Any]:
        """Get table statistics from Iceberg."""
        stats: dict[str, Any] = {}

        try:
            # Query Trino for table metadata
            # This would typically be done via PyIceberg or direct Trino query
            # Placeholder implementation
            stats["total_bytes"] = 0
            stats["row_count"] = 0

        except Exception as e:
            logger.debug(f"Failed to get Iceberg stats for {table_name}: {e}")

        return stats


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

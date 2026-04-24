"""HTTP client helpers for phlo-mcp."""

from __future__ import annotations

from typing import Any

import httpx
from opentelemetry import trace

from phlo_mcp.config import McpConfig


class PhloApiClient:
    """Small typed wrapper around phlo-api observability routes."""

    def __init__(self, config: McpConfig, *, tracer_name: str = "phlo.mcp") -> None:
        self._config = config
        self._tracer = trace.get_tracer(tracer_name)

    @property
    def api_base_url(self) -> str:
        return self._config.api_base_url

    def get_platform_health(self) -> dict[str, Any]:
        return self._get_json("/api/observability/health")

    def get_service_status(self) -> list[dict[str, Any]] | dict[str, Any]:
        return self._get_json("/api/observability/services")

    def get_recent_alerts(self, limit: int = 5) -> list[dict[str, Any]] | dict[str, Any]:
        return self._get_json("/api/observability/alerts", params={"limit": limit})

    def get_dashboard_links(self) -> list[dict[str, Any]] | dict[str, Any]:
        return self._get_json("/api/observability/dashboards")

    def get_run_logs(
        self,
        run_id: str,
        *,
        level: str | None = None,
        limit: int = 200,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        if level:
            params["level"] = level
        return self._get_json(f"/api/loki/runs/{run_id}", params=params)

    def get_materialization_history(
        self,
        asset_key_path: str,
        *,
        limit: int = 10,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json(
            f"/api/dagster/assets/{asset_key_path}/history", params={"limit": limit}
        )

    def get_run_trace_spans(
        self,
        run_id: str,
        *,
        limit: int = 500,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json(f"/api/observability/traces/runs/{run_id}", params={"limit": limit})

    def get_logs_query_link(self, service: str | None = None) -> dict[str, Any]:
        params = {"service": service} if service else None
        return self._get_json("/api/observability/links/logs", params=params)

    def get_metrics_query_link(self, metric: str | None = None) -> dict[str, Any]:
        params = {"metric": metric} if metric else None
        return self._get_json("/api/observability/links/metrics", params=params)

    def _get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        url = f"{self.api_base_url}{path}"
        with self._tracer.start_as_current_span(
            "http.client GET",
            attributes={
                "http.request.method": "GET",
                "url.full": url,
            },
        ):
            response = httpx.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()

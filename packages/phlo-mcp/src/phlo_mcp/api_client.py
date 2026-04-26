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

    @property
    def headers(self) -> dict[str, str]:
        if self._config.api_token:
            return {"Authorization": f"Bearer {self._config.api_token}"}
        return {}

    def get_platform_health(self) -> dict[str, Any]:
        return self._get_json("/api/observability/health")

    def get_config(self) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json("/api/config")

    def get_plugins(self) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json("/api/plugins")

    def get_services(self) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json("/api/services")

    def get_service_info(self, service_name: str) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json(f"/api/services/{service_name}")

    def get_assets(self) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json("/api/dagster/assets")

    def get_asset_details(self, asset_key_path: str) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json(f"/api/dagster/assets/{asset_key_path}")

    def get_contracts(self) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json("/api/contracts")

    def get_contract(self, table_name: str) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json(f"/api/contracts/{table_name}")

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

    def get_trace_spans(
        self,
        *,
        run_id: str | None = None,
        asset_key: str | None = None,
        job_name: str | None = None,
        service_name: str | None = None,
        span_name: str | None = None,
        status_code: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        limit: int = 500,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        for key, value in {
            "run_id": run_id,
            "asset_key": asset_key,
            "job_name": job_name,
            "service_name": service_name,
            "span_name": span_name,
            "status_code": status_code,
            "start_time": start_time,
            "end_time": end_time,
        }.items():
            if value:
                params[key] = value
        return self._get_json("/api/observability/traces", params=params)

    def get_metrics_query_link(self, metric: str | None = None) -> dict[str, Any]:
        params = {"metric": metric} if metric else None
        return self._get_json("/api/observability/links/metrics", params=params)

    def materialize_asset(
        self,
        asset_key_path: str,
        *,
        dry_run: bool = True,
        partition_key: str | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        payload: dict[str, Any] = {"dry_run": dry_run}
        if partition_key:
            payload["partition_key"] = partition_key
        return self._post_json(f"/api/dagster/assets/{asset_key_path}/materialize", json=payload)

    def retry_run(
        self,
        run_id: str,
        *,
        dry_run: bool = True,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        return self._post_json(f"/api/dagster/runs/{run_id}/retry", json={"dry_run": dry_run})

    def get_run_status(self, run_id: str) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json(f"/api/dagster/runs/{run_id}/status")

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
            response = httpx.get(url, params=params, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            return response.json()

    def _post_json(
        self,
        path: str,
        *,
        json: dict[str, Any],
    ) -> dict[str, Any] | list[dict[str, Any]]:
        url = f"{self.api_base_url}{path}"
        with self._tracer.start_as_current_span(
            "http.client POST",
            attributes={
                "http.request.method": "POST",
                "url.full": url,
            },
        ):
            response = httpx.post(url, json=json, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            return response.json()

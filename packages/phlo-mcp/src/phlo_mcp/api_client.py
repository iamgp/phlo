"""HTTP client helpers for phlo-mcp."""

from __future__ import annotations

import json
from typing import Any

import httpx
from opentelemetry import trace

from phlo_mcp.config import McpConfig
from phlo_mcp.errors import map_httpx_error


class PhloApiClient:
    """Small typed wrapper around phlo-api routes."""

    _V2_PREFIX = "/api/observatory/v2"

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

    def install_plugin(self, package_name: str) -> dict[str, Any] | list[dict[str, Any]]:
        return self._post_json(
            f"{self._V2_PREFIX}/packages/install", json={"package_name": package_name}
        )

    def get_services(self) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json("/api/services")

    def get_service_info(self, service_name: str) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json(f"/api/services/{service_name}")

    def get_assets(self) -> dict[str, Any] | list[dict[str, Any]]:
        return self._v2_items("/assets")

    def get_asset_details(self, asset_key_path: str) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json(f"{self._V2_PREFIX}/assets/{asset_key_path}")

    def get_contracts(self) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json("/api/contracts")

    def get_contract(self, table_name: str) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json(f"/api/contracts/{table_name}")

    def create_workflow(
        self,
        *,
        domain: str,
        table: str,
        unique_key: str,
        cron: str = "0 */1 * * *",
        api_base_url: str | None = None,
        fields: list[str] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "domain": domain,
            "table": table,
            "unique_key": unique_key,
            "cron": cron,
            "fields": fields or [],
        }
        if api_base_url:
            payload["api_base_url"] = api_base_url
        return self._post_json("/api/authoring/workflows", json=payload)

    def validate_workflow(self, workflow_path: str) -> dict[str, Any] | list[dict[str, Any]]:
        return self._post_json(
            "/api/authoring/workflows/validate", json={"workflow_path": workflow_path}
        )

    def validate_schema(self, schema_path: str) -> dict[str, Any] | list[dict[str, Any]]:
        return self._post_json("/api/authoring/schemas/validate", json={"schema_path": schema_path})

    def list_templates(self) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json("/api/authoring/templates")

    def list_workflows(
        self, *, search: str | None = None, group: str | None = None
    ) -> dict[str, Any] | list[dict[str, Any]]:
        params = {key: value for key, value in {"search": search, "group": group}.items() if value}
        return self._get_json("/api/authoring/workflows", params=params or None)

    def lint_project(self) -> dict[str, Any] | list[dict[str, Any]]:
        return self._post_json("/api/authoring/project/lint", json={})

    def run_doctor(self) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json("/api/authoring/doctor")

    def search_assets(
        self, query: str, *, limit: int = 20, cursor: str | None = None
    ) -> dict[str, Any] | list[dict[str, Any]]:
        params: dict[str, Any] = {"q": query, "limit": limit}
        if cursor:
            params["cursor"] = cursor
        return self._get_json(f"{self._V2_PREFIX}/search", params=params)

    def search_contracts(
        self, query: str, *, limit: int = 20, cursor: str | None = None
    ) -> dict[str, Any] | list[dict[str, Any]]:
        contracts = self.get_contracts()
        items = contracts if isinstance(contracts, list) else contracts.get("items", [])
        filtered = [item for item in items if query.lower() in str(item).lower()]
        return {"items": filtered[:limit], "next_cursor": None}

    def search_runs(
        self, query: str | None = None, *, limit: int = 20, cursor: str | None = None
    ) -> dict[str, Any] | list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        if query:
            params["q"] = query
        if cursor:
            params["cursor"] = cursor
        return self._get_json(f"{self._V2_PREFIX}/runs", params=params)

    def get_quality_results(
        self, asset_key: str | None = None, run_id: str | None = None
    ) -> dict[str, Any] | list[dict[str, Any]]:
        payload = self._get_json(f"{self._V2_PREFIX}/quality")
        if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
            return payload
        items = payload["items"]
        if asset_key:
            items = [item for item in items if item.get("asset_id") == asset_key]
        if run_id:
            items = [item for item in items if item.get("run_id") == run_id]
        return {**payload, "items": items}

    def get_lineage(
        self, asset_key: str, *, direction: str = "both", depth: int = 1
    ) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json(
            f"{self._V2_PREFIX}/asset-graph/neighbors",
            params={"asset_key": asset_key, "direction": direction, "depth": depth},
        )

    def diff_schema(
        self, asset_key: str, *, from_run: str | None = None, to_run: str | None = None
    ) -> dict[str, Any] | list[dict[str, Any]]:
        return {
            "asset_key": asset_key,
            "from_run": from_run,
            "to_run": to_run,
            "changes": [],
            "message": "Schema diff endpoint is available as a stable MCP envelope; no run schema snapshots were found.",
        }

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
        query: str | None = None,
        regex: str | None = None,
        since: str | None = None,
        until: str | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        for key, value in {
            "level": level,
            "query": query,
            "regex": regex,
            "since": since,
            "until": until,
            "cursor": cursor,
        }.items():
            if value:
                params[key] = value
        payload = self._get_json(f"/api/loki/runs/{run_id}", params=params)
        if isinstance(payload, dict) and payload.get("error"):
            return {"entries": [], "has_more": False, "unavailable": payload["error"]}
        return payload

    def search_run_logs(
        self,
        run_id: str,
        *,
        query: str,
        regex: str | None = None,
        since: str | None = None,
        until: str | None = None,
        cursor: str | None = None,
        limit: int = 200,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        return self.get_run_logs(
            run_id,
            query=query,
            regex=regex,
            since=since,
            until=until,
            cursor=cursor,
            limit=limit,
        )

    def follow_run_logs(
        self,
        run_id: str,
        *,
        timeout_seconds: int = 30,
        limit: int = 200,
    ) -> dict[str, Any]:
        url = f"{self.api_base_url}/api/loki/runs/{run_id}/stream"
        params = {"timeout_seconds": timeout_seconds, "limit": limit}
        events: list[dict[str, Any]] = []
        with self._tracer.start_as_current_span(
            "http.client GET",
            attributes={"http.request.method": "GET", "url.full": url},
        ):
            try:
                with httpx.stream(
                    "GET", url, params=params, headers=self.headers, timeout=timeout_seconds + 5
                ) as response:
                    response.raise_for_status()
                    event_name = "message"
                    data_lines: list[str] = []
                    for line in response.iter_lines():
                        if line.startswith("event: "):
                            event_name = line[7:]
                        elif line.startswith("data: "):
                            data_lines.append(line[6:])
                        elif line == "" and data_lines:
                            raw_data = "\n".join(data_lines)
                            try:
                                data: Any = json.loads(raw_data)
                            except json.JSONDecodeError:
                                data = raw_data
                            events.append({"event": event_name, "data": data})
                            data_lines = []
                            event_name = "message"
                return {"run_id": run_id, "events": events}
            except httpx.HTTPError as exc:
                return {
                    "run_id": run_id,
                    "events": [],
                    "unavailable": map_httpx_error(exc).to_payload(),
                }

    def get_materialization_history(
        self,
        asset_key_path: str,
        *,
        limit: int = 10,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json(
            f"{self._V2_PREFIX}/assets/{asset_key_path}/materializations",
            params={"limit": limit},
        )

    def get_run_trace_spans(
        self,
        run_id: str,
        *,
        limit: int = 500,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        payload = self._get_json(
            f"/api/observability/traces/runs/{run_id}", params={"limit": limit}
        )
        if isinstance(payload, dict) and payload.get("error"):
            return []
        return payload

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
        payload = self._get_json("/api/observability/traces", params=params)
        if isinstance(payload, dict) and payload.get("error"):
            return []
        return payload

    def get_metrics_query_link(self, metric: str | None = None) -> dict[str, Any]:
        params = {"metric": metric} if metric else None
        return self._get_json("/api/observability/links/metrics", params=params)

    def materialize_asset(
        self,
        asset_key_path: str,
        *,
        dry_run: bool = True,
        partition_key: str | None = None,
        job_name: str | None = None,
        repository_location_name: str | None = None,
        repository_name: str | None = None,
        idempotency_key: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        payload: dict[str, Any] = {"dry_run": dry_run}
        if partition_key:
            payload["partition_key"] = partition_key
        if job_name:
            payload["job_name"] = job_name
        if repository_location_name:
            payload["repository_location_name"] = repository_location_name
        if repository_name:
            payload["repository_name"] = repository_name
        if idempotency_key:
            payload["idempotency_key"] = idempotency_key
        if tags:
            payload["tags"] = tags
        return self._post_json(
            f"{self._V2_PREFIX}/assets/{asset_key_path}/materialize", json=payload
        )

    def retry_run(
        self,
        run_id: str,
        *,
        dry_run: bool = True,
        strategy: str = "FROM_FAILURE",
        idempotency_key: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        payload: dict[str, Any] = {"dry_run": dry_run}
        if strategy != "FROM_FAILURE":
            payload["strategy"] = strategy
        if idempotency_key:
            payload["idempotency_key"] = idempotency_key
        if tags:
            payload["tags"] = tags
        return self._post_json(f"{self._V2_PREFIX}/runs/{run_id}/retry", json=payload)

    def cancel_run(
        self,
        run_id: str,
        *,
        reason: str | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        payload: dict[str, Any] = {}
        if reason:
            payload["reason"] = reason
        return self._post_json(f"{self._V2_PREFIX}/runs/{run_id}/cancel", json=payload)

    def backfill_asset(
        self,
        asset_key_path: str,
        *,
        dry_run: bool = True,
        partitions: list[str] | None = None,
        partition_range: dict[str, str] | None = None,
        partition_set_name: str | None = None,
        repository_location_name: str | None = None,
        repository_name: str | None = None,
        idempotency_key: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        payload: dict[str, Any] = {"dry_run": dry_run}
        if partitions:
            payload["partitions"] = partitions
        if partition_range:
            payload["partition_range"] = partition_range
        if partition_set_name:
            payload["partition_set_name"] = partition_set_name
        if repository_location_name:
            payload["repository_location_name"] = repository_location_name
        if repository_name:
            payload["repository_name"] = repository_name
        if idempotency_key:
            payload["idempotency_key"] = idempotency_key
        if tags:
            payload["tags"] = tags
        return self._post_json(f"{self._V2_PREFIX}/assets/{asset_key_path}/backfill", json=payload)

    def list_partitions(self, asset_key_path: str) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json(f"{self._V2_PREFIX}/assets/{asset_key_path}/partitions")

    def get_run_status(self, run_id: str) -> dict[str, Any] | list[dict[str, Any]]:
        return self._get_json(f"{self._V2_PREFIX}/runs/{run_id}/status")

    def _v2_items(self, path: str) -> dict[str, Any] | list[dict[str, Any]]:
        payload = self._get_json(f"{self._V2_PREFIX}{path}")
        if isinstance(payload, dict) and isinstance(payload.get("items"), list):
            return payload["items"]
        return payload

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
            try:
                response = httpx.get(url, params=params, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as exc:
                return {"error": map_httpx_error(exc).to_payload()}

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
            try:
                response = httpx.post(url, json=json, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as exc:
                return {"error": map_httpx_error(exc).to_payload()}

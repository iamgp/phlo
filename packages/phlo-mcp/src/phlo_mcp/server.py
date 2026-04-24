"""MCP server exposing curated Phlo observability tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from opentelemetry import trace

from phlo_mcp.api_client import PhloApiClient
from phlo_mcp.config import McpConfig, config_from_env
from phlo_mcp.run_analysis import (
    render_run_trace_tree as render_log_trace_tree_text,
    render_span_tree,
    summarize_run_logs,
)
from phlo_mcp.tracing import configure_tracing


def create_server(config: McpConfig | None = None) -> FastMCP:
    """Create a configured FastMCP server instance."""
    resolved = config or config_from_env()
    configure_tracing(trace_file=resolved.trace_file)

    mcp = FastMCP("phlo", json_response=True)
    mcp.settings.host = resolved.host
    mcp.settings.port = resolved.port
    mcp.settings.streamable_http_path = resolved.streamable_http_path

    tracer = trace.get_tracer("phlo.mcp")
    client = PhloApiClient(resolved)

    @mcp.tool()
    def get_platform_health() -> dict[str, Any]:
        """Get Phlo platform observability health from phlo-api."""
        with tracer.start_as_current_span(
            "mcp.request",
            attributes={"mcp.tool.name": "get_platform_health"},
        ):
            with tracer.start_as_current_span(
                "mcp.tool.execute",
                attributes={"mcp.tool.name": "get_platform_health"},
            ):
                with tracer.start_as_current_span("phlo.observability.health"):
                    payload = client.get_platform_health()
                    return {"api_base_url": client.api_base_url, "payload": payload}

    @mcp.tool()
    def get_service_status() -> dict[str, Any]:
        """Get current service status snapshot from phlo-api."""
        with tracer.start_as_current_span(
            "mcp.request",
            attributes={"mcp.tool.name": "get_service_status"},
        ):
            with tracer.start_as_current_span(
                "mcp.tool.execute",
                attributes={"mcp.tool.name": "get_service_status"},
            ):
                with tracer.start_as_current_span("phlo.observability.services"):
                    services = client.get_service_status()
                    return {"api_base_url": client.api_base_url, "services": services}

    @mcp.tool()
    def get_recent_alerts(limit: int = 5) -> dict[str, Any]:
        """Get recent observability alerts from phlo-api."""
        with tracer.start_as_current_span(
            "mcp.request",
            attributes={"mcp.tool.name": "get_recent_alerts"},
        ):
            with tracer.start_as_current_span(
                "mcp.tool.execute",
                attributes={"mcp.tool.name": "get_recent_alerts"},
            ):
                with tracer.start_as_current_span("phlo.observability.alerts"):
                    alerts = client.get_recent_alerts(limit)
                    return {"api_base_url": client.api_base_url, "alerts": alerts}

    @mcp.tool()
    def get_dashboard_links() -> dict[str, Any]:
        """Get available observability dashboard links from phlo-api."""
        with tracer.start_as_current_span(
            "mcp.request",
            attributes={"mcp.tool.name": "get_dashboard_links"},
        ):
            with tracer.start_as_current_span(
                "mcp.tool.execute",
                attributes={"mcp.tool.name": "get_dashboard_links"},
            ):
                with tracer.start_as_current_span("phlo.observability.dashboards"):
                    dashboards = client.get_dashboard_links()
                    return {"api_base_url": client.api_base_url, "dashboards": dashboards}

    @mcp.tool()
    def get_logs_query_link(service: str | None = None) -> dict[str, Any]:
        """Get a backend-specific log query link, optionally filtered by service."""
        with tracer.start_as_current_span(
            "mcp.request",
            attributes={"mcp.tool.name": "get_logs_query_link"},
        ):
            with tracer.start_as_current_span(
                "mcp.tool.execute",
                attributes={"mcp.tool.name": "get_logs_query_link"},
            ):
                with tracer.start_as_current_span("phlo.observability.links.logs"):
                    payload = client.get_logs_query_link(service)
                    return {"api_base_url": client.api_base_url, "payload": payload}

    @mcp.tool()
    def get_metrics_query_link(metric: str | None = None) -> dict[str, Any]:
        """Get a backend-specific metrics query link, optionally filtered by metric."""
        with tracer.start_as_current_span(
            "mcp.request",
            attributes={"mcp.tool.name": "get_metrics_query_link"},
        ):
            with tracer.start_as_current_span(
                "mcp.tool.execute",
                attributes={"mcp.tool.name": "get_metrics_query_link"},
            ):
                with tracer.start_as_current_span("phlo.observability.links.metrics"):
                    payload = client.get_metrics_query_link(metric)
                    return {"api_base_url": client.api_base_url, "payload": payload}

    @mcp.tool()
    def get_materialization_history(asset_key_path: str, limit: int = 10) -> dict[str, Any]:
        """Get recent Dagster materializations for an asset."""
        with tracer.start_as_current_span(
            "mcp.request",
            attributes={"mcp.tool.name": "get_materialization_history"},
        ):
            with tracer.start_as_current_span(
                "mcp.tool.execute",
                attributes={"mcp.tool.name": "get_materialization_history"},
            ):
                with tracer.start_as_current_span("phlo.dagster.materialization_history"):
                    events = client.get_materialization_history(asset_key_path, limit=limit)
                    return {
                        "api_base_url": client.api_base_url,
                        "asset_key_path": asset_key_path,
                        "events": events,
                    }

    @mcp.tool()
    def get_run_logs(run_id: str, limit: int = 200, level: str | None = None) -> dict[str, Any]:
        """Get correlated logs for a specific run or materialization."""
        with tracer.start_as_current_span(
            "mcp.request",
            attributes={"mcp.tool.name": "get_run_logs"},
        ):
            with tracer.start_as_current_span(
                "mcp.tool.execute",
                attributes={"mcp.tool.name": "get_run_logs"},
            ):
                with tracer.start_as_current_span("phlo.loki.run_logs"):
                    payload = client.get_run_logs(run_id, limit=limit, level=level)
                    return {
                        "api_base_url": client.api_base_url,
                        "run_id": run_id,
                        "payload": payload,
                    }

    @mcp.tool()
    def get_run_trace_spans(run_id: str, limit: int = 500) -> dict[str, Any]:
        """Get OTEL spans correlated to a specific run id."""
        with tracer.start_as_current_span(
            "mcp.request",
            attributes={"mcp.tool.name": "get_run_trace_spans"},
        ):
            with tracer.start_as_current_span(
                "mcp.tool.execute",
                attributes={"mcp.tool.name": "get_run_trace_spans"},
            ):
                with tracer.start_as_current_span("phlo.observability.run_spans"):
                    payload = client.get_run_trace_spans(run_id, limit=limit)
                    return {
                        "api_base_url": client.api_base_url,
                        "run_id": run_id,
                        "spans": payload,
                    }

    def _inspect_materialization_payload(
        asset_key_path: str,
        *,
        limit: int,
        log_limit: int,
        span_limit: int = 500,
    ) -> dict[str, Any]:
        events = client.get_materialization_history(asset_key_path, limit=limit)
        if not isinstance(events, list) or not events:
            return {
                "api_base_url": client.api_base_url,
                "asset_key_path": asset_key_path,
                "events": events,
                "latest_run": None,
            }
        latest = events[0]
        run_id = latest.get("run_id")
        log_payload = client.get_run_logs(run_id, limit=log_limit) if run_id else {"entries": []}
        entries = log_payload.get("entries", []) if isinstance(log_payload, dict) else []
        span_payload = client.get_run_trace_spans(run_id, limit=span_limit) if run_id else []
        spans = span_payload if isinstance(span_payload, list) else []
        return {
            "api_base_url": client.api_base_url,
            "asset_key_path": asset_key_path,
            "events": events,
            "latest_run": {
                "run_id": run_id,
                "log_summary": summarize_run_logs(run_id or "unknown", entries),
                "span_count": len(spans),
                "trace_tree": render_span_tree(run_id or "unknown", spans)
                if spans
                else render_log_trace_tree_text(run_id or "unknown", entries),
                "trace_source": "spans" if spans else "logs",
                "spans": spans,
            },
        }

    @mcp.tool()
    def inspect_materialization(
        asset_key_path: str, limit: int = 5, log_limit: int = 200
    ) -> dict[str, Any]:
        """Inspect recent materializations and correlated logs for the latest run."""
        with tracer.start_as_current_span(
            "mcp.request",
            attributes={"mcp.tool.name": "inspect_materialization"},
        ):
            with tracer.start_as_current_span(
                "mcp.tool.execute",
                attributes={"mcp.tool.name": "inspect_materialization"},
            ):
                with tracer.start_as_current_span("phlo.materialization.inspect"):
                    return _inspect_materialization_payload(
                        asset_key_path,
                        limit=limit,
                        log_limit=log_limit,
                    )

    @mcp.tool()
    def get_asset_materialization_trace(
        asset_key_path: str, limit: int = 5, span_limit: int = 500
    ) -> dict[str, Any]:
        """Resolve the latest materialization for an asset and return its trace payload."""
        with tracer.start_as_current_span(
            "mcp.request",
            attributes={"mcp.tool.name": "get_asset_materialization_trace"},
        ):
            with tracer.start_as_current_span(
                "mcp.tool.execute",
                attributes={"mcp.tool.name": "get_asset_materialization_trace"},
            ):
                with tracer.start_as_current_span("phlo.materialization.trace"):
                    payload = _inspect_materialization_payload(
                        asset_key_path,
                        limit=limit,
                        log_limit=50,
                        span_limit=span_limit,
                    )
                    latest_run = payload.get("latest_run") or {}
                    return {
                        "api_base_url": client.api_base_url,
                        "asset_key_path": asset_key_path,
                        "run_id": latest_run.get("run_id"),
                        "trace_source": latest_run.get("trace_source"),
                        "span_count": latest_run.get("span_count"),
                        "spans": latest_run.get("spans", []),
                        "events": payload.get("events", []),
                    }

    @mcp.tool()
    def render_materialization_trace_tree(
        asset_key_path: str, limit: int = 5, span_limit: int = 500
    ) -> dict[str, Any]:
        """Render the latest materialization trace tree for an asset key path."""
        with tracer.start_as_current_span(
            "mcp.request",
            attributes={"mcp.tool.name": "render_materialization_trace_tree"},
        ):
            with tracer.start_as_current_span(
                "mcp.tool.execute",
                attributes={"mcp.tool.name": "render_materialization_trace_tree"},
            ):
                with tracer.start_as_current_span("phlo.materialization.trace_tree"):
                    payload = _inspect_materialization_payload(
                        asset_key_path,
                        limit=limit,
                        log_limit=50,
                        span_limit=span_limit,
                    )
                    latest_run = payload.get("latest_run") or {}
                    return {
                        "api_base_url": client.api_base_url,
                        "asset_key_path": asset_key_path,
                        "run_id": latest_run.get("run_id"),
                        "trace_source": latest_run.get("trace_source"),
                        "span_count": latest_run.get("span_count"),
                        "tree": latest_run.get("trace_tree"),
                    }

    @mcp.tool()
    def render_run_trace_tree(run_id: str, limit: int = 200) -> dict[str, Any]:
        """Render a run execution tree using real spans when available, else logs."""
        with tracer.start_as_current_span(
            "mcp.request",
            attributes={"mcp.tool.name": "render_run_trace_tree"},
        ):
            with tracer.start_as_current_span(
                "mcp.tool.execute",
                attributes={"mcp.tool.name": "render_run_trace_tree"},
            ):
                with tracer.start_as_current_span("phlo.run.trace_tree"):
                    span_payload = client.get_run_trace_spans(run_id, limit=max(limit, 500))
                    spans = span_payload if isinstance(span_payload, list) else []
                    if spans:
                        return {
                            "api_base_url": client.api_base_url,
                            "run_id": run_id,
                            "tree": render_span_tree(run_id, spans),
                            "span_count": len(spans),
                            "source": "spans",
                        }
                    payload = client.get_run_logs(run_id, limit=limit)
                    entries = payload.get("entries", []) if isinstance(payload, dict) else []
                    return {
                        "api_base_url": client.api_base_url,
                        "run_id": run_id,
                        "tree": render_log_trace_tree_text(run_id, entries, limit=limit),
                        "entry_count": len(entries),
                        "source": "logs",
                    }

    return mcp

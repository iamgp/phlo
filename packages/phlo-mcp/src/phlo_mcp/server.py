"""MCP server exposing curated Phlo observability tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from opentelemetry import trace

from phlo_mcp.api_client import PhloApiClient
from phlo_mcp.config import McpConfig, config_from_env
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

    return mcp

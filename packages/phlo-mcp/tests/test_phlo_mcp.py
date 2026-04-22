"""Tests for phlo-mcp package surfaces."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from phlo_mcp.api_client import PhloApiClient
from phlo_mcp.cli import parse_args
from phlo_mcp.config import McpConfig
from phlo_mcp.server import create_server
from phlo_mcp.tracing import render_trace_tree


class _FakeResponse:
    def __init__(self, payload):  # noqa: ANN001
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):  # noqa: ANN201
        return self._payload


def test_api_client_wraps_observability_routes(monkeypatch) -> None:
    seen_urls: list[str] = []

    def fake_get(url: str, params=None, timeout=10.0):  # noqa: ANN001
        seen_urls.append(url)
        if url.endswith("/health"):
            return _FakeResponse({"overall_status": "healthy"})
        if url.endswith("/services"):
            return _FakeResponse([{"name": "observability", "status": "unknown"}])
        if url.endswith("/alerts"):
            assert params == {"limit": 3}
            return _FakeResponse([{"title": "No alerts"}])
        if url.endswith("/dashboards"):
            return _FakeResponse([{"title": "ClickStack", "url": "http://example.test"}])
        if url.endswith("/links/logs"):
            return _FakeResponse({"url": "http://logs.test"})
        if url.endswith("/links/metrics"):
            return _FakeResponse({"url": "http://metrics.test"})
        raise AssertionError(f"Unexpected URL {url}")

    monkeypatch.setattr("phlo_mcp.api_client.httpx.get", fake_get)
    client = PhloApiClient(McpConfig(api_base_url="http://example.test"))

    assert client.get_platform_health()["overall_status"] == "healthy"
    assert client.get_service_status()[0]["name"] == "observability"
    assert client.get_recent_alerts(limit=3)[0]["title"] == "No alerts"
    assert client.get_dashboard_links()[0]["title"] == "ClickStack"
    assert client.get_logs_query_link()["url"] == "http://logs.test"
    assert client.get_metrics_query_link()["url"] == "http://metrics.test"
    assert seen_urls[0] == "http://example.test/api/observability/health"


def test_create_server_registers_expected_tools() -> None:
    server = create_server(McpConfig())

    tool_names = [tool.name for tool in server._tool_manager.list_tools()]

    assert tool_names == [
        "get_platform_health",
        "get_service_status",
        "get_recent_alerts",
        "get_dashboard_links",
        "get_logs_query_link",
        "get_metrics_query_link",
    ]


def test_parse_args_overrides_env(monkeypatch) -> None:
    monkeypatch.setenv("PHLO_MCP_API_BASE_URL", "http://env.test:4000")
    monkeypatch.setenv("PHLO_MCP_TRANSPORT", "stdio")
    monkeypatch.setenv("PHLO_MCP_PORT", "8000")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "phlo-mcp",
            "--transport",
            "streamable-http",
            "--api-base-url",
            "http://cli.test:4100",
            "--port",
            "9000",
        ],
    )

    config = parse_args()

    assert config.transport == "streamable-http"
    assert config.api_base_url == "http://cli.test:4100"
    assert config.port == 9000


def test_render_trace_tree_formats_tree(tmp_path: Path) -> None:
    trace_file = tmp_path / "trace.jsonl"
    spans = [
        {
            "name": "mcp.request",
            "context": {"trace_id": "a" * 32, "span_id": "1" * 16, "parent_id": None},
            "start_time_ns": 0,
            "end_time_ns": 4_000_000,
            "attributes": {},
            "status": {"code": "UNSET", "description": None},
        },
        {
            "name": "mcp.tool.execute",
            "context": {"trace_id": "a" * 32, "span_id": "2" * 16, "parent_id": "1" * 16},
            "start_time_ns": 1_000_000,
            "end_time_ns": 3_000_000,
            "attributes": {"mcp.tool.name": "get_platform_health"},
            "status": {"code": "UNSET", "description": None},
        },
    ]
    trace_file.write_text("\n".join(json.dumps(span) for span in spans), encoding="utf-8")

    rendered = render_trace_tree(trace_file)

    assert "Trace aaaaaaaa" in rendered
    assert "mcp.request 4.0ms" in rendered
    assert "mcp.tool.execute 2.0ms [tool=get_platform_health]" in rendered

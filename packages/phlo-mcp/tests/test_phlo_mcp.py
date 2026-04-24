"""Tests for phlo-mcp package surfaces."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from phlo_mcp.api_client import PhloApiClient
from phlo_mcp.cli import parse_args
from phlo_mcp.config import McpConfig
from phlo_mcp.run_analysis import (
    render_run_trace_tree as render_run_trace_tree_text,
    summarize_run_logs,
)
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
        if "/api/loki/runs/" in url:
            return _FakeResponse(
                {
                    "entries": [
                        {
                            "timestamp": "2026-01-01T00:00:00Z",
                            "level": "info",
                            "message": "materialization started",
                            "metadata": {
                                "service": "dagster",
                                "asset_key": "silver/orders",
                                "trace_id": "abc123",
                            },
                        }
                    ],
                    "has_more": False,
                }
            )
        if "/api/observability/traces/runs/" in url:
            return _FakeResponse(
                [
                    {
                        "timestamp": "2026-01-01T00:00:00Z",
                        "trace_id": "abc123",
                        "span_id": "root",
                        "parent_span_id": None,
                        "span_name": "materialize_orders",
                        "service_name": "dagster",
                        "span_kind": "INTERNAL",
                        "duration_ms": 12.5,
                        "status_code": "STATUS_CODE_OK",
                        "span_attributes": {
                            "phlo.run_id": "run-123",
                            "phlo.asset_key": "silver/orders",
                            "phlo.stage": "materialize",
                            "phlo.operation": "write",
                        },
                        "resource_attributes": {
                            "service.name": "dagster",
                            "service.version": "1.2.3",
                        },
                    }
                ]
            )
        if "/api/dagster/assets/" in url and url.endswith("/history"):
            return _FakeResponse([{"run_id": "run-123", "timestamp": "2026-01-01T00:00:00Z"}])
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
    assert client.get_run_logs("run-123")["entries"][0]["metadata"]["trace_id"] == "abc123"
    assert client.get_run_trace_spans("run-123")[0]["span_id"] == "root"
    assert client.get_materialization_history("silver/orders")[0]["run_id"] == "run-123"
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
        "get_materialization_history",
        "get_run_logs",
        "get_run_trace_spans",
        "inspect_materialization",
        "get_asset_materialization_trace",
        "render_materialization_trace_tree",
        "render_run_trace_tree",
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


def test_run_analysis_helpers_render_materialization_view() -> None:
    entries = [
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "level": "info",
            "message": "materialization started",
            "metadata": {"service": "dagster", "function": "step", "trace_id": "abc123"},
        },
        {
            "timestamp": "2026-01-01T00:00:01Z",
            "level": "info",
            "message": "materialization completed",
            "metadata": {"service": "dagster", "function": "step", "trace_id": "abc123"},
        },
    ]
    spans = [
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "trace_id": "abc123",
            "span_id": "root",
            "parent_span_id": None,
            "span_name": "materialize_orders",
            "service_name": "dagster",
            "span_kind": "INTERNAL",
            "status_code": "STATUS_CODE_OK",
            "duration_ms": 12.5,
            "span_attributes": {
                "phlo.asset_key": "silver/orders",
                "phlo.stage": "materialize",
                "phlo.operation": "write",
            },
            "resource_attributes": {"service.name": "dagster", "service.version": "1.2.3"},
        },
        {
            "timestamp": "2026-01-01T00:00:01Z",
            "trace_id": "abc123",
            "span_id": "child",
            "parent_span_id": "root",
            "span_name": "write_output",
            "service_name": "dagster",
            "span_kind": "INTERNAL",
            "status_code": "STATUS_CODE_OK",
            "duration_ms": 3.0,
            "span_attributes": {"phlo.stage": "materialize"},
            "resource_attributes": {"service.name": "dagster"},
        },
    ]

    summary = summarize_run_logs("run-123", entries)
    tree = render_run_trace_tree_text("run-123", entries)
    from phlo_mcp.run_analysis import render_span_tree

    span_tree = render_span_tree("run-123", spans)

    assert summary["trace_ids"] == ["abc123"]
    assert summary["entry_count"] == 2
    assert "Run run-123" in tree
    assert "trace abc123" in tree
    assert "materialization started" in tree
    assert "materialize_orders [internal ok]" in span_tree
    assert "write_output [internal ok]" in span_tree
    assert "asset=silver/orders" in span_tree
    assert "stage=materialize" in span_tree
    assert "service.version=1.2.3" in span_tree


def test_render_run_trace_tree_uses_most_recent_logs_with_limit() -> None:
    entries = [
        {
            "timestamp": "2026-01-01T00:00:03Z",
            "level": "error",
            "message": "latest failure",
            "metadata": {"service": "dagster"},
        },
        {
            "timestamp": "2026-01-01T00:00:02Z",
            "level": "warn",
            "message": "latest warning",
            "metadata": {"service": "dagster"},
        },
        {
            "timestamp": "2026-01-01T00:00:01Z",
            "level": "info",
            "message": "older info",
            "metadata": {"service": "dagster"},
        },
    ]

    tree = render_run_trace_tree_text("run-123", entries, limit=2)

    assert "latest failure" in tree
    assert "latest warning" in tree
    assert "older info" not in tree
    assert tree.index("latest warning") < tree.index("latest failure")


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

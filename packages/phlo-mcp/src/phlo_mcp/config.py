"""Configuration helpers for phlo-mcp."""

from __future__ import annotations

import os
from dataclasses import dataclass

_DEFAULT_API_BASE_URL = "http://127.0.0.1:4000"


@dataclass(frozen=True, slots=True)
class McpConfig:
    """Runtime configuration for the Phlo MCP server."""

    api_base_url: str = _DEFAULT_API_BASE_URL
    api_token: str | None = None
    enable_write_tools: bool = False
    trace_file: str | None = None
    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000
    streamable_http_path: str = "/mcp"


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "").lower() in {"1", "true", "yes", "on"}


def config_from_env() -> McpConfig:
    """Load MCP configuration from environment variables."""
    port = int(os.environ.get("PHLO_MCP_PORT", "8000"))
    return McpConfig(
        api_base_url=os.environ.get("PHLO_MCP_API_BASE_URL", _DEFAULT_API_BASE_URL).rstrip("/"),
        api_token=os.environ.get("PHLO_MCP_API_TOKEN") or None,
        enable_write_tools=_truthy_env("PHLO_MCP_ENABLE_WRITE_TOOLS"),
        trace_file=os.environ.get("PHLO_MCP_TRACE_FILE") or None,
        transport=os.environ.get("PHLO_MCP_TRANSPORT", "stdio"),
        host=os.environ.get("PHLO_MCP_HOST", "127.0.0.1"),
        port=port,
        streamable_http_path=os.environ.get("PHLO_MCP_HTTP_PATH", "/mcp"),
    )

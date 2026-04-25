"""Live smoke test for phlo-mcp against phlo-api, Dagster, and ClickStack.

This script is intentionally not part of the default unit test path. It expects
real local services and exercises the MCP stdio transport against a live
``phlo-api`` instance.

Examples:
    uv run python packages/phlo-mcp/tests/smoke_stack.py
    uv run python packages/phlo-mcp/tests/smoke_stack.py --run-id abc-123 --require-run-spans
    uv run python packages/phlo-mcp/tests/smoke_stack.py --asset-key silver/orders
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import anyio
import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_DEFAULT_API_BASE_URL = "http://127.0.0.1:4000"
_DEFAULT_DAGSTER_URL = "http://127.0.0.1:3000/graphql"
_DEFAULT_CLICKSTACK_QUERY_URL = "http://127.0.0.1:8123"
_SMOKE_RUN_ID = "phlo-mcp-smoke-no-such-run"


class SmokeFailure(RuntimeError):
    """Raised when a smoke check fails."""


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_root = Path(__file__).resolve().parents[3]

    if args.start_stack:
        _start_stack(repo_root)

    try:
        _wait_for_json(f"{args.api_base_url}/health", timeout_seconds=args.timeout_seconds)
        _check_phlo_api(args)
        _check_clickstack(args)
        anyio.run(_check_mcp_stdio, args, repo_root)
    except SmokeFailure as exc:
        print(f"SMOKE FAILED: {exc}", file=sys.stderr)
        return 1

    print("SMOKE PASSED: phlo-mcp, phlo-api, Dagster, and ClickStack paths are reachable")
    return 0


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--api-base-url",
        default=os.environ.get("PHLO_MCP_SMOKE_API_BASE_URL", _DEFAULT_API_BASE_URL),
        help="Base URL for the live phlo-api instance",
    )
    parser.add_argument(
        "--dagster-url",
        default=os.environ.get("PHLO_MCP_SMOKE_DAGSTER_URL", _DEFAULT_DAGSTER_URL),
        help="Dagster GraphQL URL reachable by phlo-api",
    )
    parser.add_argument(
        "--clickstack-query-url",
        default=os.environ.get(
            "PHLO_MCP_SMOKE_CLICKSTACK_QUERY_URL", _DEFAULT_CLICKSTACK_QUERY_URL
        ),
        help="ClickStack ClickHouse HTTP query URL reachable from this host",
    )
    parser.add_argument(
        "--clickstack-query-user",
        default=os.environ.get("PHLO_MCP_SMOKE_CLICKSTACK_QUERY_USER"),
        help="Optional ClickStack ClickHouse HTTP query user",
    )
    parser.add_argument(
        "--clickstack-query-password",
        default=os.environ.get("PHLO_MCP_SMOKE_CLICKSTACK_QUERY_PASSWORD", ""),
        help="Optional ClickStack ClickHouse HTTP query password",
    )
    parser.add_argument(
        "--api-token",
        default=os.environ.get("PHLO_MCP_SMOKE_API_TOKEN"),
        help="Optional bearer token for protected phlo-api instances",
    )
    parser.add_argument(
        "--run-id",
        default=os.environ.get("PHLO_MCP_SMOKE_RUN_ID", _SMOKE_RUN_ID),
        help="Run id to query through the MCP trace-span tool",
    )
    parser.add_argument(
        "--asset-key",
        default=os.environ.get("PHLO_MCP_SMOKE_ASSET_KEY"),
        help="Optional slash-delimited asset key to query for materialization history",
    )
    parser.add_argument(
        "--require-run-spans",
        action="store_true",
        default=_truthy_env("PHLO_MCP_SMOKE_REQUIRE_RUN_SPANS"),
        help="Fail unless --run-id returns at least one trace span",
    )
    parser.add_argument(
        "--require-materialization",
        action="store_true",
        default=_truthy_env("PHLO_MCP_SMOKE_REQUIRE_MATERIALIZATION"),
        help="Fail unless --asset-key returns at least one materialization event",
    )
    parser.add_argument(
        "--start-stack",
        action="store_true",
        default=_truthy_env("PHLO_MCP_SMOKE_START_STACK"),
        help="Run phlo service init/start before checking endpoints",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=float(os.environ.get("PHLO_MCP_SMOKE_TIMEOUT_SECONDS", "180")),
        help="How long to wait for live endpoints",
    )
    return parser.parse_args(argv)


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "").lower() in {"1", "true", "yes", "on"}


def _start_stack(repo_root: Path) -> None:
    _run(["phlo", "services", "init", "--profile", "api", "--profile", "observability"], repo_root)
    _run(
        [
            "phlo",
            "services",
            "start",
            "--profile",
            "api",
            "--profile",
            "observability",
            "--service",
            "dagster,clickstack,phlo-api",
            "--native",
        ],
        repo_root,
    )


def _run(command: list[str], cwd: Path) -> None:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=600)
    if result.returncode != 0:
        raise SmokeFailure(
            f"{' '.join(command)} failed with exit {result.returncode}\n{result.stderr}"
        )


def _wait_for_json(url: str, *, timeout_seconds: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            response = httpx.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(2)
    raise SmokeFailure(f"{url} did not become ready: {last_error}")


def _get_json(url: str, *, params: dict[str, str] | None = None) -> dict[str, Any] | list[Any]:
    response = httpx.get(url, params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict) and payload.get("error"):
        raise SmokeFailure(f"{url} returned error: {payload['error']}")
    return payload


def _check_phlo_api(args: argparse.Namespace) -> None:
    health = _get_json(f"{args.api_base_url}/api/observability/health")
    if not isinstance(health, dict) or "overall_status" not in health:
        raise SmokeFailure("phlo-api observability health response was malformed")

    dagster = _get_json(
        f"{args.api_base_url}/api/dagster/connection",
        params={"dagster_url": args.dagster_url},
    )
    if not isinstance(dagster, dict) or dagster.get("connected") is not True:
        raise SmokeFailure(f"Dagster is not connected through phlo-api: {dagster}")


def _check_clickstack(args: argparse.Namespace) -> None:
    exists = _clickstack_query(args, "EXISTS TABLE default.otel_traces")
    if not exists or exists[0].get("result") != 1:
        raise SmokeFailure("ClickStack default.otel_traces table is missing")

    count = _clickstack_query(
        args,
        "SELECT count() AS count FROM default.otel_traces",
    )
    if not count or "count" not in count[0]:
        raise SmokeFailure("ClickStack otel_traces count query returned an unexpected payload")
    print(f"ClickStack default.otel_traces rows: {count[0]['count']}")


def _clickstack_query(args: argparse.Namespace, query: str) -> list[dict[str, Any]]:
    response = httpx.post(
        args.clickstack_query_url.rstrip("/"),
        content=f"{query} FORMAT JSONEachRow".encode("utf-8"),
        auth=_clickstack_auth(args),
        timeout=20,
    )
    response.raise_for_status()
    return [json.loads(line) for line in response.text.splitlines() if line.strip()]


def _clickstack_auth(args: argparse.Namespace) -> tuple[str, str] | None:
    user = args.clickstack_query_user
    if user is None:
        return None
    return (user, args.clickstack_query_password)


async def _check_mcp_stdio(args: argparse.Namespace, repo_root: Path) -> None:
    command_args = [
        "run",
        "--package",
        "phlo-mcp",
        "phlo-mcp",
        "--api-base-url",
        args.api_base_url,
    ]
    if args.api_token:
        command_args.extend(["--api-token", args.api_token])

    params = StdioServerParameters(command="uv", args=command_args, cwd=repo_root)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            expected = {
                "get_platform_health",
                "get_dashboard_links",
                "get_run_trace_spans",
                "get_materialization_history",
            }
            missing = sorted(expected - names)
            if missing:
                raise SmokeFailure(f"MCP server is missing expected tools: {missing}")

            await _call_tool_json(session, "get_platform_health", {})
            await _call_tool_json(session, "get_dashboard_links", {})
            spans = await _call_tool_json(session, "get_run_trace_spans", {"run_id": args.run_id})
            span_rows = spans.get("spans") if isinstance(spans, dict) else None
            if not isinstance(span_rows, list):
                raise SmokeFailure(f"get_run_trace_spans returned unexpected payload: {spans}")
            if args.require_run_spans and not span_rows:
                raise SmokeFailure(f"run {args.run_id!r} returned no trace spans")

            if args.asset_key:
                history = await _call_tool_json(
                    session,
                    "get_materialization_history",
                    {"asset_key_path": args.asset_key},
                )
                events = history.get("events") if isinstance(history, dict) else None
                if not isinstance(events, list):
                    raise SmokeFailure(
                        f"get_materialization_history returned unexpected payload: {history}"
                    )
                if args.require_materialization and not events:
                    raise SmokeFailure(f"asset {args.asset_key!r} returned no materializations")


async def _call_tool_json(
    session: ClientSession,
    name: str,
    arguments: dict[str, Any],
) -> dict[str, Any] | list[Any]:
    result = await session.call_tool(name, arguments)
    if result.isError:
        raise SmokeFailure(f"MCP tool {name} returned an error: {result.content}")
    if not result.content:
        raise SmokeFailure(f"MCP tool {name} returned no content")
    content = result.content[0]
    text = getattr(content, "text", None)
    if not isinstance(text, str):
        raise SmokeFailure(f"MCP tool {name} returned non-text content: {content}")
    payload = json.loads(text)
    if isinstance(payload, dict) and payload.get("payload", {}).get("error"):
        raise SmokeFailure(f"MCP tool {name} returned upstream error: {payload}")
    if isinstance(payload, dict):
        spans = payload.get("spans")
        if isinstance(spans, dict) and spans.get("error"):
            raise SmokeFailure(f"MCP tool {name} returned upstream error: {payload}")
        events = payload.get("events")
        if isinstance(events, dict) and events.get("error"):
            raise SmokeFailure(f"MCP tool {name} returned upstream error: {payload}")
    return payload


if __name__ == "__main__":
    raise SystemExit(main())

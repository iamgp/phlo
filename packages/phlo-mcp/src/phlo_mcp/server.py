"""MCP server exposing curated Phlo observability tools."""

from __future__ import annotations

from pathlib import Path
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


def _read_package_doc(package_name: str) -> str:
    safe_name = package_name.removesuffix(".md")
    if "/" in safe_name or "\\" in safe_name or safe_name in {"", ".", ".."}:
        return f"# {package_name}\n\nPackage documentation not found.\n"
    for base in (Path.cwd(), *Path.cwd().parents):
        candidate = base / "docs" / "packages" / f"{safe_name}.md"
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8")
    return f"# {package_name}\n\nPackage documentation not found.\n"


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

    @mcp.resource(
        "phlo://runtime/config",
        name="runtime_config",
        mime_type="application/json",
    )
    def runtime_config() -> dict[str, Any] | list[dict[str, Any]]:
        """Read the current phlo project configuration."""
        return client.get_config()

    @mcp.resource(
        "phlo://runtime/services",
        name="runtime_services",
        mime_type="application/json",
    )
    def runtime_services() -> dict[str, Any] | list[dict[str, Any]]:
        """Read discovered service metadata."""
        return client.get_services()

    @mcp.resource(
        "phlo://runtime/plugins",
        name="runtime_plugins",
        mime_type="application/json",
    )
    def runtime_plugins() -> dict[str, Any] | list[dict[str, Any]]:
        """Read installed plugin metadata."""
        return client.get_plugins()

    @mcp.resource(
        "phlo://runtime/assets",
        name="runtime_assets",
        mime_type="application/json",
    )
    def runtime_assets() -> dict[str, Any] | list[dict[str, Any]]:
        """Read Dagster asset metadata."""
        return client.get_assets()

    @mcp.resource(
        "phlo://runtime/contracts",
        name="runtime_contracts",
        mime_type="application/json",
    )
    def runtime_contracts() -> dict[str, Any] | list[dict[str, Any]]:
        """Read schema contract metadata."""
        return client.get_contracts()

    @mcp.resource(
        "phlo://runtime/dashboards",
        name="runtime_dashboards",
        mime_type="application/json",
    )
    def runtime_dashboards() -> dict[str, Any] | list[dict[str, Any]]:
        """Read observability dashboard metadata."""
        return client.get_dashboard_links()

    @mcp.resource(
        "phlo://runtime/services/{service_name}",
        name="runtime_service",
        mime_type="application/json",
    )
    def runtime_service(service_name: str) -> dict[str, Any] | list[dict[str, Any]]:
        """Read metadata for one service."""
        return client.get_service_info(service_name)

    @mcp.resource(
        "phlo://runtime/assets/{asset_key_path}",
        name="runtime_asset",
        mime_type="application/json",
    )
    def runtime_asset(asset_key_path: str) -> dict[str, Any] | list[dict[str, Any]]:
        """Read metadata for one Dagster asset."""
        return client.get_asset_details(asset_key_path)

    @mcp.resource(
        "phlo://runtime/schemas/{asset_key_path}",
        name="runtime_asset_schema",
        mime_type="application/json",
    )
    def runtime_asset_schema(asset_key_path: str) -> dict[str, Any]:
        """Read schema metadata for one Dagster asset."""
        details = client.get_asset_details(asset_key_path)
        if not isinstance(details, dict):
            return {"asset_key_path": asset_key_path, "columns": []}
        return {
            "asset_key_path": asset_key_path,
            "columns": details.get("columns") or [],
            "column_lineage": details.get("column_lineage"),
            "partition_definition": details.get("partition_definition"),
        }

    @mcp.resource(
        "phlo://runtime/contracts/{table_name}",
        name="runtime_contract",
        mime_type="application/json",
    )
    def runtime_contract(table_name: str) -> dict[str, Any] | list[dict[str, Any]]:
        """Read one schema contract."""
        return client.get_contract(table_name)

    @mcp.resource(
        "phlo://docs/packages/{package_name}",
        name="package_docs",
        mime_type="text/markdown",
    )
    def package_docs(package_name: str) -> str:
        """Read package documentation from the local docs tree."""
        return _read_package_doc(package_name)

    def _write_audit_context(
        operation: str, target: dict[str, Any], dry_run: bool
    ) -> dict[str, Any]:
        return {
            "operation": operation,
            "target": target,
            "dry_run": dry_run,
            "authenticated": bool(resolved.api_token),
            "api_base_url": client.api_base_url,
        }

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

    @mcp.tool()
    def get_trace_spans(
        run_id: str | None = None,
        asset_key: str | None = None,
        job_name: str | None = None,
        service_name: str | None = None,
        span_name: str | None = None,
        status_code: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        """Get OTEL spans filtered by run, asset, job, service, status, name, or time."""
        with tracer.start_as_current_span(
            "mcp.request",
            attributes={"mcp.tool.name": "get_trace_spans"},
        ):
            with tracer.start_as_current_span(
                "mcp.tool.execute",
                attributes={"mcp.tool.name": "get_trace_spans"},
            ):
                with tracer.start_as_current_span("phlo.observability.trace_spans"):
                    payload = client.get_trace_spans(
                        run_id=run_id,
                        asset_key=asset_key,
                        job_name=job_name,
                        service_name=service_name,
                        span_name=span_name,
                        status_code=status_code,
                        start_time=start_time,
                        end_time=end_time,
                        limit=limit,
                    )
                    return {
                        "api_base_url": client.api_base_url,
                        "filters": _trace_filter_payload(
                            run_id=run_id,
                            asset_key=asset_key,
                            job_name=job_name,
                            service_name=service_name,
                            span_name=span_name,
                            status_code=status_code,
                            start_time=start_time,
                            end_time=end_time,
                            limit=limit,
                        ),
                        "spans": payload,
                    }

    @mcp.tool()
    def render_trace_spans_tree(
        run_id: str | None = None,
        asset_key: str | None = None,
        job_name: str | None = None,
        service_name: str | None = None,
        span_name: str | None = None,
        status_code: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        """Render a trace tree for spans matching observability filters."""
        with tracer.start_as_current_span(
            "mcp.request",
            attributes={"mcp.tool.name": "render_trace_spans_tree"},
        ):
            with tracer.start_as_current_span(
                "mcp.tool.execute",
                attributes={"mcp.tool.name": "render_trace_spans_tree"},
            ):
                with tracer.start_as_current_span("phlo.observability.trace_spans_tree"):
                    payload = client.get_trace_spans(
                        run_id=run_id,
                        asset_key=asset_key,
                        job_name=job_name,
                        service_name=service_name,
                        span_name=span_name,
                        status_code=status_code,
                        start_time=start_time,
                        end_time=end_time,
                        limit=limit,
                    )
                    spans = payload if isinstance(payload, list) else []
                    label = run_id or asset_key or job_name or "filtered traces"
                    return {
                        "api_base_url": client.api_base_url,
                        "filters": _trace_filter_payload(
                            run_id=run_id,
                            asset_key=asset_key,
                            job_name=job_name,
                            service_name=service_name,
                            span_name=span_name,
                            status_code=status_code,
                            start_time=start_time,
                            end_time=end_time,
                            limit=limit,
                        ),
                        "span_count": len(spans),
                        "tree": render_span_tree(label, spans),
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

    def _trace_filter_payload(**filters: Any) -> dict[str, Any]:
        return {key: value for key, value in filters.items() if value is not None}

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

    if resolved.enable_write_tools and resolved.api_token:

        @mcp.tool()
        def materialize_asset(
            asset_key_path: str,
            dry_run: bool = True,
            partition_key: str | None = None,
        ) -> dict[str, Any]:
            """Materialize a Dagster asset through phlo-api when write tools are enabled."""
            with tracer.start_as_current_span(
                "mcp.request",
                attributes={"mcp.tool.name": "materialize_asset"},
            ):
                with tracer.start_as_current_span(
                    "mcp.tool.execute",
                    attributes={"mcp.tool.name": "materialize_asset"},
                ):
                    with tracer.start_as_current_span("phlo.dagster.asset.materialize"):
                        target = {"asset_key_path": asset_key_path}
                        if partition_key:
                            target["partition_key"] = partition_key
                        audit_context = _write_audit_context("materialize_asset", target, dry_run)
                        payload = client.materialize_asset(
                            asset_key_path,
                            dry_run=dry_run,
                            partition_key=partition_key,
                        )
                        return {"audit_context": audit_context, "payload": payload}

        @mcp.tool()
        def retry_failed_run(run_id: str, dry_run: bool = True) -> dict[str, Any]:
            """Retry a Dagster run through phlo-api when write tools are enabled."""
            with tracer.start_as_current_span(
                "mcp.request",
                attributes={"mcp.tool.name": "retry_failed_run"},
            ):
                with tracer.start_as_current_span(
                    "mcp.tool.execute",
                    attributes={"mcp.tool.name": "retry_failed_run"},
                ):
                    with tracer.start_as_current_span("phlo.dagster.run.retry"):
                        audit_context = _write_audit_context(
                            "retry_failed_run", {"run_id": run_id}, dry_run
                        )
                        payload = client.retry_run(run_id, dry_run=dry_run)
                        return {"audit_context": audit_context, "payload": payload}

        @mcp.tool()
        def get_dagster_run_status(run_id: str) -> dict[str, Any]:
            """Get Dagster run status through phlo-api for operational follow-up."""
            with tracer.start_as_current_span(
                "mcp.request",
                attributes={"mcp.tool.name": "get_dagster_run_status"},
            ):
                with tracer.start_as_current_span(
                    "mcp.tool.execute",
                    attributes={"mcp.tool.name": "get_dagster_run_status"},
                ):
                    with tracer.start_as_current_span("phlo.dagster.run.status"):
                        payload = client.get_run_status(run_id)
                        return {
                            "api_base_url": client.api_base_url,
                            "run_id": run_id,
                            "payload": payload,
                        }

    return mcp

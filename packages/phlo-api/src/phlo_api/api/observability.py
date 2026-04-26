"""Observability API Router.

Endpoints for platform observability backed by the observability backend capability.

This module provides a unified interface to query platform health, service status,
metrics, alerts, and dashboard links from various observability backends like
Prometheus, Grafana, and the ClickHouse-based observability stack.

Key Endpoints:
    GET /health: Get overall platform health summary.
    GET /services: Get status of all services.
    GET /metrics: Get platform metrics for a time period.
    GET /alerts: Get recent alerts.
    GET /dashboards: Get links to monitoring dashboards.
    GET /links/logs: Get log query link.
    GET /links/metrics: Get metrics query link.

Environment Variables:
    PHLO_OBSERVABILITY_BACKEND: Name of the observability backend to use.

Example:
    Checking platform health:

    .. code-block:: bash

        curl http://localhost:4000/api/observability/health

    Response:

    .. code-block:: json

        {
            "overall_status": "healthy",
            "components": {
                "trino": "healthy",
                "dagster": "healthy"
            },
            "timestamp": "2024-01-15T10:30:00"
        }

"""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from phlo.capabilities import TraceSpanFilter, list_capabilities, resolve_capability
from phlo.capabilities.discovery import discover_capabilities
from phlo.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["observability"])

_DEFAULT_BACKEND_ENV = "PHLO_OBSERVABILITY_BACKEND"


def _resolve_observability_backend(backend_name: str | None = None) -> Any:
    """Resolve the configured observability backend capability."""
    discover_capabilities()

    name = backend_name or os.environ.get(_DEFAULT_BACKEND_ENV)

    if name:
        resolution = resolve_capability("observability_backend", name)
        if resolution is None:
            available = list_capabilities("observability_backend")
            raise RuntimeError(
                f"Observability backend '{name}' not found. Available backends: {available}"
            )
        return resolution.provider

    resolution = resolve_capability("observability_backend")
    if resolution is None:
        available = list_capabilities("observability_backend")
        if available:
            raise RuntimeError(
                f"Multiple observability backends are installed: {available}. "
                f"Set PHLO_OBSERVABILITY_BACKEND env var or pass ?backend=... query param to select one."
            )
        raise RuntimeError(
            "Observability requires an observability_backend capability. "
            "Install phlo-clickstack with phlo-otel, or another provider."
        )
    return resolution.provider


class HealthSummaryResponse(BaseModel):
    """Serialized health summary response."""

    overall_status: str
    components: dict[str, str]
    timestamp: str


class ServiceStatusResponse(BaseModel):
    """Serialized service status response."""

    name: str
    status: str
    last_check: str


class PlatformMetricsResponse(BaseModel):
    """Serialized platform metrics response."""

    period: str
    metrics: dict[str, Any]
    timestamp: str


class AlertResponse(BaseModel):
    """Serialized alert response."""

    title: str
    severity: str
    status: str
    fired_at: str


class DashboardLinkResponse(BaseModel):
    """Serialized dashboard link response."""

    title: str
    url: str
    category: str | None = None


class TraceSpanResponse(BaseModel):
    """Serialized OTEL trace span row."""

    timestamp: str
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    span_name: str
    service_name: str | None = None
    span_kind: str | None = None
    duration_ms: float | None = None
    status_code: str | None = None
    span_attributes: dict[str, Any] = Field(default_factory=dict)
    resource_attributes: dict[str, Any] = Field(default_factory=dict)


@router.get("/health", response_model=HealthSummaryResponse | dict)
def get_health_summary(
    backend: str | None = Query(default=None, description="Observability backend name"),
) -> HealthSummaryResponse | dict[str, str]:
    """Get platform health summary from observability backend.

    Args:
        backend: Optional observability backend name override.

    Returns:
        HealthSummaryResponse with overall status and component health, or error dict.

    Raises:
        None: Exceptions are caught and returned in the response.

    """
    try:
        provider = _resolve_observability_backend(backend)
        health = provider.health_summary()
        return HealthSummaryResponse(
            overall_status=health.overall_status,
            components=health.components,
            timestamp=health.timestamp,
        )
    except Exception as exc:
        logger.exception("health_summary_load_failed")
        return {"error": str(exc)}


@router.get("/services", response_model=list[ServiceStatusResponse] | dict)
def get_service_status(
    backend: str | None = Query(default=None, description="Observability backend name"),
) -> list[ServiceStatusResponse] | dict[str, str]:
    """Get service status list from observability backend.

    Args:
        backend: Optional observability backend name override.

    Returns:
        List of ServiceStatusResponse objects, or error dictionary.

    Raises:
        None: Exceptions are caught and returned in the response.

    """
    try:
        provider = _resolve_observability_backend(backend)
        services = provider.service_status()
        return [
            ServiceStatusResponse(
                name=svc.name,
                status=svc.status,
                last_check=svc.last_check,
            )
            for svc in services
        ]
    except Exception as exc:
        logger.exception("service_status_load_failed")
        return {"error": str(exc)}


@router.get("/metrics", response_model=PlatformMetricsResponse | dict)
def get_platform_metrics(
    period: str = Query(default="24h"),
    backend: str | None = Query(default=None, description="Observability backend name"),
) -> PlatformMetricsResponse | dict[str, str]:
    """Get platform metrics from observability backend.

    Args:
        period: Time period for metrics (default: "24h").
        backend: Optional observability backend name override.

    Returns:
        PlatformMetricsResponse with metrics data, or error dictionary.

    Raises:
        None: Exceptions are caught and returned in the response.

    """
    try:
        provider = _resolve_observability_backend(backend)
        metrics = provider.platform_metrics(period)
        return PlatformMetricsResponse(
            period=metrics.period,
            metrics=metrics.metrics,
            timestamp=metrics.timestamp,
        )
    except Exception as exc:
        logger.exception("platform_metrics_load_failed")
        return {"error": str(exc)}


@router.get("/alerts", response_model=list[AlertResponse] | dict)
def get_recent_alerts(
    limit: int = Query(default=10, le=100),
    backend: str | None = Query(default=None, description="Observability backend name"),
) -> list[AlertResponse] | dict[str, str]:
    """Get recent alerts from observability backend.

    Args:
        limit: Maximum number of alerts to return (default: 10, max: 100).
        backend: Optional observability backend name override.

    Returns:
        List of AlertResponse objects, or error dictionary.

    Raises:
        None: Exceptions are caught and returned in the response.

    """
    try:
        provider = _resolve_observability_backend(backend)
        alerts = provider.recent_alerts(limit)
        return [
            AlertResponse(
                title=alert.title,
                severity=alert.severity,
                status=alert.status,
                fired_at=alert.fired_at,
            )
            for alert in alerts
        ]
    except Exception as exc:
        logger.exception("recent_alerts_load_failed")
        return {"error": str(exc)}


@router.get("/dashboards", response_model=list[DashboardLinkResponse] | dict)
def get_dashboard_links(
    backend: str | None = Query(default=None, description="Observability backend name"),
) -> list[DashboardLinkResponse] | dict[str, str]:
    """Get dashboard links from observability backend.

    Args:
        backend: Optional observability backend name override.

    Returns:
        List of DashboardLinkResponse objects, or error dictionary.

    Raises:
        None: Exceptions are caught and returned in the response.

    """
    try:
        provider = _resolve_observability_backend(backend)
        links = provider.dashboard_links()
        return [
            DashboardLinkResponse(
                title=link.title,
                url=link.url,
                category=link.category,
            )
            for link in links
        ]
    except Exception as exc:
        logger.exception("dashboard_links_load_failed")
        return {"error": str(exc)}


@router.get("/links/logs")
def get_logs_query_link(
    service: str | None = None,
    backend: str | None = Query(default=None, description="Observability backend name"),
) -> dict[str, str | None]:
    """Get log query link from observability backend.

    Args:
        service: Optional service name to include in the query.
        backend: Optional observability backend name override.

    Returns:
        Dictionary with "url" key containing the query link, or error dictionary.

    Raises:
        None: Exceptions are caught and returned in the response.

    """
    try:
        provider = _resolve_observability_backend(backend)
        link = provider.logs_query_link(service)
        return {"url": link}
    except Exception as exc:
        logger.exception("logs_query_link_failed")
        return {"error": str(exc)}


@router.get("/links/metrics")
def get_metrics_query_link(
    metric: str | None = None,
    backend: str | None = Query(default=None, description="Observability backend name"),
) -> dict[str, str | None]:
    """Get metrics query link from observability backend.

    Args:
        metric: Optional metric name to include in the query.
        backend: Optional observability backend name override.

    Returns:
        Dictionary with "url" key containing the query link, or error dictionary.

    Raises:
        None: Exceptions are caught and returned in the response.

    """
    try:
        provider = _resolve_observability_backend(backend)
        link = provider.metrics_query_link(metric)
        return {"url": link}
    except Exception as exc:
        logger.exception("metrics_query_link_failed")
        return {"error": str(exc)}


@router.get("/traces/runs/{run_id}", response_model=list[TraceSpanResponse] | dict)
def get_run_trace_spans(
    run_id: str,
    limit: int = Query(default=500, le=5000),
    backend: str | None = Query(default=None, description="Observability backend name"),
) -> list[TraceSpanResponse] | dict[str, str]:
    """Get OTEL spans correlated to a run id from the observability backend."""
    try:
        provider = _resolve_observability_backend(backend)
        if hasattr(provider, "trace_spans"):
            spans = provider.trace_spans(TraceSpanFilter(run_id=run_id, limit=limit))
        else:
            spans = provider.run_trace_spans(run_id, limit=limit)
        return [TraceSpanResponse(**span.__dict__) for span in spans]
    except Exception as exc:
        logger.exception("run_trace_spans_load_failed", run_id=run_id)
        return {"error": str(exc)}


@router.get("/traces", response_model=list[TraceSpanResponse] | dict)
def get_trace_spans(
    run_id: str | None = Query(default=None),
    asset_key: str | None = Query(default=None),
    job_name: str | None = Query(default=None),
    service_name: str | None = Query(default=None),
    span_name: str | None = Query(default=None),
    status_code: str | None = Query(default=None),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    limit: int = Query(default=500, le=5000),
    backend: str | None = Query(default=None, description="Observability backend name"),
) -> list[TraceSpanResponse] | dict[str, str]:
    """Get OTEL spans matching bounded observability filters."""
    try:
        provider = _resolve_observability_backend(backend)
        filters = TraceSpanFilter(
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
        if hasattr(provider, "trace_spans"):
            spans = provider.trace_spans(filters)
        elif run_id:
            spans = provider.run_trace_spans(run_id, limit=limit)
        else:
            spans = []
        return [TraceSpanResponse(**span.__dict__) for span in spans]
    except Exception as exc:
        logger.exception("trace_spans_load_failed")
        return {"error": str(exc)}

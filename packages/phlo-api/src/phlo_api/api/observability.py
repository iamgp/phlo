"""Observability API Router.

Endpoints for platform observability backed by the observability backend capability.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

from phlo.capabilities import list_capabilities, resolve_capability
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


@router.get("/health", response_model=HealthSummaryResponse | dict)
def get_health_summary(
    backend: str | None = Query(default=None, description="Observability backend name"),
) -> HealthSummaryResponse | dict[str, str]:
    """Get platform health summary from observability backend."""

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
    """Get service status list from observability backend."""

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
    """Get platform metrics from observability backend."""

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
    """Get recent alerts from observability backend."""

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
    """Get dashboard links from observability backend."""

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
    """Get log query link from observability backend."""

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
    """Get metrics query link from observability backend."""

    try:
        provider = _resolve_observability_backend(backend)
        link = provider.metrics_query_link(metric)
        return {"url": link}
    except Exception as exc:
        logger.exception("metrics_query_link_failed")
        return {"error": str(exc)}

# observability (/docs/python-reference/packages/phlo-api/phlo_api/api/observability)



Observability API Router.

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
PHLO\_OBSERVABILITY\_BACKEND: Name of the observability backend to use.

Example:
Checking platform health:

.. code-block:: bash

curl [http://localhost:4000/api/observability/health](http://localhost:4000/api/observability/health)

Response:

.. code-block:: json

\{
"overall\_status": "healthy",
"components": \{
"trino": "healthy",
"dagster": "healthy"
},
"timestamp": "2024-01-15T10:30:00"
}

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;router&#x22;" type="null" value="&#x22;APIRouter(tags=['observability'])&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;HealthSummaryResponse&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/api/observability/HealthSummaryResponse&#x22;" />

      <Card title="&#x22;ServiceStatusResponse&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/api/observability/ServiceStatusResponse&#x22;" />

      <Card title="&#x22;PlatformMetricsResponse&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/api/observability/PlatformMetricsResponse&#x22;" />

      <Card title="&#x22;AlertResponse&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/api/observability/AlertResponse&#x22;" />

      <Card title="&#x22;DashboardLinkResponse&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/api/observability/DashboardLinkResponse&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_resolve_observability_backend&#x22;" type="&#x22;(backend_name=None) -> Any&#x22;">
      Resolve the configured observability backend capability.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;backend_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;typing.Any&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;get_health_summary&#x22;" type="&#x22;(backend=Query(default=None, description='Observability backend name')) -> HealthSummaryResponse | dict[str, str]&#x22;">
      Get platform health summary from observability backend.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;backend&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Query(default=None, description='Observability backend name')&#x22;">
          Optional observability backend name override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;HealthSummaryResponse | dict[str, str]&#x22;">
        HealthSummaryResponse with overall status and component health, or error dict.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_service_status&#x22;" type="&#x22;(backend=Query(default=None, description='Observability backend name')) -> list[ServiceStatusResponse] | dict[str, str]&#x22;">
      Get service status list from observability backend.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;backend&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Query(default=None, description='Observability backend name')&#x22;">
          Optional observability backend name override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list[ServiceStatusResponse] | dict[str, str]&#x22;">
        List of ServiceStatusResponse objects, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_platform_metrics&#x22;" type="&#x22;(period=Query(default='24h'), backend=Query(default=None, description='Observability backend name')) -> PlatformMetricsResponse | dict[str, str]&#x22;">
      Get platform metrics from observability backend.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;period&#x22;" type="&#x22;str&#x22;" value="&#x22;Query(default='24h')&#x22;">
          Time period for metrics (default: "24h").
        </PyParameter>

        <PyParameter name="&#x22;backend&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Query(default=None, description='Observability backend name')&#x22;">
          Optional observability backend name override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;PlatformMetricsResponse | dict[str, str]&#x22;">
        PlatformMetricsResponse with metrics data, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_recent_alerts&#x22;" type="&#x22;(limit=Query(default=10, le=100), backend=Query(default=None, description='Observability backend name')) -> list[AlertResponse] | dict[str, str]&#x22;">
      Get recent alerts from observability backend.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="&#x22;Query(default=10, le=100)&#x22;">
          Maximum number of alerts to return (default: 10, max: 100).
        </PyParameter>

        <PyParameter name="&#x22;backend&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Query(default=None, description='Observability backend name')&#x22;">
          Optional observability backend name override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list[AlertResponse] | dict[str, str]&#x22;">
        List of AlertResponse objects, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_dashboard_links&#x22;" type="&#x22;(backend=Query(default=None, description='Observability backend name')) -> list[DashboardLinkResponse] | dict[str, str]&#x22;">
      Get dashboard links from observability backend.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;backend&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Query(default=None, description='Observability backend name')&#x22;">
          Optional observability backend name override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list[DashboardLinkResponse] | dict[str, str]&#x22;">
        List of DashboardLinkResponse objects, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_logs_query_link&#x22;" type="&#x22;(service=None, backend=Query(default=None, description='Observability backend name')) -> dict[str, str | None]&#x22;">
      Get log query link from observability backend.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;service&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional service name to include in the query.
        </PyParameter>

        <PyParameter name="&#x22;backend&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Query(default=None, description='Observability backend name')&#x22;">
          Optional observability backend name override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Dictionary with "url" key containing the query link, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_metrics_query_link&#x22;" type="&#x22;(metric=None, backend=Query(default=None, description='Observability backend name')) -> dict[str, str | None]&#x22;">
      Get metrics query link from observability backend.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;metric&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional metric name to include in the query.
        </PyParameter>

        <PyParameter name="&#x22;backend&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Query(default=None, description='Observability backend name')&#x22;">
          Optional observability backend name override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Dictionary with "url" key containing the query link, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>

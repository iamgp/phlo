# DefaultObservabilityBackend (/docs/python-reference/core/phlo/capabilities/observability/DefaultObservabilityBackend)



Default observability backend composing metrics, logs, and dashboards.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, grafana_url=None, prometheus_url=None, loki_url=None)&#x22;">
  <PySourceCode>
    ```python
    def __init__(
        self,
        grafana_url: str | None = None,
        prometheus_url: str | None = None,
        loki_url: str | None = None,
    ):
        self._grafana_url = grafana_url
        self._prometheus_url = prometheus_url
        self._loki_url = loki_url
        self._maintenance = DefaultMaintenanceReadModel()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;grafana_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;prometheus_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;loki_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;health_summary&#x22;" type="&#x22;(self) -> PlatformHealthSummary&#x22;">
  <PySourceCode>
    ```python
    def health_summary(self) -> PlatformHealthSummary:
        try:
            maintenance = self._maintenance.load_maintenance_status()
            components = {
                "observability": "healthy",
                "maintenance": "healthy" if maintenance.operations else "no_data",
            }
            if maintenance.operations:
                failed = any(op.status == "failed" for op in maintenance.operations)
                overall = "degraded" if failed else "healthy"
            else:
                overall = "unknown"
        except Exception:
            overall = "unhealthy"
            components = {"observability": "unhealthy", "maintenance": "unhealthy"}

        return PlatformHealthSummary(
            overall_status=overall,
            components=components,
            timestamp=datetime.now(UTC).isoformat(),
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.PlatformHealthSummary&#x22;" />
</PyFunction>

<PyFunction name="&#x22;service_status&#x22;" type="&#x22;(self) -> list[ServiceStatus]&#x22;">
  <PySourceCode>
    ```python
    def service_status(self) -> list[ServiceStatus]:
        try:
            maintenance = self._maintenance.load_maintenance_status()
            latest_by_service: dict[str, ServiceStatus] = {}
            for operation in maintenance.operations:
                service_name = operation.job_name or operation.operation
                if service_name in latest_by_service:
                    continue
                status = "healthy" if operation.status == "completed" else "unknown"
                latest_by_service[service_name] = ServiceStatus(
                    name=service_name,
                    status=status,
                    last_check=operation.completed_at.isoformat(),
                )
            return [latest_by_service[name] for name in sorted(latest_by_service)]
        except Exception:
            return [
                ServiceStatus(
                    name="observability",
                    status="unknown",
                    last_check=datetime.now(UTC).isoformat(),
                )
            ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.interfaces.ServiceStatus]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;platform_metrics&#x22;" type="&#x22;(self, period) -> PlatformMetricsSummary&#x22;">
  <PySourceCode>
    ```python
    def platform_metrics(self, period: str) -> PlatformMetricsSummary:
        try:
            maintenance = self._maintenance.load_maintenance_status()
            total_ops = len(maintenance.operations)
            failed_ops = sum(1 for op in maintenance.operations if op.status == "failed")
            metrics = {
                "total_maintenance_operations": total_ops,
                "failed_operations": failed_ops,
                "successful_operations": total_ops - failed_ops,
            }
        except Exception:
            metrics = {"error": "failed_to_load_metrics"}

        return PlatformMetricsSummary(
            period=period,
            metrics=metrics,
            timestamp=datetime.now(UTC).isoformat(),
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;period&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.PlatformMetricsSummary&#x22;" />
</PyFunction>

<PyFunction name="&#x22;recent_alerts&#x22;" type="&#x22;(self, limit) -> list[AlertSummary]&#x22;">
  <PySourceCode>
    ```python
    def recent_alerts(self, limit: int) -> list[AlertSummary]:
        try:
            maintenance = self._maintenance.load_maintenance_status()
            failed_ops = [op for op in maintenance.operations if op.status == "failed"]
            return [
                AlertSummary(
                    title=f"Maintenance operation {op.operation} failed",
                    severity="error",
                    status="firing",
                    fired_at=op.completed_at.isoformat(),
                )
                for op in failed_ops[:limit]
            ]
        except Exception:
            return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.interfaces.AlertSummary]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;dashboard_links&#x22;" type="&#x22;(self) -> list[DashboardLink]&#x22;">
  <PySourceCode>
    ```python
    def dashboard_links(self) -> list[DashboardLink]:
        clickstack_url = self._resolve_clickstack_url()
        if clickstack_url is not None:
            dashboards_path = (
                _service_env_value("clickstack", _CLICKSTACK_DASHBOARDS_PATH_ENV) or "/"
            )
            return [
                DashboardLink(
                    title="ClickStack",
                    url=_join_url(clickstack_url, dashboards_path),
                    category="overview",
                )
            ]

        grafana_url = self._grafana_url or _resolve_service_base_url(
            "grafana",
            public_url_env=_GRAFANA_PUBLIC_URL_ENV,
            port_env_key="GRAFANA_PORT",
        )
        if grafana_url is None:
            return []

        path_template = (
            _service_env_value("grafana", _GRAFANA_DASHBOARD_PATH_TEMPLATE_ENV) or "/d/{uid}"
        )
        return [
            DashboardLink(
                title=dashboard["title"],
                url=f"{grafana_url}{path_template.format(uid=dashboard['uid'])}",
                category=_dashboard_category(dashboard["title"]),
            )
            for dashboard in _discover_grafana_dashboards()
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.interfaces.DashboardLink]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;logs_query_link&#x22;" type="&#x22;(self, service=None) -> str | None&#x22;">
  <PySourceCode>
    ```python
    def logs_query_link(self, service: str | None = None) -> str | None:
        clickstack_url = self._resolve_clickstack_url()
        if clickstack_url is not None:
            logs_path = _service_env_value("clickstack", _CLICKSTACK_LOGS_PATH_ENV) or "/"
            return _append_query_params(_join_url(clickstack_url, logs_path), service=service)

        loki_url = self._loki_url or _resolve_service_base_url(
            "loki",
            public_url_env=_LOKI_PUBLIC_URL_ENV,
            port_env_key="LOKI_PORT",
        )
        if loki_url is None:
            return None
        logs_path = _service_env_value("loki", _LOKI_LOGS_PATH_ENV) or "/logs"
        if service:
            return f"{loki_url}{logs_path}?service={service}"
        return f"{loki_url}{logs_path}"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;service&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;str | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;metrics_query_link&#x22;" type="&#x22;(self, metric=None) -> str | None&#x22;">
  <PySourceCode>
    ```python
    def metrics_query_link(self, metric: str | None = None) -> str | None:
        clickstack_url = self._resolve_clickstack_url()
        if clickstack_url is not None:
            metrics_path = _service_env_value("clickstack", _CLICKSTACK_METRICS_PATH_ENV) or "/"
            return _append_query_params(_join_url(clickstack_url, metrics_path), metric=metric)

        prometheus_url = self._prometheus_url or _resolve_service_base_url(
            "prometheus",
            public_url_env=_PROMETHEUS_PUBLIC_URL_ENV,
            port_env_key="PROMETHEUS_PORT",
        )
        if prometheus_url is None:
            return None
        query_path = _service_env_value("prometheus", _PROMETHEUS_QUERY_PATH_ENV) or "/graph"
        if metric:
            return f"{prometheus_url}{query_path}?g0.expr={metric}"
        return f"{prometheus_url}{query_path}"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;metric&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;str | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_resolve_clickstack_url&#x22;" type="&#x22;(self) -> str | None&#x22;">
  <PySourceCode>
    ```python
    def _resolve_clickstack_url(self) -> str | None:
        return _resolve_service_base_url(
            "clickstack",
            public_url_env=_CLICKSTACK_PUBLIC_URL_ENV,
            port_env_key="CLICKSTACK_PORT",
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str | None&#x22;" />
</PyFunction>

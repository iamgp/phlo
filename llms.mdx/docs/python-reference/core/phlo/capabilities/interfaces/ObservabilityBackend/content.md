# ObservabilityBackend (/docs/python-reference/core/phlo/capabilities/interfaces/ObservabilityBackend)



Protocol for swappable observability backends (metrics, logs, dashboards).

Functions [#functions]

<PyFunction name="&#x22;health_summary&#x22;" type="&#x22;(self) -> PlatformHealthSummary&#x22;">
  Return platform health summary.

  <PySourceCode>
    ```python
    def health_summary(self) -> PlatformHealthSummary:
        """Return platform health summary."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.PlatformHealthSummary&#x22;" />
</PyFunction>

<PyFunction name="&#x22;service_status&#x22;" type="&#x22;(self) -> list[ServiceStatus]&#x22;">
  Return service status list.

  <PySourceCode>
    ```python
    def service_status(self) -> list[ServiceStatus]:
        """Return service status list."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.interfaces.ServiceStatus]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;platform_metrics&#x22;" type="&#x22;(self, period) -> PlatformMetricsSummary&#x22;">
  Return platform metrics for the specified period.

  <PySourceCode>
    ```python
    def platform_metrics(self, period: str) -> PlatformMetricsSummary:
        """Return platform metrics for the specified period."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;period&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.PlatformMetricsSummary&#x22;" />
</PyFunction>

<PyFunction name="&#x22;recent_alerts&#x22;" type="&#x22;(self, limit) -> list[AlertSummary]&#x22;">
  Return recent alerts up to the specified limit.

  <PySourceCode>
    ```python
    def recent_alerts(self, limit: int) -> list[AlertSummary]:
        """Return recent alerts up to the specified limit."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.interfaces.AlertSummary]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;dashboard_links&#x22;" type="&#x22;(self) -> list[DashboardLink]&#x22;">
  Return available dashboard links.

  <PySourceCode>
    ```python
    def dashboard_links(self) -> list[DashboardLink]:
        """Return available dashboard links."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.interfaces.DashboardLink]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;logs_query_link&#x22;" type="&#x22;(self, service=None) -> str | None&#x22;">
  Return a link to query logs, optionally filtered by service.

  <PySourceCode>
    ```python
    def logs_query_link(self, service: str | None = None) -> str | None:
        """Return a link to query logs, optionally filtered by service."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;service&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;str | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;metrics_query_link&#x22;" type="&#x22;(self, metric=None) -> str | None&#x22;">
  Return a link to query metrics, optionally filtered by metric.

  <PySourceCode>
    ```python
    def metrics_query_link(self, metric: str | None = None) -> str | None:
        """Return a link to query metrics, optionally filtered by metric."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;metric&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;str | None&#x22;" />
</PyFunction>

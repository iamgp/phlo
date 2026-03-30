# metrics (/docs/python-reference/core/phlo/metrics)



Metrics collection models and helpers.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;MetricsBackendSettings&#x22;" href="&#x22;/docs/python-reference/core/phlo/metrics/MetricsBackendSettings&#x22;" />

      <Card title="&#x22;MetricsCollectorError&#x22;" href="&#x22;/docs/python-reference/core/phlo/metrics/MetricsCollectorError&#x22;" />

      <Card title="&#x22;MetricsDependencyError&#x22;" href="&#x22;/docs/python-reference/core/phlo/metrics/MetricsDependencyError&#x22;" />

      <Card title="&#x22;MetricsMalformedResponseError&#x22;" href="&#x22;/docs/python-reference/core/phlo/metrics/MetricsMalformedResponseError&#x22;" />

      <Card title="&#x22;RunMetrics&#x22;" href="&#x22;/docs/python-reference/core/phlo/metrics/RunMetrics&#x22;" />

      <Card title="&#x22;AssetMetrics&#x22;" href="&#x22;/docs/python-reference/core/phlo/metrics/AssetMetrics&#x22;" />

      <Card title="&#x22;SummaryMetrics&#x22;" href="&#x22;/docs/python-reference/core/phlo/metrics/SummaryMetrics&#x22;" />

      <Card title="&#x22;MetricsCollector&#x22;" href="&#x22;/docs/python-reference/core/phlo/metrics/MetricsCollector&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_metrics_collector&#x22;" type="&#x22;() -> MetricsCollector&#x22;">
      Get or create the global metrics collector.

      <PySourceCode>
        ```python
        def get_metrics_collector() -> MetricsCollector:
            """Get or create the global metrics collector."""
            global _metrics_collector
            if _metrics_collector is None:
                _metrics_collector = MetricsCollector()
            return _metrics_collector
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.metrics.MetricsCollector&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>

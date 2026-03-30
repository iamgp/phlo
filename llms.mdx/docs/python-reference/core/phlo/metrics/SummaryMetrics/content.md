# SummaryMetrics (/docs/python-reference/core/phlo/metrics/SummaryMetrics)



Summary metrics for the entire platform.

Attributes [#attributes]

<PyAttribute name="&#x22;total_runs_24h&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;" />

<PyAttribute name="&#x22;successful_runs_24h&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;" />

<PyAttribute name="&#x22;failed_runs_24h&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;" />

<PyAttribute name="&#x22;total_rows_processed_24h&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;" />

<PyAttribute name="&#x22;total_bytes_written_24h&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;" />

<PyAttribute name="&#x22;p50_duration_seconds&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />

<PyAttribute name="&#x22;p95_duration_seconds&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />

<PyAttribute name="&#x22;p99_duration_seconds&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />

<PyAttribute name="&#x22;active_assets_count&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;" />

<PyAttribute name="&#x22;data_growth_bytes&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;" />

<PyAttribute name="&#x22;assets_by_status&#x22;" type="&#x22;dict[str, int]&#x22;" value="&#x22;field(default_factory=(lambda: {'success': 0, 'warning': 0, 'failure': 0}))&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, total_runs_24h=0, successful_runs_24h=0, failed_runs_24h=0, total_rows_processed_24h=0, total_bytes_written_24h=0, p50_duration_seconds=0.0, p95_duration_seconds=0.0, p99_duration_seconds=0.0, active_assets_count=0, data_growth_bytes=0, assets_by_status=(lambda: {'success': 0, 'warning': 0, 'failure': 0})()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;total_runs_24h&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;" />

    <PyParameter name="&#x22;successful_runs_24h&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;" />

    <PyParameter name="&#x22;failed_runs_24h&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;" />

    <PyParameter name="&#x22;total_rows_processed_24h&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;" />

    <PyParameter name="&#x22;total_bytes_written_24h&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;" />

    <PyParameter name="&#x22;p50_duration_seconds&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />

    <PyParameter name="&#x22;p95_duration_seconds&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />

    <PyParameter name="&#x22;p99_duration_seconds&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />

    <PyParameter name="&#x22;active_assets_count&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;" />

    <PyParameter name="&#x22;data_growth_bytes&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;" />

    <PyParameter name="&#x22;assets_by_status&#x22;" type="&#x22;dict[str, int]&#x22;" value="&#x22;(lambda: {'success': 0, 'warning': 0, 'failure': 0})()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

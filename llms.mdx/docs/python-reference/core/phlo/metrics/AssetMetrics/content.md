# AssetMetrics (/docs/python-reference/core/phlo/metrics/AssetMetrics)



Aggregated metrics for an asset.

Attributes [#attributes]

<PyAttribute name="&#x22;asset_name&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;last_run&#x22;" type="&#x22;RunMetrics | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;last_10_runs&#x22;" type="&#x22;list[RunMetrics]&#x22;" value="&#x22;field(default_factory=list)&#x22;" />

<PyAttribute name="&#x22;average_duration&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />

<PyAttribute name="&#x22;failure_rate&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />

<PyAttribute name="&#x22;average_rows_per_run&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />

<PyAttribute name="&#x22;data_growth_bytes&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, asset_name, last_run=None, last_10_runs=list(), average_duration=0.0, failure_rate=0.0, average_rows_per_run=0.0, data_growth_bytes=0) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;last_run&#x22;" type="&#x22;RunMetrics | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;last_10_runs&#x22;" type="&#x22;list[RunMetrics]&#x22;" value="&#x22;list()&#x22;" />

    <PyParameter name="&#x22;average_duration&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />

    <PyParameter name="&#x22;failure_rate&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />

    <PyParameter name="&#x22;average_rows_per_run&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />

    <PyParameter name="&#x22;data_growth_bytes&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

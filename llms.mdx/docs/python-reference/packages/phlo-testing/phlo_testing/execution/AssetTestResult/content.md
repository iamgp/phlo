# AssetTestResult (/docs/python-reference/packages/phlo-testing/phlo_testing/execution/AssetTestResult)



Result of executing an asset in test mode.

Encapsulates all information about an asset test execution including
success status, resulting data, metadata, logs, timing, and errors.

Attributes [#attributes]

<PyAttribute name="&#x22;success&#x22;" type="&#x22;bool&#x22;" value="null">
  Whether asset execution succeeded.
</PyAttribute>

<PyAttribute name="&#x22;data&#x22;" type="&#x22;Optional[pd.DataFrame]&#x22;" value="&#x22;None&#x22;">
  Resulting DataFrame (if available).
</PyAttribute>

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;field(default_factory=dict)&#x22;">
  Metadata from MaterializeResult.
</PyAttribute>

<PyAttribute name="&#x22;logs&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;field(default_factory=list)&#x22;">
  Captured log messages.
</PyAttribute>

<PyAttribute name="&#x22;duration&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;">
  Execution time in seconds.
</PyAttribute>

<PyAttribute name="&#x22;error&#x22;" type="&#x22;Optional[Exception]&#x22;" value="&#x22;None&#x22;">
  Exception if execution failed.
</PyAttribute>

<PyAttribute name="&#x22;raw_result&#x22;" type="&#x22;Optional[Any]&#x22;" value="&#x22;None&#x22;">
  Raw Dagster ExecuteInProcessResult (advanced use).
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, success, data=None, metadata=dict(), logs=list(), duration=0.0, error=None, raw_result=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;success&#x22;" type="&#x22;bool&#x22;" value="null" />

    <PyParameter name="&#x22;data&#x22;" type="&#x22;Optional[pd.DataFrame]&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;logs&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;list()&#x22;" />

    <PyParameter name="&#x22;duration&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />

    <PyParameter name="&#x22;error&#x22;" type="&#x22;Optional[Exception]&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;raw_result&#x22;" type="&#x22;Optional[Any]&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

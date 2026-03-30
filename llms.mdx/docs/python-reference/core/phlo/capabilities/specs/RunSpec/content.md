# RunSpec (/docs/python-reference/core/phlo/capabilities/specs/RunSpec)



Execution details for an asset.

Attributes [#attributes]

<PyAttribute name="&#x22;fn&#x22;" type="&#x22;Callable[[RuntimeContext], Iterable[RunResult]]&#x22;" value="null" />

<PyAttribute name="&#x22;max_runtime_seconds&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;max_retries&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;retry_delay_seconds&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;cron&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;freshness_hours&#x22;" type="&#x22;tuple[int, int] | None&#x22;" value="&#x22;None&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, fn, max_runtime_seconds=None, max_retries=None, retry_delay_seconds=None, cron=None, freshness_hours=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;fn&#x22;" type="&#x22;Callable[[RuntimeContext], Iterable[RunResult]]&#x22;" value="null" />

    <PyParameter name="&#x22;max_runtime_seconds&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;max_retries&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;retry_delay_seconds&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;cron&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;freshness_hours&#x22;" type="&#x22;tuple[int, int] | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

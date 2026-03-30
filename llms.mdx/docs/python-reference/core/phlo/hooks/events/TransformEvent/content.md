# TransformEvent (/docs/python-reference/core/phlo/hooks/events/TransformEvent)



Event emitted for dbt transformation lifecycle stages.

These events track the execution of dbt models and transformations,
capturing information about which models were run, their status, and
performance metrics.

Attributes [#attributes]

<PyAttribute name="&#x22;tool&#x22;" type="&#x22;str&#x22;" value="null">
  Transformation tool name (typically "dbt").
</PyAttribute>

<PyAttribute name="&#x22;project_dir&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Path to the dbt project directory.
</PyAttribute>

<PyAttribute name="&#x22;target&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  dbt target environment (dev, prod, etc.).
</PyAttribute>

<PyAttribute name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Optional partition identifier for partitioned runs.
</PyAttribute>

<PyAttribute name="&#x22;asset_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Dagster asset key if triggered by asset materialization.
</PyAttribute>

<PyAttribute name="&#x22;model_names&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;field(default_factory=list)&#x22;">
  List of dbt models executed in this run.
</PyAttribute>

<PyAttribute name="&#x22;status&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Final status ("success", "failed", "error", etc.).
</PyAttribute>

<PyAttribute name="&#x22;metrics&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;field(default_factory=dict)&#x22;">
  Performance metrics (execution\_time, rows\_affected, etc.).
</PyAttribute>

<PyAttribute name="&#x22;error&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Error message if transformation failed.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, *, event_type, version=EVENT_VERSION, timestamp=_utc_now(), tags=dict(), correlation=HookCorrelation(), tool, project_dir=None, target=None, partition_key=None, asset_key=None, model_names=list(), status=None, metrics=dict(), error=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event_type&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;version&#x22;" type="&#x22;str&#x22;" value="&#x22;EVENT_VERSION&#x22;" />

    <PyParameter name="&#x22;timestamp&#x22;" type="&#x22;datetime&#x22;" value="&#x22;_utc_now()&#x22;" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="&#x22;HookCorrelation()&#x22;" />

    <PyParameter name="&#x22;tool&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;project_dir&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;target&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;asset_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;model_names&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;list()&#x22;" />

    <PyParameter name="&#x22;status&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;metrics&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;error&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

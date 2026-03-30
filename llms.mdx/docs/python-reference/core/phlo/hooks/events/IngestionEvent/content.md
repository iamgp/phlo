# IngestionEvent (/docs/python-reference/core/phlo/hooks/events/IngestionEvent)



Event emitted for data ingestion lifecycle stages.

These events track the progress of data ingestion operations from sources
to the lakehouse. They are emitted at the start and end of ingestion runs,
capturing metrics, status, and any errors that occur.

Attributes [#attributes]

<PyAttribute name="&#x22;asset_key&#x22;" type="&#x22;str&#x22;" value="null">
  Dagster asset key for the ingested table (e.g., "raw\.users").
</PyAttribute>

<PyAttribute name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null">
  Target table name in the lakehouse.
</PyAttribute>

<PyAttribute name="&#x22;group_name&#x22;" type="&#x22;str&#x22;" value="null">
  Ingestion group classification (e.g., "raw", "staging").
</PyAttribute>

<PyAttribute name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Optional partition identifier for partitioned assets.
</PyAttribute>

<PyAttribute name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Unique identifier for this ingestion run.
</PyAttribute>

<PyAttribute name="&#x22;branch_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Git branch name for branch-based ingestion.
</PyAttribute>

<PyAttribute name="&#x22;status&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Final status of the ingestion ("success", "failed", etc.).
</PyAttribute>

<PyAttribute name="&#x22;metrics&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;field(default_factory=dict)&#x22;">
  Performance metrics (rows\_processed, bytes\_written, duration).
</PyAttribute>

<PyAttribute name="&#x22;error&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Error message if ingestion failed.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, *, event_type, version=EVENT_VERSION, timestamp=_utc_now(), tags=dict(), correlation=HookCorrelation(), asset_key, table_name, group_name, partition_key=None, run_id=None, branch_name=None, status=None, metrics=dict(), error=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event_type&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;version&#x22;" type="&#x22;str&#x22;" value="&#x22;EVENT_VERSION&#x22;" />

    <PyParameter name="&#x22;timestamp&#x22;" type="&#x22;datetime&#x22;" value="&#x22;_utc_now()&#x22;" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;correlation&#x22;" type="&#x22;HookCorrelation&#x22;" value="&#x22;HookCorrelation()&#x22;" />

    <PyParameter name="&#x22;asset_key&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;group_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;branch_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;status&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;metrics&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;error&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

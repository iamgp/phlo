# ReplicationConfig (/docs/python-reference/packages/phlo-sling/phlo_sling/registry/ReplicationConfig)



Configuration describing a registered Sling replication stream.

This immutable dataclass represents the complete configuration for a
single Sling replication operation, including source and target connections,
replication mode, filtering, and options.

Attributes [#attributes]

<PyAttribute name="&#x22;stream_name&#x22;" type="&#x22;str&#x22;" value="null">
  Source stream identifier (e.g., 'public.users').
</PyAttribute>

<PyAttribute name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null">
  Target table-store table name.
</PyAttribute>

<PyAttribute name="&#x22;source_conn&#x22;" type="&#x22;str&#x22;" value="null">
  Sling source connection name or URL.
</PyAttribute>

<PyAttribute name="&#x22;target_conn&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Sling target connection name or URL.
</PyAttribute>

<PyAttribute name="&#x22;mode&#x22;" type="&#x22;str&#x22;" value="&#x22;'incremental'&#x22;">
  Replication mode (full-refresh, incremental, snapshot, backfill).
</PyAttribute>

<PyAttribute name="&#x22;primary_key&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;field(default_factory=list)&#x22;">
  Column(s) used as primary key for merge operations.
</PyAttribute>

<PyAttribute name="&#x22;update_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Column used as cursor for incremental replication.
</PyAttribute>

<PyAttribute name="&#x22;group_name&#x22;" type="&#x22;str&#x22;" value="&#x22;'sling'&#x22;">
  Dagster/asset group name for generated assets.
</PyAttribute>

<PyAttribute name="&#x22;object&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Target object path (for file-based targets).
</PyAttribute>

<PyAttribute name="&#x22;select&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;field(default_factory=list)&#x22;">
  Column selection list. Empty means all columns.
</PyAttribute>

<PyAttribute name="&#x22;where&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  SQL WHERE clause for source filtering.
</PyAttribute>

<PyAttribute name="&#x22;source_options&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;field(default_factory=dict)&#x22;">
  Additional Sling source options.
</PyAttribute>

<PyAttribute name="&#x22;target_options&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;field(default_factory=dict)&#x22;">
  Additional Sling target options.
</PyAttribute>

<PyAttribute name="&#x22;full_table_name&#x22;" type="&#x22;str&#x22;" value="null">
  Return fully qualified table name with default namespace.

  Combines the configured namespace with the table name to create
  a fully qualified identifier for the target table.
</PyAttribute>

<PyAttribute name="&#x22;asset_key&#x22;" type="&#x22;str&#x22;" value="null">
  Return the Phlo asset key for this replication stream.

  Generates a unique asset key for referencing this replication
  within the Phlo orchestration system.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, stream_name, table_name, source_conn, target_conn=None, mode='incremental', primary_key=list(), update_key=None, group_name='sling', object=None, select=list(), where=None, source_options=dict(), target_options=dict()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;stream_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;source_conn&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;target_conn&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;mode&#x22;" type="&#x22;str&#x22;" value="&#x22;'incremental'&#x22;" />

    <PyParameter name="&#x22;primary_key&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;list()&#x22;" />

    <PyParameter name="&#x22;update_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;group_name&#x22;" type="&#x22;str&#x22;" value="&#x22;'sling'&#x22;" />

    <PyParameter name="&#x22;object&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;select&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;list()&#x22;" />

    <PyParameter name="&#x22;where&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;source_options&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;target_options&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;dict()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

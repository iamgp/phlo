# SlingReplication (/docs/python-reference/packages/phlo-sling/phlo_sling/registry/SlingReplication)



Python-first replication definition for dynamic Sling asset discovery.

This dataclass provides a programmatic way to define Sling replication
configurations when using the @phlo\_sling\_assets decorator. It supports
all the same options as the individual @phlo\_sling\_replication decorator
but allows for dynamic generation of multiple assets.

Attributes [#attributes]

<PyAttribute name="&#x22;stream_name&#x22;" type="&#x22;str&#x22;" value="null">
  Source stream identifier (e.g., 'public.users').
</PyAttribute>

<PyAttribute name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null">
  Target table name.
</PyAttribute>

<PyAttribute name="&#x22;source_conn&#x22;" type="&#x22;str&#x22;" value="null">
  Sling source connection name or URL.
</PyAttribute>

<PyAttribute name="&#x22;target_conn&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Sling target connection name or URL.
</PyAttribute>

<PyAttribute name="&#x22;mode&#x22;" type="&#x22;Literal['full-refresh', 'incremental', 'snapshot', 'backfill'] | None&#x22;" value="&#x22;None&#x22;">
  Replication mode (full-refresh, incremental, snapshot, backfill).
</PyAttribute>

<PyAttribute name="&#x22;primary_key&#x22;" type="&#x22;list[str] | str | None&#x22;" value="&#x22;None&#x22;">
  Column(s) used as primary key.
</PyAttribute>

<PyAttribute name="&#x22;update_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Column used as cursor for incremental replication.
</PyAttribute>

<PyAttribute name="&#x22;group_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Asset group name (overrides decorator default).
</PyAttribute>

<PyAttribute name="&#x22;object&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Target object path for file-based targets.
</PyAttribute>

<PyAttribute name="&#x22;select&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;field(default_factory=list)&#x22;">
  Column selection list.
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

<PyAttribute name="&#x22;description&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Asset description.
</PyAttribute>

<PyAttribute name="&#x22;owner&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Asset owner identifier.
</PyAttribute>

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;field(default_factory=dict)&#x22;">
  Additional asset metadata.
</PyAttribute>

<PyAttribute name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;field(default_factory=dict)&#x22;">
  Asset tags.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, stream_name, table_name, source_conn, target_conn=None, mode=None, primary_key=None, update_key=None, group_name=None, object=None, select=list(), where=None, source_options=dict(), target_options=dict(), description=None, owner=None, metadata=dict(), tags=dict()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;stream_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;source_conn&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;target_conn&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;mode&#x22;" type="&#x22;Literal['full-refresh', 'incremental', 'snapshot', 'backfill'] | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;primary_key&#x22;" type="&#x22;list[str] | str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;update_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;group_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;object&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;select&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;list()&#x22;" />

    <PyParameter name="&#x22;where&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;source_options&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;target_options&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;description&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;owner&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;dict()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

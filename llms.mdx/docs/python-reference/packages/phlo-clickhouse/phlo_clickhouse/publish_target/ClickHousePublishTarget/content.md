# ClickHousePublishTarget (/docs/python-reference/packages/phlo-clickhouse/phlo_clickhouse/publish_target/ClickHousePublishTarget)



Publish target backed by ClickHouse.

Provides configuration for publishing data marts to ClickHouse tables.
Uses a ClickHouseResource for database connections and operations.

Attributes [#attributes]

<PyAttribute name="&#x22;resource&#x22;" type="&#x22;ClickHouseResource&#x22;" value="&#x22;field(default_factory=ClickHouseResource)&#x22;">
  ClickHouseResource instance for database operations.
  Defaults to a new ClickHouseResource instance.
</PyAttribute>

<PyAttribute name="&#x22;target_system&#x22;" type="&#x22;str&#x22;" value="&#x22;'clickhouse'&#x22;">
  Target system identifier. Always "clickhouse".
</PyAttribute>

<PyAttribute name="&#x22;default_schema&#x22;" type="&#x22;str&#x22;" value="&#x22;'marts'&#x22;">
  Default database/schema for publishing.
  Defaults to "marts".
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, resource=ClickHouseResource(), target_system='clickhouse', default_schema='marts') -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;resource&#x22;" type="&#x22;ClickHouseResource&#x22;" value="&#x22;ClickHouseResource()&#x22;" />

    <PyParameter name="&#x22;target_system&#x22;" type="&#x22;str&#x22;" value="&#x22;'clickhouse'&#x22;" />

    <PyParameter name="&#x22;default_schema&#x22;" type="&#x22;str&#x22;" value="&#x22;'marts'&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

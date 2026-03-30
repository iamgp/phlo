# resource (/docs/python-reference/packages/phlo-clickhouse/phlo_clickhouse/resource)



ClickHouse resource for executing queries.

This module provides the ClickHouseResource class for managing ClickHouse
database connections, executing queries, and handling data operations
including table creation and Parquet file ingestion.

Example:
Basic resource usage:

> > > from phlo\_clickhouse.resource import ClickHouseResource
> > > resource = ClickHouseResource()
> > > resource.execute("SELECT 1")
> > > \[\[1]]

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;CLICKHOUSE_QUERY_ENGINE_SUPPORT&#x22;" type="null" value="&#x22;CapabilitySupport(supports_snapshots=False, supports_time_travel=False)&#x22;" />

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;ClickHouseResource&#x22;" href="&#x22;/docs/python-reference/packages/phlo-clickhouse/phlo_clickhouse/resource/ClickHouseResource&#x22;" />
    </Cards>
  </Tab>
</Tabs>

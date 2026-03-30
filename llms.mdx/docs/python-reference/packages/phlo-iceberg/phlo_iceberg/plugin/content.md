# plugin (/docs/python-reference/packages/phlo-iceberg/phlo_iceberg/plugin)



Phlo plugin for Iceberg resource provider capabilities.

This module registers the Iceberg plugin with Phlo's plugin system,
exposing `IcebergResource` as a table store and `IcebergSchemaMigrator`
as a schema migration provider.

The plugin advertises full Iceberg capability support including:

* Branch/tag references (via Nessie)
* Snapshot-based time travel
* Native schema evolution
* Snapshot management

Example:
Plugin is auto-discovered by Phlo's plugin system::

In pyproject.toml or entry_points: [#in-pyprojecttoml-or-entry_points]

\[project.entry-points."phlo.resource\_providers"]
iceberg = "phlo\_iceberg.plugin:IcebergResourceProvider"

The plugin automatically registers IcebergResource [#the-plugin-automatically-registers-icebergresource]

and IcebergSchemaMigrator for use in Dagster assets. [#and-icebergschemamigrator-for-use-in-dagster-assets]

Access via Phlo capability system::

from phlo.capabilities import get\_resource

Get Iceberg resource [#get-iceberg-resource]

iceberg = get\_resource("table\_store", name="iceberg")
result = iceberg.append\_parquet("raw\.events", "/data/events.parquet")

Get schema migrator [#get-schema-migrator]

migrator = get\_resource("schema\_migrator", name="iceberg")
plan = migrator.diff\_schema(table\_name="raw\.users", desired=schema)

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;IcebergResourceProvider&#x22;" href="&#x22;/docs/python-reference/packages/phlo-iceberg/phlo_iceberg/plugin/IcebergResourceProvider&#x22;" />
    </Cards>
  </Tab>
</Tabs>

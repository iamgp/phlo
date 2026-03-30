# resource (/docs/python-reference/packages/phlo-iceberg/phlo_iceberg/resource)



IcebergResource dataclass for asset/resource access.

This module provides the `IcebergResource` dataclass, which serves as a
high-level interface for Iceberg operations within Dagster assets and resources.
It wraps table operations, snapshot management, and schema conversion in a
convenient API suitable for use as a Dagster resource.

The resource is designed to work with Phlo's capability system and supports
branching via Nessie references.

Example:
Using IcebergResource in a Dagster asset::

from dagster import asset
from phlo\_iceberg import IcebergResource

@asset
def processed\_events(iceberg: IcebergResource):

Ensure table exists [#ensure-table-exists]

from pyiceberg.schema import Schema
from pyiceberg.types import NestedField, LongType, StringType

schema = Schema(
NestedField(1, "id", LongType(), required=True),
NestedField(2, "data", StringType(), required=False),
)
iceberg.ensure\_table("raw\.events", schema=schema)

Append data [#append-data]

result = iceberg.append\_parquet(
table\_name="raw\.events",
data\_path="/data/events.parquet"
)
return result

Resource configuration::

from dagster import Definitions
from phlo\_iceberg import IcebergResource

defs = Definitions(
resources=\{
"iceberg": IcebergResource(ref="main")
}
)

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;IcebergResource&#x22;" href="&#x22;/docs/python-reference/packages/phlo-iceberg/phlo_iceberg/resource/IcebergResource&#x22;" />
    </Cards>
  </Tab>
</Tabs>

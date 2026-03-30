# registry (/docs/python-reference/packages/phlo-dlt/phlo_dlt/registry)



Table configuration and registry for DLT ingestion.

This module defines the TableConfig dataclass used to store table-level
configuration for DLT ingestion assets. It provides the data structure
that links table metadata, schemas, and partition specifications.

Key Components:

* :class:`TableConfig`: Dataclass holding table configuration

Configuration Attributes:

* table\_name: Base table name (without namespace)
* table\_schema: Optional explicit table-store schema
* validation\_schema: Optional Pandera DataFrameModel for validation
* unique\_key: Column name used for deduplication/merge operations
* group\_name: Dagster asset group name
* partition\_spec: Optional partition transform specification

Namespace Resolution:
The full\_table\_name property automatically prepends the configured
default namespace (from settings) to create fully-qualified table names.

See Also:

* :mod:`phlo_dlt.settings`: Default namespace configuration
* :mod:`phlo_dlt.decorator`: Uses TableConfig for asset registration
* :mod:`phlo_dlt.executor`: Uses TableConfig for table operations

Example:

```python
from phlo_dlt.registry import TableConfig
from my_schemas import UserSchema

config = TableConfig(
    table_name="users",
    table_schema=None,  # Will derive from validation_schema
    validation_schema=UserSchema,
    unique_key="id",
    group_name="raw",
    partition_spec=None,
)
print(config.full_table_name)  # "raw.users"
```

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;TableConfig&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dlt/phlo_dlt/registry/TableConfig&#x22;" />
    </Cards>
  </Tab>
</Tabs>

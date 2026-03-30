# schema_check (/docs/python-reference/packages/phlo-core-plugins/phlo_core/quality/schema_check)



Schema check plugin for validating data structure and types.

This module provides the SchemaCheckPlugin, which enables validation of
data against expected schemas including column presence and data type checks.
It integrates with Pandera to provide comprehensive schema validation
capabilities.

Example:
Using the schema check plugin with a Pandera schema::

import pandera as pa
from phlo\_core.quality.schema\_check import SchemaCheckPlugin

Define expected schema [#define-expected-schema]

schema = pa.DataFrameSchema(\{
"id": pa.Column(pa.Int64, nullable=False),
"name": pa.Column(pa.String, nullable=False),
"email": pa.Column(pa.String, nullable=False),
"created\_at": pa.Column(pa.DateTime, nullable=False),
})

Create the check [#create-the-check]

plugin = SchemaCheckPlugin()
check = plugin.create\_check(schema=schema, lazy=True)

Apply to data [#apply-to-data]

validated\_df = check.validate(dataframe)

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;SchemaCheckPlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-core-plugins/phlo_core/quality/schema_check/SchemaCheckPlugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>

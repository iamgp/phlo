# base (/docs/python-reference/packages/phlo-pandera/phlo_pandera/schemas/base)



PhloSchema base class with smart defaults.

This module provides the PhloSchema base class which extends Pandera's
DataFrameModel with standard phlo configuration. Using PhloSchema eliminates
the need to specify Config on every schema definition.

Default Configuration:

* `strict=False`: Allows extra columns (useful for DLT metadata like
  `_dlt_id`, `_dlt_load_id`)
* `coerce=True`: Automatically coerce types to match schema definitions

Important Notes:

* For optional fields (e.g., `str | None`), you must use `Field(nullable=True)`.
  This is a Pandera requirement when `coerce=True`.
* The base class is designed to be extended, not instantiated directly.

Example:

```python
from phlo_pandera.schemas import PhloSchema
from pandera.pandas import Field

class RawUserEvents(PhloSchema):
    '''Schema for raw user events with DLT metadata.'''
    id: str = Field(unique=True)
    type: str
    actor_login: str | None = Field(nullable=True)  # Required for nullable!
    created_at: str
    # No Config needed - defaults are applied automatically
    # Extra columns like _dlt_id, _dlt_load_id are allowed (strict=False)
```

See Also:

* Pandera documentation for DataFrameModel configuration
* `phlo_pandera.schema_extractor`: Schema extraction utilities
* `phlo_pandera.checks_extra`: SchemaCheck for validation

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PhloSchema&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/schemas/base/PhloSchema&#x22;" />
    </Cards>
  </Tab>
</Tabs>

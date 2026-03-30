# schemas (/docs/python-reference/packages/phlo-pandera/phlo_pandera/schemas)



Schemas module initialization.

This module provides base schemas and utilities for data validation using
Pandera. It exposes the PhloSchema base class and output schema models used
across the Phlo ecosystem.

Available Components:

* **PhloSchema**: Base Pandera DataFrameModel with phlo smart defaults
* **PublishPostgresOutput**: Pydantic model for table publishing results
* **RawDataOutput**: Pydantic model for raw data ingestion results
* **TablePublishStats**: Statistics for published tables

Example:

```python
from phlo_pandera.schemas import PhloSchema
from pandera.pandas import Field

class CustomerDimensions(PhloSchema):
    customer_id: int = Field(unique=True)
    email: str | None = Field(nullable=True)
    created_at: str
    # No Config needed - defaults from PhloSchema are applied automatically
```

See Also:

* `schemas/base.py`: PhloSchema implementation
* `schemas/asset_outputs.py`: Output model definitions

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['PhloSchema', 'PublishPostgresOutput', 'RawDataOutput', 'TablePublishStats']&#x22;" />

<Tabs items="[&#x22;Modules&#x22;]">
  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/schemas/base&#x22;" title="&#x22;base&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/schemas/asset_outputs&#x22;" title="&#x22;asset_outputs&#x22;" />
    </Cards>
  </Tab>
</Tabs>

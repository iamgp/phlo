# asset_outputs (/docs/python-reference/packages/phlo-pandera/phlo_pandera/schemas/asset_outputs)



Pydantic models for Dagster asset output structures.

This module defines Pydantic models that specify the expected output schemas
for various pipeline stages. These models are used for:

1. **Validation**: Ensure asset materialization results have correct structure
2. **Metadata Tracking**: Track statistics and status of asset execution
3. **Type Safety**: Provide type hints for downstream consumers

Available Models:

* **RawDataOutput**: Output model for raw data ingestion assets
* **TablePublishStats**: Statistics for a published table
* **PublishPostgresOutput**: Output model for Trino to Postgres publishing

Example:

```python
from phlo_pandera.schemas import RawDataOutput, TablePublishStats

# Create output from ingestion asset
output = RawDataOutput(
    status="available",
    path="/data/raw/events",
    file_count=42,
    files=["part_001.parquet", "part_002.parquet"],
)

# Create stats for publishing
stats = TablePublishStats(row_count=10000, column_count=15)
```

See Also:

* Pydantic documentation for model validation
* Dagster documentation for asset outputs

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;RawDataOutput&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/schemas/asset_outputs/RawDataOutput&#x22;" />

      <Card title="&#x22;TablePublishStats&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/schemas/asset_outputs/TablePublishStats&#x22;" />

      <Card title="&#x22;PublishPostgresOutput&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/schemas/asset_outputs/PublishPostgresOutput&#x22;" />
    </Cards>
  </Tab>
</Tabs>

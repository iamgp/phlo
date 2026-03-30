# PublishPostgresOutput (/docs/python-reference/packages/phlo-pandera/phlo_pandera/schemas/asset_outputs/PublishPostgresOutput)



Output model for Trino to Postgres publishing assets.

Aggregates TablePublishStats for multiple tables published in a single
operation.

Attributes [#attributes]

<PyAttribute name="&#x22;tables&#x22;" type="&#x22;dict[str, TablePublishStats]&#x22;" value="&#x22;Field(..., description='Publishing statistics for each table')&#x22;">
  Dictionary mapping table names to their publishing statistics.
</PyAttribute>

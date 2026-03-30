# TablePublishStats (/docs/python-reference/packages/phlo-pandera/phlo_pandera/schemas/asset_outputs/TablePublishStats)



Statistics for a published table.

Captures row and column counts for tables published from Trino to Postgres
or other destinations.

Attributes [#attributes]

<PyAttribute name="&#x22;row_count&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(..., ge=0, description='Number of rows in the published table')&#x22;">
  Number of rows in the published table. Must be >= 0.
</PyAttribute>

<PyAttribute name="&#x22;column_count&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(..., ge=0, description='Number of columns in the published table')&#x22;">
  Number of columns in the published table. Must be >= 0.
</PyAttribute>

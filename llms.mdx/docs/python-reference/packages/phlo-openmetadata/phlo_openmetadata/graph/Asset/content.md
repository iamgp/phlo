# Asset (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/graph/Asset)



Represents one asset in the OpenMetadata lineage graph.

Attributes [#attributes]

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Unique identifier for the asset.
</PyAttribute>

<PyAttribute name="&#x22;asset_type&#x22;" type="&#x22;str&#x22;" value="&#x22;'unknown'&#x22;">
  Type of asset (e.g., 'ingestion', 'transform', 'publish').
</PyAttribute>

<PyAttribute name="&#x22;status&#x22;" type="&#x22;str&#x22;" value="&#x22;'unknown'&#x22;">
  Current status of the asset.
</PyAttribute>

<PyAttribute name="&#x22;description&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Optional description of the asset.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, name, asset_type='unknown', status='unknown', description=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;asset_type&#x22;" type="&#x22;str&#x22;" value="&#x22;'unknown'&#x22;" />

    <PyParameter name="&#x22;status&#x22;" type="&#x22;str&#x22;" value="&#x22;'unknown'&#x22;" />

    <PyParameter name="&#x22;description&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

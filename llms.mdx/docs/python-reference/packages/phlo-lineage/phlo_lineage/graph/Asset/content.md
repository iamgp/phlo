# Asset (/docs/python-reference/packages/phlo-lineage/phlo_lineage/graph/Asset)



Represents a single asset node in the lineage graph.

An asset is any data object that participates in the pipeline - source tables,
staging models, fact tables, dimension tables, published datasets, etc.

Attributes [#attributes]

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Fully qualified asset identifier (e.g., "bronze.orders",
  "silver.stg\_orders", "gold.fct\_orders").
</PyAttribute>

<PyAttribute name="&#x22;asset_type&#x22;" type="&#x22;str&#x22;" value="&#x22;'unknown'&#x22;">
  Classification of the asset's role in the pipeline:

  * "ingestion": Raw data loaded from sources
  * "transform": Intermediate models created by dbt
  * "publish": Final curated datasets for consumption
  * "unknown": Type not specified
</PyAttribute>

<PyAttribute name="&#x22;status&#x22;" type="&#x22;str&#x22;" value="&#x22;'unknown'&#x22;">
  Current materialization status:

  * "success": Successfully built and fresh
  * "warning": Built with warnings or stale
  * "failure": Failed or missing
  * "unknown": Status not determined
</PyAttribute>

<PyAttribute name="&#x22;description&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
  Optional human-readable description of the asset's
  purpose and contents.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, name, asset_type='unknown', status='unknown', description=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;asset_type&#x22;" type="&#x22;str&#x22;" value="&#x22;'unknown'&#x22;" />

    <PyParameter name="&#x22;status&#x22;" type="&#x22;str&#x22;" value="&#x22;'unknown'&#x22;" />

    <PyParameter name="&#x22;description&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

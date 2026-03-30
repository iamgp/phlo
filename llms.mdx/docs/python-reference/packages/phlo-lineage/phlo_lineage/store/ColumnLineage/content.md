# ColumnLineage (/docs/python-reference/packages/phlo-lineage/phlo_lineage/store/ColumnLineage)



Represents a single column-to-column lineage mapping between two assets.

This dataclass captures the relationship between a source column in an
upstream asset and a target column in a downstream asset, along with
metadata about how the mapping was derived.

Attributes [#attributes]

<PyAttribute name="&#x22;source_asset&#x22;" type="&#x22;str&#x22;" value="null">
  Fully qualified name of the upstream asset (e.g., "bronze.orders").
</PyAttribute>

<PyAttribute name="&#x22;source_column&#x22;" type="&#x22;str&#x22;" value="null">
  Name of the column in the source asset.
</PyAttribute>

<PyAttribute name="&#x22;target_asset&#x22;" type="&#x22;str&#x22;" value="null">
  Fully qualified name of the downstream asset (e.g., "silver.stg\_orders").
</PyAttribute>

<PyAttribute name="&#x22;target_column&#x22;" type="&#x22;str&#x22;" value="null">
  Name of the column in the target asset.
</PyAttribute>

<PyAttribute name="&#x22;source_type&#x22;" type="&#x22;str&#x22;" value="&#x22;'dbt_heuristic'&#x22;">
  Origin of the mapping, typically "dbt\_heuristic" for
  name-based matching or "manual" for user-defined mappings.
</PyAttribute>

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
  Optional dictionary containing additional context such as
  transformation logic, confidence scores, or data quality metrics.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, source_asset, source_column, target_asset, target_column, source_type='dbt_heuristic', metadata=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;source_asset&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;source_column&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;target_asset&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;target_column&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;source_type&#x22;" type="&#x22;str&#x22;" value="&#x22;'dbt_heuristic'&#x22;" />

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

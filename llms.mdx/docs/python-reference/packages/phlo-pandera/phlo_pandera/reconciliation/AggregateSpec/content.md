# AggregateSpec (/docs/python-reference/packages/phlo-pandera/phlo_pandera/reconciliation/AggregateSpec)



Aggregate definition for multi-aggregate reconciliation.

Defines a single aggregate computation to be validated in a
MultiAggregateConsistencyCheck.

Attributes [#attributes]

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Alias used for the source aggregate expression.
</PyAttribute>

<PyAttribute name="&#x22;expression&#x22;" type="&#x22;str&#x22;" value="null">
  SQL expression to compute from source.
</PyAttribute>

<PyAttribute name="&#x22;target_column&#x22;" type="&#x22;str&#x22;" value="null">
  Column in target table containing the aggregate value.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, name, expression, target_column) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;expression&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;target_column&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

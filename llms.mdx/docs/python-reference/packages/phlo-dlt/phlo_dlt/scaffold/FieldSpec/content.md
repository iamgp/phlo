# FieldSpec (/docs/python-reference/packages/phlo-dlt/phlo_dlt/scaffold/FieldSpec)



Structured representation of a scaffold field declaration.

Immutable dataclass representing a parsed field specification with
normalized name, type, and nullability information.

Attributes [#attributes]

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Normalized snake\_case field name.
</PyAttribute>

<PyAttribute name="&#x22;type_name&#x22;" type="&#x22;str&#x22;" value="null">
  Primitive field type name (str, int, float, bool, datetime, date).
</PyAttribute>

<PyAttribute name="&#x22;nullable&#x22;" type="&#x22;bool&#x22;" value="null">
  Whether the field is nullable (True for ? modifier).
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, name, type_name, nullable) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;type_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;nullable&#x22;" type="&#x22;bool&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

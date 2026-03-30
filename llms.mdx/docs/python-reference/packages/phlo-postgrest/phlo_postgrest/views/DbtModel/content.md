# DbtModel (/docs/python-reference/packages/phlo-postgrest/phlo_postgrest/views/DbtModel)



Represents a dbt model extracted from manifest.json.

Data class containing metadata about a dbt model including its
name, schema, columns, tags, and description for view generation.

Attributes [#attributes]

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Model identifier (table/view name).
</PyAttribute>

<PyAttribute name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="null">
  Database schema where model resides.
</PyAttribute>

<PyAttribute name="&#x22;description&#x22;" type="&#x22;str&#x22;" value="null">
  Documentation string from dbt model YAML.
</PyAttribute>

<PyAttribute name="&#x22;columns&#x22;" type="&#x22;dict&#x22;" value="null">
  Dictionary of column metadata from manifest.
</PyAttribute>

<PyAttribute name="&#x22;tags&#x22;" type="&#x22;list[str]&#x22;" value="null">
  List of dbt tags applied to the model.
</PyAttribute>

<PyAttribute name="&#x22;unique_id&#x22;" type="&#x22;str&#x22;" value="null">
  Full unique identifier from manifest (e.g., 'model.project.name').
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, name, schema, description, columns, tags, unique_id) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;description&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;columns&#x22;" type="&#x22;dict&#x22;" value="null" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;list[str]&#x22;" value="null" />

    <PyParameter name="&#x22;unique_id&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

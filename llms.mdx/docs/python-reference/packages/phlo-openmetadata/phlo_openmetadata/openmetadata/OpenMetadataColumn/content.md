# OpenMetadataColumn (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/openmetadata/OpenMetadataColumn)



Represents a column in OpenMetadata.

Attributes [#attributes]

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Column name.
</PyAttribute>

<PyAttribute name="&#x22;displayName&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
  Display name (optional).
</PyAttribute>

<PyAttribute name="&#x22;description&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
  Column description.
</PyAttribute>

<PyAttribute name="&#x22;dataType&#x22;" type="&#x22;str&#x22;" value="&#x22;'UNKNOWN'&#x22;">
  Data type (default 'UNKNOWN').
</PyAttribute>

<PyAttribute name="&#x22;dataLength&#x22;" type="&#x22;Optional[int]&#x22;" value="&#x22;None&#x22;">
  Length for string types.
</PyAttribute>

<PyAttribute name="&#x22;precision&#x22;" type="&#x22;Optional[int]&#x22;" value="&#x22;None&#x22;">
  Precision for numeric types.
</PyAttribute>

<PyAttribute name="&#x22;scale&#x22;" type="&#x22;Optional[int]&#x22;" value="&#x22;None&#x22;">
  Scale for numeric types.
</PyAttribute>

<PyAttribute name="&#x22;tags&#x22;" type="&#x22;Optional[list[dict[str, Any]]]&#x22;" value="&#x22;None&#x22;">
  List of tag dictionaries.
</PyAttribute>

<PyAttribute name="&#x22;constraint&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
  Constraint type (e.g., 'PRIMARY\_KEY').
</PyAttribute>

<PyAttribute name="&#x22;ordinalPosition&#x22;" type="&#x22;Optional[int]&#x22;" value="&#x22;None&#x22;">
  Column position in table.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;to_dict&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Convert to dict, excluding None values.

  <PySourceCode>
    ```python
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict, excluding None values.

        Returns:
            Dictionary representation of the column.

        """
        return compact_dict(asdict(self))
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary representation of the column.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, name, displayName=None, description=None, dataType='UNKNOWN', dataLength=None, precision=None, scale=None, tags=None, constraint=None, ordinalPosition=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;displayName&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;description&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;dataType&#x22;" type="&#x22;str&#x22;" value="&#x22;'UNKNOWN'&#x22;" />

    <PyParameter name="&#x22;dataLength&#x22;" type="&#x22;Optional[int]&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;precision&#x22;" type="&#x22;Optional[int]&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;scale&#x22;" type="&#x22;Optional[int]&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;Optional[list[dict[str, Any]]]&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;constraint&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;ordinalPosition&#x22;" type="&#x22;Optional[int]&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

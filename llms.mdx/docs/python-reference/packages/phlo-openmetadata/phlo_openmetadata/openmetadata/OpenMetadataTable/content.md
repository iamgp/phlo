# OpenMetadataTable (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/openmetadata/OpenMetadataTable)



Represents a table entity in OpenMetadata.

Attributes [#attributes]

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Table name.
</PyAttribute>

<PyAttribute name="&#x22;description&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
  Table description.
</PyAttribute>

<PyAttribute name="&#x22;columns&#x22;" type="&#x22;Optional[list[OpenMetadataColumn]]&#x22;" value="&#x22;None&#x22;">
  List of column definitions.
</PyAttribute>

<PyAttribute name="&#x22;tableType&#x22;" type="&#x22;str&#x22;" value="&#x22;'Regular'&#x22;">
  Table type (default 'Regular').
</PyAttribute>

<PyAttribute name="&#x22;owner&#x22;" type="&#x22;Optional[dict[str, Any]]&#x22;" value="&#x22;None&#x22;">
  Owner dictionary with name and type.
</PyAttribute>

<PyAttribute name="&#x22;tags&#x22;" type="&#x22;Optional[list[dict[str, Any]]]&#x22;" value="&#x22;None&#x22;">
  List of tag dictionaries.
</PyAttribute>

<PyAttribute name="&#x22;sourceUrl&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
  Source URL for the table.
</PyAttribute>

<PyAttribute name="&#x22;location&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
  Storage location path.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;to_dict&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Convert to dict, converting columns to dicts.

  <PySourceCode>
    ```python
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict, converting columns to dicts.

        Returns:
            Dictionary representation of the table.

        """
        return compact_dict(
            {
                "name": self.name,
                "tableType": self.tableType,
                "description": self.description,
                "columns": [col.to_dict() for col in self.columns] if self.columns else None,
                "owner": self.owner,
                "tags": self.tags,
                "sourceUrl": self.sourceUrl,
                "location": self.location,
            }
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary representation of the table.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, name, description=None, columns=None, tableType='Regular', owner=None, tags=None, sourceUrl=None, location=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;description&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;columns&#x22;" type="&#x22;Optional[list[OpenMetadataColumn]]&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;tableType&#x22;" type="&#x22;str&#x22;" value="&#x22;'Regular'&#x22;" />

    <PyParameter name="&#x22;owner&#x22;" type="&#x22;Optional[dict[str, Any]]&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;Optional[list[dict[str, Any]]]&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;sourceUrl&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;location&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

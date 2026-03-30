# OpenMetadataLineageEdge (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/openmetadata/OpenMetadataLineageEdge)



Represents a lineage edge in OpenMetadata.

Attributes [#attributes]

<PyAttribute name="&#x22;fromEntity&#x22;" type="&#x22;str&#x22;" value="null">
  Source entity FQN.
</PyAttribute>

<PyAttribute name="&#x22;toEntity&#x22;" type="&#x22;str&#x22;" value="null">
  Target entity FQN.
</PyAttribute>

<PyAttribute name="&#x22;description&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
  Optional edge description.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;to_dict&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Convert to dict for API submission.

  <PySourceCode>
    ```python
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for API submission.

        Returns:
            Dictionary representation of the lineage edge.

        """
        return compact_dict(
            {
                "fromEntity": self.fromEntity,
                "toEntity": self.toEntity,
                "description": self.description,
            }
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary representation of the lineage edge.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, fromEntity, toEntity, description=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;fromEntity&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;toEntity&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;description&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

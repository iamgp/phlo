# MetadataCatalog (/docs/python-reference/core/phlo/capabilities/interfaces/MetadataCatalog)



Protocol for metadata catalog providers.

Functions [#functions]

<PyFunction name="&#x22;health_check&#x22;" type="&#x22;(self) -> bool&#x22;">
  Check provider connectivity and readiness.

  <PySourceCode>
    ```python
    def health_check(self) -> bool:
        """Check provider connectivity and readiness."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>

<PyFunction name="&#x22;upsert_table&#x22;" type="&#x22;(self, *, namespace, table) -> Any&#x22;">
  Create or update one table definition in the metadata catalog.

  <PySourceCode>
    ```python
    def upsert_table(self, *, namespace: str, table: Any) -> Any:
        """Create or update one table definition in the metadata catalog."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;namespace&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;table&#x22;" type="&#x22;Any&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;" />
</PyFunction>

<PyFunction name="&#x22;publish_quality_result&#x22;" type="&#x22;(self, *, event) -> None&#x22;">
  Publish one quality result payload to the metadata catalog.

  <PySourceCode>
    ```python
    def publish_quality_result(self, *, event: Any) -> None:
        """Publish one quality result payload to the metadata catalog."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;Any&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;publish_lineage_edges&#x22;" type="&#x22;(self, *, edges) -> None&#x22;">
  Publish directed lineage edges to the metadata catalog.

  <PySourceCode>
    ```python
    def publish_lineage_edges(self, *, edges: list[tuple[str, str]]) -> None:
        """Publish directed lineage edges to the metadata catalog."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;edges&#x22;" type="&#x22;list[tuple[str, str]]&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

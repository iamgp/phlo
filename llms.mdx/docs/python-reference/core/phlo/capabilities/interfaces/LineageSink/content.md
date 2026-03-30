# LineageSink (/docs/python-reference/core/phlo/capabilities/interfaces/LineageSink)



Protocol for lineage backends and queryable lineage stores.

Functions [#functions]

<PyFunction name="&#x22;record_asset_edges&#x22;" type="&#x22;(self, edges, *, asset_keys=None, metadata=None, tags=None) -> int&#x22;">
  Persist directed asset lineage edges.

  <PySourceCode>
    ```python
    def record_asset_edges(
        self,
        edges: list[tuple[str, str]],
        *,
        asset_keys: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
    ) -> int:
        """Persist directed asset lineage edges."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;edges&#x22;" type="&#x22;list[tuple[str, str]]&#x22;" value="null" />

    <PyParameter name="&#x22;asset_keys&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, str] | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;int&#x22;" />
</PyFunction>

<PyFunction name="&#x22;record_row_lineage&#x22;" type="&#x22;(self, *, row_id, table_name, source_type, parent_row_ids=None, metadata=None) -> None&#x22;">
  Persist one row-level lineage record.

  <PySourceCode>
    ```python
    def record_row_lineage(
        self,
        *,
        row_id: str,
        table_name: str,
        source_type: str,
        parent_row_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Persist one row-level lineage record."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;row_id&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;source_type&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;parent_row_ids&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;record_column_lineage&#x22;" type="&#x22;(self, mappings) -> int&#x22;">
  Persist column-level lineage mappings.

  <PySourceCode>
    ```python
    def record_column_lineage(self, mappings: list[dict[str, Any]]) -> int:
        """Persist column-level lineage mappings."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;mappings&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;int&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_asset_graph&#x22;" type="&#x22;(self) -> Any&#x22;">
  Return the current asset-level lineage graph representation.

  <PySourceCode>
    ```python
    def get_asset_graph(self) -> Any:
        """Return the current asset-level lineage graph representation."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_row_journey&#x22;" type="&#x22;(self, *, row_id, depth=10) -> Any&#x22;">
  Return upstream and downstream lineage for one row identifier.

  <PySourceCode>
    ```python
    def get_row_journey(self, *, row_id: str, depth: int = 10) -> Any:
        """Return upstream and downstream lineage for one row identifier."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;row_id&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;depth&#x22;" type="&#x22;int&#x22;" value="&#x22;10&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;" />
</PyFunction>

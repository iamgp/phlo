# PhloLineageSink (/docs/python-reference/packages/phlo-lineage/phlo_lineage/lineage_sink/PhloLineageSink)



Capability wrapper around phlo-lineage store and graph functionality.

This class provides a simplified, capability-friendly interface to the
lineage system. It handles connection management internally and exposes
high-level methods for recording and querying lineage data.

The sink is designed to be used as a capability provider in the Phlo
plugin system, but can also be instantiated directly for programmatic use.

Functions [#functions]

<PyFunction name="&#x22;record_asset_edges&#x22;" type="&#x22;(self, edges, *, asset_keys=None, metadata=None, tags=None) -> int&#x22;">
  Persist directed asset lineage edges to the store.

  Records data flow relationships (source -> target) in the lineage
  database. Also creates or updates node entries for all assets
  mentioned in the edges.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > sink = PhloLineageSink()
    > > > count = sink.record\_asset\_edges(
    > > > ...     edges=\[
    > > > ...         ("bronze.orders", "silver.stg\_orders"),
    > > > ...         ("silver.stg\_orders", "gold.fct\_orders"),
    > > > ...     ],
    > > > ...     metadata=\{"run\_id": "manual-001"},
    > > > ... )
    > > > print(f"Recorded \{count} edges")
  </Callout>

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
        """Persist directed asset lineage edges to the store.

        Records data flow relationships (source -> target) in the lineage
        database. Also creates or updates node entries for all assets
        mentioned in the edges.

        Args:
            edges: List of (source, target) tuples representing data flow
                direction. Each tuple indicates that target depends on source.
            asset_keys: Optional additional asset keys to register as nodes
                even if not connected by edges.
            metadata: Optional dictionary of metadata to attach to all edges
                in this batch. Common keys: run_id, timestamp, source_system.
            tags: Optional dictionary of string tags for categorization.

        Returns:
            Number of edges successfully persisted.

        Raises:
            RuntimeError: If the lineage database is not configured.
            Exception: Re-raised from LineageStore if database operation fails.

        Example:
            >>> sink = PhloLineageSink()
            >>> count = sink.record_asset_edges(
            ...     edges=[
            ...         ("bronze.orders", "silver.stg_orders"),
            ...         ("silver.stg_orders", "gold.fct_orders"),
            ...     ],
            ...     metadata={"run_id": "manual-001"},
            ... )
            >>> print(f"Recorded {count} edges")

        """
        return self._get_store().record_asset_edges(
            edges,
            asset_keys=asset_keys,
            metadata=metadata,
            tags=tags,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;edges&#x22;" type="&#x22;list[tuple[str, str]]&#x22;" value="undefined">
      List of (source, target) tuples representing data flow
      direction. Each tuple indicates that target depends on source.
    </PyParameter>

    <PyParameter name="&#x22;asset_keys&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
      Optional additional asset keys to register as nodes
      even if not connected by edges.
    </PyParameter>

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
      Optional dictionary of metadata to attach to all edges
      in this batch. Common keys: run\_id, timestamp, source\_system.
    </PyParameter>

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, str] | None&#x22;" value="&#x22;None&#x22;">
      Optional dictionary of string tags for categorization.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;int&#x22;">
    Number of edges successfully persisted.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;record_row_lineage&#x22;" type="&#x22;(self, *, row_id, table_name, source_type, parent_row_ids=None, metadata=None) -> None&#x22;">
  Persist a single row-level lineage record.

  Records the provenance of an individual data row, including its origin
  and any parent rows it was derived from.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > sink = PhloLineageSink()
    > > > sink.record\_row\_lineage(
    > > > ...     row\_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
    > > > ...     table\_name="bronze.orders",
    > > > ...     source\_type="dlt",
    > > > ...     parent\_row\_ids=\[],
    > > > ...     metadata=\{"source": "api", "batch\_id": "batch-001"},
    > > > ... )
  </Callout>

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
        """Persist a single row-level lineage record.

        Records the provenance of an individual data row, including its origin
        and any parent rows it was derived from.

        Args:
            row_id: ULID string identifying the row. Should be generated via
                generate_row_id() or extracted from _phlo_row_id column.
            table_name: Fully qualified table name (e.g., "bronze.orders",
                "silver.stg_orders").
            source_type: Origin classification:
                - "dlt": Data loaded via dlt (data load tool)
                - "dbt": Data transformed via dbt
                - "external": Data from external systems
                - "manual": User-inserted data
            parent_row_ids: List of ULIDs for parent rows this row was derived
                from. Empty or None for root-level source rows.
            metadata: Optional dictionary with additional context such as
                run_id, partition keys, or processing timestamps.

        Raises:
            RuntimeError: If the lineage database is not configured.
            Exception: Re-raised from LineageStore if database operation fails.

        Example:
            >>> sink = PhloLineageSink()
            >>> sink.record_row_lineage(
            ...     row_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
            ...     table_name="bronze.orders",
            ...     source_type="dlt",
            ...     parent_row_ids=[],
            ...     metadata={"source": "api", "batch_id": "batch-001"},
            ... )

        """
        self._get_store().record_row(
            row_id=row_id,
            table_name=table_name,
            source_type=source_type,
            parent_row_ids=parent_row_ids,
            metadata=metadata,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;row_id&#x22;" type="&#x22;str&#x22;" value="undefined">
      ULID string identifying the row. Should be generated via
      generate\_row\_id() or extracted from \_phlo\_row\_id column.
    </PyParameter>

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (e.g., "bronze.orders",
      "silver.stg\_orders").
    </PyParameter>

    <PyParameter name="&#x22;source_type&#x22;" type="&#x22;str&#x22;" value="undefined">
      Origin classification:

      * "dlt": Data loaded via dlt (data load tool)
      * "dbt": Data transformed via dbt
      * "external": Data from external systems
      * "manual": User-inserted data
    </PyParameter>

    <PyParameter name="&#x22;parent_row_ids&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
      List of ULIDs for parent rows this row was derived
      from. Empty or None for root-level source rows.
    </PyParameter>

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
      Optional dictionary with additional context such as
      run\_id, partition keys, or processing timestamps.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;record_column_lineage&#x22;" type="&#x22;(self, mappings) -> int&#x22;">
  Persist column-level lineage mappings.

  Records relationships between columns in upstream and downstream assets.
  Each mapping indicates that data from a source column flows into a target
  column.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > sink = PhloLineageSink()
    > > > mappings = \[
    > > > ...     \{
    > > > ...         "source\_asset": "bronze.orders",
    > > > ...         "source\_column": "order\_id",
    > > > ...         "target\_asset": "silver.stg\_orders",
    > > > ...         "target\_column": "order\_id",
    > > > ...         "source\_type": "dbt\_heuristic",
    > > > ...         "metadata": \{"confidence": 0.95},
    > > > ...     },
    > > > ... ]
    > > > count = sink.record\_column\_lineage(mappings)
  </Callout>

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    The mappings parameter accepts raw dictionaries for convenience,
    which are converted to ColumnLineage dataclasses internally.
  </Callout>

  <PySourceCode>
    ```python
    def record_column_lineage(self, mappings: list[dict[str, Any]]) -> int:
        """Persist column-level lineage mappings.

        Records relationships between columns in upstream and downstream assets.
        Each mapping indicates that data from a source column flows into a target
        column.

        Args:
            mappings: List of dictionaries representing column lineage mappings.
                Each dict should contain:
                - source_asset: Upstream table/model name
                - source_column: Column name in source
                - target_asset: Downstream table/model name
                - target_column: Column name in target
                - source_type (optional): Origin of mapping, default "dbt_heuristic"
                - metadata (optional): Dictionary with additional context

        Returns:
            Number of mappings successfully persisted.

        Raises:
            RuntimeError: If the lineage database is not configured.
            Exception: Re-raised from LineageStore if database operation fails.

        Example:
            >>> sink = PhloLineageSink()
            >>> mappings = [
            ...     {
            ...         "source_asset": "bronze.orders",
            ...         "source_column": "order_id",
            ...         "target_asset": "silver.stg_orders",
            ...         "target_column": "order_id",
            ...         "source_type": "dbt_heuristic",
            ...         "metadata": {"confidence": 0.95},
            ...     },
            ... ]
            >>> count = sink.record_column_lineage(mappings)

        Note:
            The mappings parameter accepts raw dictionaries for convenience,
            which are converted to ColumnLineage dataclasses internally.

        """
        return self._get_store().record_column_lineage(
            [
                ColumnLineage(
                    source_asset=str(mapping["source_asset"]),
                    source_column=str(mapping["source_column"]),
                    target_asset=str(mapping["target_asset"]),
                    target_column=str(mapping["target_column"]),
                    source_type=str(mapping.get("source_type") or "dbt_heuristic"),
                    metadata=mapping.get("metadata")
                    if isinstance(mapping.get("metadata"), dict | type(None))
                    else None,
                )
                for mapping in mappings
            ]
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;mappings&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="undefined">
      List of dictionaries representing column lineage mappings.
      Each dict should contain:

      * source\_asset: Upstream table/model name
      * source\_column: Column name in source
      * target\_asset: Downstream table/model name
      * target\_column: Column name in target
      * source\_type (optional): Origin of mapping, default "dbt\_heuristic"
      * metadata (optional): Dictionary with additional context
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;int&#x22;">
    Number of mappings successfully persisted.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_asset_graph&#x22;" type="&#x22;(self) -> Any&#x22;">
  Return the current in-memory asset lineage graph.

  Retrieves the global LineageGraph singleton, which is lazily loaded
  from the persistent store on first access.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > sink = PhloLineageSink()
    > > > graph = sink.get\_asset\_graph()
    > > >
    > > > Analyze dependencies [#analyze-dependencies]
    > > >
    > > > upstream = graph.get\_upstream("gold.fct\_orders")
    > > > downstream = graph.get\_downstream("bronze.orders")
    > > >
    > > > Export visualization [#export-visualization]
    > > >
    > > > dot = graph.to\_dot()
  </Callout>

  <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
    phlo\_lineage.graph.LineageGraph for graph analysis methods.
  </Callout>

  <PySourceCode>
    ```python
    def get_asset_graph(self) -> Any:
        """Return the current in-memory asset lineage graph.

        Retrieves the global LineageGraph singleton, which is lazily loaded
        from the persistent store on first access.

        Returns:
            LineageGraph instance containing all known assets and edges.
            May be empty if no lineage database is configured or if the
            database contains no lineage data.

        Example:
            >>> sink = PhloLineageSink()
            >>> graph = sink.get_asset_graph()
            >>>
            >>> # Analyze dependencies
            >>> upstream = graph.get_upstream("gold.fct_orders")
            >>> downstream = graph.get_downstream("bronze.orders")
            >>>
            >>> # Export visualization
            >>> dot = graph.to_dot()

        See Also:
            phlo_lineage.graph.LineageGraph for graph analysis methods.

        """
        return get_lineage_graph()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    LineageGraph instance containing all known assets and edges.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_row_journey&#x22;" type="&#x22;(self, *, row_id, depth=10) -> Any&#x22;">
  Query the complete lineage journey for a single row.

  Retrieves current row information, all ancestor rows (upstream), and
  all descendant rows (downstream) in a single call.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > sink = PhloLineageSink()
    > > > journey = sink.get\_row\_journey(
    > > > ...     row\_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
    > > > ...     depth=5,
    > > > ... )
    > > >
    > > > if journey\["current"]:
    > > > ...     print(f"Row in table: \{journey\['current']\['table\_name']}")
    > > > ...     print(f"Ancestors: \{len(journey\['ancestors'])}")
    > > > ...     print(f"Descendants: \{len(journey\['descendants'])}")
  </Callout>

  <Callout title="&#x22;Use Case&#x22;" type="&#x22;use-case&#x22;">
    This method is ideal for data debugging and impact analysis:

    * Trace a problematic row back to its source
    * Determine which downstream reports depend on a row
    * Validate data transformation chains
  </Callout>

  <PySourceCode>
    ```python
    def get_row_journey(self, *, row_id: str, depth: int = 10) -> Any:
        """Query the complete lineage journey for a single row.

        Retrieves current row information, all ancestor rows (upstream), and
        all descendant rows (downstream) in a single call.

        Args:
            row_id: ULID string identifying the row to query.
            depth: Maximum traversal depth for ancestor and descendant queries.
                Default is 10. Increase for deep lineage chains, decrease for
                performance with shallow queries.

        Returns:
            Dictionary with three keys:
                - current: Dict with row's own lineage info, or None if not found
                - ancestors: List of ancestor row dicts sorted by time desc
                - descendants: List of descendant row dicts sorted by time asc

        Raises:
            RuntimeError: If the lineage database is not configured.
            Exception: Re-raised from LineageStore if database query fails.

        Example:
            >>> sink = PhloLineageSink()
            >>> journey = sink.get_row_journey(
            ...     row_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
            ...     depth=5,
            ... )
            >>>
            >>> if journey["current"]:
            ...     print(f"Row in table: {journey['current']['table_name']}")
            ...     print(f"Ancestors: {len(journey['ancestors'])}")
            ...     print(f"Descendants: {len(journey['descendants'])}")

        Use Case:
            This method is ideal for data debugging and impact analysis:
            - Trace a problematic row back to its source
            - Determine which downstream reports depend on a row
            - Validate data transformation chains

        """
        store = self._get_store()
        return {
            "current": store.get_row(row_id),
            "ancestors": store.get_ancestors(row_id, max_depth=depth),
            "descendants": store.get_descendants(row_id, max_depth=depth),
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;row_id&#x22;" type="&#x22;str&#x22;" value="undefined">
      ULID string identifying the row to query.
    </PyParameter>

    <PyParameter name="&#x22;depth&#x22;" type="&#x22;int&#x22;" value="&#x22;10&#x22;">
      Maximum traversal depth for ancestor and descendant queries.
      Default is 10. Increase for deep lineage chains, decrease for
      performance with shallow queries.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Dictionary with three keys:

    * current: Dict with row's own lineage info, or None if not found
    * ancestors: List of ancestor row dicts sorted by time desc
    * descendants: List of descendant row dicts sorted by time asc
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_store&#x22;" type="&#x22;() -> LineageStore&#x22;">
  Retrieve or create a configured LineageStore instance.

  Resolves the database connection string from environment variables
  and returns a LineageStore instance.

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    This is a static method that creates a new store instance on each
    call. The LineageStore class itself manages schema caching.
  </Callout>

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > store = PhloLineageSink.\_get\_store()
    > > >
    > > > Use store directly for advanced operations [#use-store-directly-for-advanced-operations]
    > > >
    > > > rows = store.get\_table\_rows("bronze.orders", limit=10)
  </Callout>

  <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
    resolve\_lineage\_db\_url\_with\_postgres\_fallback() for URL resolution logic.
  </Callout>

  <PySourceCode>
    ```python
    @staticmethod
    def _get_store() -> LineageStore:
        """Retrieve or create a configured LineageStore instance.

        Resolves the database connection string from environment variables
        and returns a LineageStore instance.

        Returns:
            Configured LineageStore ready for operations.

        Raises:
            RuntimeError: If no lineage database URL can be resolved from
                environment variables (LINEAGE_DB_URL, PHLO_LINEAGE_DB_URL,
                or standard PostgreSQL variables).

        Note:
            This is a static method that creates a new store instance on each
            call. The LineageStore class itself manages schema caching.

        Example:
            >>> store = PhloLineageSink._get_store()
            >>> # Use store directly for advanced operations
            >>> rows = store.get_table_rows("bronze.orders", limit=10)

        See Also:
            resolve_lineage_db_url_with_postgres_fallback() for URL resolution logic.

        """
        connection_string = resolve_lineage_db_url_with_postgres_fallback()
        if not connection_string:
            raise RuntimeError("Lineage sink requires PHLO_LINEAGE_DB_URL to be configured.")
        return LineageStore(connection_string)
    ```
  </PySourceCode>

  <PyFunctionReturn type="&#x22;phlo_lineage.store.LineageStore&#x22;">
    Configured LineageStore ready for operations.
  </PyFunctionReturn>
</PyFunction>

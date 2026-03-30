# graph (/docs/python-reference/packages/phlo-lineage/phlo_lineage/graph)



Build and analyze asset lineage graphs.

This module provides graph-based analysis of data asset dependencies. It implements
a directed graph structure where nodes represent assets (tables, models, datasets)
and edges represent data flow relationships (source -> target).

The LineageGraph class supports:

* Upstream dependency traversal (finding all sources)
* Downstream impact analysis (finding all dependents)
* Impact assessment with categorization
* Multiple export formats (ASCII, DOT, Mermaid, JSON)

Graph Construction:
Graphs are typically built from the persistent LineageStore rather than
constructed manually. The get\_lineage\_graph() function provides a global
singleton instance that loads from the database.

Example:

> > > from phlo\_lineage import get\_lineage\_graph
> > > graph = get\_lineage\_graph()
> > > upstream = graph.get\_upstream("gold.fct\_orders")
> > > downstream = graph.get\_downstream("bronze.orders")
> > > impact = graph.get\_impact("silver.stg\_orders")

Export Formats:

* ASCII: Human-readable tree visualization
* DOT: Graphviz format for rendering diagrams
* Mermaid: Markdown-compatible diagram syntax
* JSON: Machine-readable serialization

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;Asset&#x22;" href="&#x22;/docs/python-reference/packages/phlo-lineage/phlo_lineage/graph/Asset&#x22;" />

      <Card title="&#x22;LineageGraph&#x22;" href="&#x22;/docs/python-reference/packages/phlo-lineage/phlo_lineage/graph/LineageGraph&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_lineage_graph&#x22;" type="&#x22;() -> LineageGraph&#x22;">
      Get or create the global LineageGraph singleton instance.

      This function provides a lazily-initialized global graph instance that
      loads from the persistent LineageStore on first access. Subsequent calls
      return the cached instance.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > from phlo\_lineage import get\_lineage\_graph
        > > > graph = get\_lineage\_graph()
        > > > print(f"Assets: \{len(graph.assets)}")
      </Callout>

      <Callout title="&#x22;Initialization&#x22;" type="&#x22;initialization&#x22;">
        On first call, attempts to:

        1. Resolve the lineage database connection string
        2. Connect to PostgreSQL and load asset nodes
        3. Load asset edges to reconstruct the graph
        4. Handle errors gracefully (returns empty graph on failure)
      </Callout>

      <Callout title="&#x22;Thread Safety&#x22;" type="&#x22;thread-safety&#x22;">
        The global instance is created lazily without explicit locking.
        In concurrent scenarios, multiple threads may briefly have different
        instances until the assignment completes.
      </Callout>

      <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
        \_build\_lineage\_from\_store() for the loading implementation.
      </Callout>

      <PySourceCode>
        ```python
        def get_lineage_graph() -> LineageGraph:
            """Get or create the global LineageGraph singleton instance.

            This function provides a lazily-initialized global graph instance that
            loads from the persistent LineageStore on first access. Subsequent calls
            return the cached instance.

            Returns:
                LineageGraph instance populated from the database if available,
                or an empty graph if no database is configured.

            Example:
                >>> from phlo_lineage import get_lineage_graph
                >>> graph = get_lineage_graph()
                >>> print(f"Assets: {len(graph.assets)}")

            Initialization:
                On first call, attempts to:
                1. Resolve the lineage database connection string
                2. Connect to PostgreSQL and load asset nodes
                3. Load asset edges to reconstruct the graph
                4. Handle errors gracefully (returns empty graph on failure)

            Thread Safety:
                The global instance is created lazily without explicit locking.
                In concurrent scenarios, multiple threads may briefly have different
                instances until the assignment completes.

            See Also:
                _build_lineage_from_store() for the loading implementation.

            """
            global _lineage_graph
            if _lineage_graph is None:
                _lineage_graph = _build_lineage_from_store()
            return _lineage_graph
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_lineage.graph.LineageGraph&#x22;">
        LineageGraph instance populated from the database if available,
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_build_lineage_from_store&#x22;" type="&#x22;() -> LineageGraph&#x22;">
      Build a LineageGraph from the persistent PostgreSQL store.

      This internal function reconstructs the in-memory graph representation
      by querying the phlo.asset\_lineage\_nodes and phlo.asset\_lineage\_edges
      tables.

      <Callout title="&#x22;Loading Process&#x22;" type="&#x22;loading-process&#x22;">
        1. Create empty LineageGraph
        2. Resolve database connection URL
        3. Load all asset nodes with metadata
        4. Load all edges and reconstruct adjacency list
        5. Handle exceptions gracefully with logging
      </Callout>

      <Callout title="&#x22;Error Handling&#x22;" type="&#x22;error-handling&#x22;">
        If the database is unavailable or queries fail, returns an empty
        graph and logs a warning. This ensures the application can start
        even without lineage database connectivity.
      </Callout>

      <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
        This is an internal implementation function. Use get\_lineage\_graph()
        for public access to the graph.
      </Callout>

      <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
        get\_lineage\_graph() for the public accessor.
      </Callout>

      <PySourceCode>
        ```python
        def _build_lineage_from_store() -> LineageGraph:
            """Build a LineageGraph from the persistent PostgreSQL store.

            This internal function reconstructs the in-memory graph representation
            by querying the phlo.asset_lineage_nodes and phlo.asset_lineage_edges
            tables.

            Returns:
                Populated LineageGraph if database is accessible, empty graph otherwise.

            Loading Process:
                1. Create empty LineageGraph
                2. Resolve database connection URL
                3. Load all asset nodes with metadata
                4. Load all edges and reconstruct adjacency list
                5. Handle exceptions gracefully with logging

            Error Handling:
                If the database is unavailable or queries fail, returns an empty
                graph and logs a warning. This ensures the application can start
                even without lineage database connectivity.

            Note:
                This is an internal implementation function. Use get_lineage_graph()
                for public access to the graph.

            See Also:
                get_lineage_graph() for the public accessor.

            """
            graph = LineageGraph()
            connection_string = resolve_lineage_db_url_with_postgres_fallback()
            if not connection_string:
                logger.debug("Lineage graph initialized (no lineage DB configured)")
                return graph

            try:
                store = LineageStore(connection_string)
                for node in store.list_asset_nodes():
                    graph.add_asset(
                        node["asset_key"],
                        asset_type=node.get("asset_type") or "unknown",
                        status=node.get("status") or "unknown",
                    )
                    if node.get("description"):
                        graph.assets[node["asset_key"]].description = node["description"]

                for edge in store.list_asset_edges():
                    graph.add_edge(edge["source_asset"], edge["target_asset"])
            except Exception as exc:
                logger.warning("Failed to build lineage graph from store: %s", exc)

            return graph
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_lineage.graph.LineageGraph&#x22;">
        Populated LineageGraph if database is accessible, empty graph otherwise.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>

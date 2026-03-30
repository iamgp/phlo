# LineageGraph (/docs/python-reference/packages/phlo-lineage/phlo_lineage/graph/LineageGraph)



Directed graph representing asset dependencies and data lineage.

Attributes [#attributes]

<PyAttribute name="&#x22;assets&#x22;" type="&#x22;dict[str, Asset]&#x22;" value="&#x22;field(default_factory=dict)&#x22;">
  Map of asset name -> Asset object containing metadata.
</PyAttribute>

<PyAttribute name="&#x22;edges&#x22;" type="&#x22;dict[str, list[str]]&#x22;" value="&#x22;field(default_factory=(lambda: defaultdict(list)))&#x22;">
  Adjacency list mapping source -> list of targets.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;add_asset&#x22;" type="&#x22;(self, name, asset_type='unknown', status='unknown') -> None&#x22;">
  Add an asset to the graph if it doesn't already exist.

  Idempotent operation - if the asset already exists, no changes are made.
  This allows edges to be added without pre-creating nodes.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > graph = LineageGraph()
    > > > graph.add\_asset("bronze.orders", "ingestion", "success")
    > > > assert "bronze.orders" in graph.assets
  </Callout>

  <PySourceCode>
    ```python
    def add_asset(self, name: str, asset_type: str = "unknown", status: str = "unknown") -> None:
        """Add an asset to the graph if it doesn't already exist.

        Idempotent operation - if the asset already exists, no changes are made.
        This allows edges to be added without pre-creating nodes.

        Args:
            name: Unique asset identifier (fully qualified table/model name).
            asset_type: Classification (ingestion, transform, publish, unknown).
            status: Current materialization status (success, warning, failure, unknown).

        Example:
            >>> graph = LineageGraph()
            >>> graph.add_asset("bronze.orders", "ingestion", "success")
            >>> assert "bronze.orders" in graph.assets

        """
        if name not in self.assets:
            self.assets[name] = Asset(name=name, asset_type=asset_type, status=status)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Unique asset identifier (fully qualified table/model name).
    </PyParameter>

    <PyParameter name="&#x22;asset_type&#x22;" type="&#x22;str&#x22;" value="&#x22;'unknown'&#x22;">
      Classification (ingestion, transform, publish, unknown).
    </PyParameter>

    <PyParameter name="&#x22;status&#x22;" type="&#x22;str&#x22;" value="&#x22;'unknown'&#x22;">
      Current materialization status (success, warning, failure, unknown).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;add_edge&#x22;" type="&#x22;(self, source, target) -> None&#x22;">
  Add a directed edge from source to target asset.

  Creates implicit asset nodes for both source and target if they don't
  exist. Duplicate edges (same source-target pair) are ignored.

  <Callout title="&#x22;Direction Convention&#x22;" type="&#x22;direction-convention&#x22;">
    Data flows source -> target. Target depends on source.
    Example: add\_edge("bronze.orders", "silver.stg\_orders") means
    stg\_orders is derived from orders.
  </Callout>

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > graph = LineageGraph()
    > > > graph.add\_edge("bronze.orders", "silver.stg\_orders")
    > > > assert "silver.stg\_orders" in graph.edges\["bronze.orders"]
  </Callout>

  <PySourceCode>
    ```python
    def add_edge(self, source: str, target: str) -> None:
        """Add a directed edge from source to target asset.

        Creates implicit asset nodes for both source and target if they don't
        exist. Duplicate edges (same source-target pair) are ignored.

        Args:
            source: Upstream asset name (data origin).
            target: Downstream asset name (data destination).

        Direction Convention:
            Data flows source -> target. Target depends on source.
            Example: add_edge("bronze.orders", "silver.stg_orders") means
            stg_orders is derived from orders.

        Example:
            >>> graph = LineageGraph()
            >>> graph.add_edge("bronze.orders", "silver.stg_orders")
            >>> assert "silver.stg_orders" in graph.edges["bronze.orders"]

        """
        self.add_asset(source)
        self.add_asset(target)
        if target not in self.edges[source]:
            self.edges[source].append(target)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;source&#x22;" type="&#x22;str&#x22;" value="undefined">
      Upstream asset name (data origin).
    </PyParameter>

    <PyParameter name="&#x22;target&#x22;" type="&#x22;str&#x22;" value="undefined">
      Downstream asset name (data destination).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_upstream&#x22;" type="&#x22;(self, asset_name, depth=None) -> Set[str]&#x22;">
  Traverse and return all upstream assets (dependencies/sources).

  Performs a breadth-first search from the starting asset to find all
  assets that feed data into it, directly or indirectly.

  <Callout title="&#x22;Algorithm&#x22;" type="&#x22;algorithm&#x22;">
    BFS traversal following edges in reverse direction (find all sources
    that have the current node as a target).
  </Callout>

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > graph = LineageGraph()
    > > > graph.add\_edge("bronze.orders", "silver.stg\_orders")
    > > > graph.add\_edge("silver.stg\_orders", "gold.fct\_orders")
    > > >
    > > > Full upstream [#full-upstream]
    > > >
    > > > upstream = graph.get\_upstream("gold.fct\_orders")
    > > > print(upstream)  # \{'bronze.orders', 'silver.stg\_orders'}
    > > >
    > > > Direct only [#direct-only]
    > > >
    > > > direct = graph.get\_upstream("gold.fct\_orders", depth=1)
    > > > print(direct)  # \{'silver.stg\_orders'}
  </Callout>

  <PySourceCode>
    ```python
    def get_upstream(self, asset_name: str, depth: Optional[int] = None) -> Set[str]:
        """Traverse and return all upstream assets (dependencies/sources).

        Performs a breadth-first search from the starting asset to find all
        assets that feed data into it, directly or indirectly.

        Args:
            asset_name: Starting asset for upstream traversal.
            depth: Maximum traversal depth. None means unlimited (default).
                Depth 1 returns only direct parents.

        Returns:
            Set of asset names that are upstream of the starting asset.

        Algorithm:
            BFS traversal following edges in reverse direction (find all sources
            that have the current node as a target).

        Example:
            >>> graph = LineageGraph()
            >>> graph.add_edge("bronze.orders", "silver.stg_orders")
            >>> graph.add_edge("silver.stg_orders", "gold.fct_orders")
            >>>
            >>> # Full upstream
            >>> upstream = graph.get_upstream("gold.fct_orders")
            >>> print(upstream)  # {'bronze.orders', 'silver.stg_orders'}
            >>>
            >>> # Direct only
            >>> direct = graph.get_upstream("gold.fct_orders", depth=1)
            >>> print(direct)  # {'silver.stg_orders'}

        """
        upstream = set()
        visited = set()
        queue = deque([(asset_name, 0)])

        while queue:
            current, current_depth = queue.popleft()

            if current in visited:
                continue

            visited.add(current)

            # Find all assets that point to current
            for source, targets in self.edges.items():
                if current in targets:
                    upstream.add(source)

                    if depth is None or current_depth < depth:
                        queue.append((source, current_depth + 1))

        return upstream
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Starting asset for upstream traversal.
    </PyParameter>

    <PyParameter name="&#x22;depth&#x22;" type="&#x22;Optional[int]&#x22;" value="&#x22;None&#x22;">
      Maximum traversal depth. None means unlimited (default).
      Depth 1 returns only direct parents.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Set&#x22;">
    Set of asset names that are upstream of the starting asset.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_downstream&#x22;" type="&#x22;(self, asset_name, depth=None) -> Set[str]&#x22;">
  Traverse and return all downstream assets (dependents).

  Performs a breadth-first search from the starting asset to find all
  assets that depend on it, directly or indirectly.

  <Callout title="&#x22;Algorithm&#x22;" type="&#x22;algorithm&#x22;">
    BFS traversal following edges in forward direction (find all targets
    of the current node).
  </Callout>

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > graph = LineageGraph()
    > > > graph.add\_edge("bronze.orders", "silver.stg\_orders")
    > > > graph.add\_edge("silver.stg\_orders", "gold.fct\_orders")
    > > >
    > > > Full downstream [#full-downstream]
    > > >
    > > > downstream = graph.get\_downstream("bronze.orders")
    > > > print(downstream)  # \{'silver.stg\_orders', 'gold.fct\_orders'}
    > > >
    > > > Direct only [#direct-only-1]
    > > >
    > > > direct = graph.get\_downstream("bronze.orders", depth=1)
    > > > print(direct)  # \{'silver.stg\_orders'}
  </Callout>

  <PySourceCode>
    ```python
    def get_downstream(self, asset_name: str, depth: Optional[int] = None) -> Set[str]:
        """Traverse and return all downstream assets (dependents).

        Performs a breadth-first search from the starting asset to find all
        assets that depend on it, directly or indirectly.

        Args:
            asset_name: Starting asset for downstream traversal.
            depth: Maximum traversal depth. None means unlimited (default).
                Depth 1 returns only direct children.

        Returns:
            Set of asset names that are downstream of the starting asset.

        Algorithm:
            BFS traversal following edges in forward direction (find all targets
            of the current node).

        Example:
            >>> graph = LineageGraph()
            >>> graph.add_edge("bronze.orders", "silver.stg_orders")
            >>> graph.add_edge("silver.stg_orders", "gold.fct_orders")
            >>>
            >>> # Full downstream
            >>> downstream = graph.get_downstream("bronze.orders")
            >>> print(downstream)  # {'silver.stg_orders', 'gold.fct_orders'}
            >>>
            >>> # Direct only
            >>> direct = graph.get_downstream("bronze.orders", depth=1)
            >>> print(direct)  # {'silver.stg_orders'}

        """
        downstream = set()
        visited = set()
        queue = deque([(asset_name, 0)])

        while queue:
            current, current_depth = queue.popleft()

            if current in visited:
                continue

            visited.add(current)

            # Find all assets that current points to
            for target in self.edges.get(current, []):
                downstream.add(target)

                if depth is None or current_depth < depth:
                    queue.append((target, current_depth + 1))

        return downstream
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Starting asset for downstream traversal.
    </PyParameter>

    <PyParameter name="&#x22;depth&#x22;" type="&#x22;Optional[int]&#x22;" value="&#x22;None&#x22;">
      Maximum traversal depth. None means unlimited (default).
      Depth 1 returns only direct children.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Set&#x22;">
    Set of asset names that are downstream of the starting asset.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_impact&#x22;" type="&#x22;(self, asset_name) -> dict&#x22;">
  Analyze the downstream impact of changes to an asset.

  Calculates metrics about how many and what types of assets would be
  affected by a failure or schema change in the specified asset.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > graph = LineageGraph()
    > > > graph.add\_edge("bronze.orders", "silver.stg\_orders")
    > > > graph.add\_asset("gold.fct\_orders", "publish")
    > > > graph.add\_edge("silver.stg\_orders", "gold.fct\_orders")
    > > >
    > > > impact = graph.get\_impact("bronze.orders")
    > > > print(impact\["publishing\_affected"])  # True
    > > > print(len(impact\["affected\_assets"]))  # 2
  </Callout>

  <Callout title="&#x22;Use Case&#x22;" type="&#x22;use-case&#x22;">
    This method is useful for:

    * Pre-deployment impact assessment
    * Data incident scope evaluation
    * Change management approval workflows
  </Callout>

  <PySourceCode>
    ```python
    def get_impact(self, asset_name: str) -> dict:
        """Analyze the downstream impact of changes to an asset.

        Calculates metrics about how many and what types of assets would be
        affected by a failure or schema change in the specified asset.

        Args:
            asset_name: Asset to analyze for impact.

        Returns:
            Dictionary containing impact analysis:
                - direct_count: Number of directly dependent assets (depth=1).
                - indirect_count: Number of transitively dependent assets.
                - publishing_affected: Boolean indicating if any "publish"
                  type assets would be affected.
                - affected_assets: Complete list of downstream asset names.

        Example:
            >>> graph = LineageGraph()
            >>> graph.add_edge("bronze.orders", "silver.stg_orders")
            >>> graph.add_asset("gold.fct_orders", "publish")
            >>> graph.add_edge("silver.stg_orders", "gold.fct_orders")
            >>>
            >>> impact = graph.get_impact("bronze.orders")
            >>> print(impact["publishing_affected"])  # True
            >>> print(len(impact["affected_assets"]))  # 2

        Use Case:
            This method is useful for:
            - Pre-deployment impact assessment
            - Data incident scope evaluation
            - Change management approval workflows

        """
        downstream = self.get_downstream(asset_name)

        # Categorize by type
        impact = {
            "direct_count": 0,
            "indirect_count": len(downstream) - len(self.get_downstream(asset_name, depth=1)),
            "publishing_affected": False,
            "affected_assets": list(downstream),
        }

        # Check if any publishing assets are affected
        for asset in downstream:
            if self.assets.get(asset, Asset("")).asset_type == "publish":
                impact["publishing_affected"] = True

        return impact
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Asset to analyze for impact.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary containing impact analysis:

    * direct\_count: Number of directly dependent assets (depth=1).
    * indirect\_count: Number of transitively dependent assets.
    * publishing\_affected: Boolean indicating if any "publish"
      type assets would be affected.
    * affected\_assets: Complete list of downstream asset names.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;to_ascii_tree&#x22;" type="&#x22;(self, asset_name, direction='both', depth=None) -> str&#x22;">
  Generate a human-readable ASCII tree representation of lineage.

  Creates a visual tree diagram showing upstream dependencies and/or
  downstream dependents of the specified asset.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > graph = LineageGraph()
    > > > graph.add\_edge("bronze.orders", "silver.stg\_orders")
    > > > print(graph.to\_ascii\_tree("silver.stg\_orders", direction="upstream"))
    > > > silver.stg\_orders
    > > > ├── \[upstream]
    > > > │   └── bronze.orders (ingestion)
  </Callout>

  <Callout title="&#x22;Visual Elements&#x22;" type="&#x22;visual-elements&#x22;">
    * ├── indicates more siblings follow
    * └── indicates last sibling
    * │   shows branch continuation
    * \[upstream] and \[downstream] label sections
    * Status icons: ✓ (success) or ✗ (failure/warning)
  </Callout>

  <PySourceCode>
    ```python
    def to_ascii_tree(
        self, asset_name: str, direction: str = "both", depth: Optional[int] = None
    ) -> str:
        """Generate a human-readable ASCII tree representation of lineage.

        Creates a visual tree diagram showing upstream dependencies and/or
        downstream dependents of the specified asset.

        Args:
            asset_name: Root asset to display at the top of the tree.
            direction: Scope of lineage to include:
                - "upstream": Show only dependencies (parents above)
                - "downstream": Show only dependents (children below)
                - "both": Show both directions (default)
            depth: Maximum depth to display. None means unlimited.

        Returns:
            Multi-line string containing ASCII tree visualization.

        Example:
            >>> graph = LineageGraph()
            >>> graph.add_edge("bronze.orders", "silver.stg_orders")
            >>> print(graph.to_ascii_tree("silver.stg_orders", direction="upstream"))
            silver.stg_orders
            ├── [upstream]
            │   └── bronze.orders (ingestion)

        Visual Elements:
            - ├── indicates more siblings follow
            - └── indicates last sibling
            - │   shows branch continuation
            - [upstream] and [downstream] label sections
            - Status icons: ✓ (success) or ✗ (failure/warning)

        """
        lines = []
        lines.append(asset_name)

        if direction in ["upstream", "both"]:
            upstream = self.get_upstream(asset_name, depth=depth)
            if upstream:
                lines.append("├── [upstream]")
                for asset in sorted(upstream):
                    prefix = (
                        "│   "
                        if direction == "both" and self.get_downstream(asset_name, depth=depth)
                        else "    "
                    )
                    asset_obj = self.assets.get(asset, Asset(asset))
                    lines.append(f"{prefix}└── {asset} ({asset_obj.asset_type})")

        if direction in ["downstream", "both"]:
            downstream = self.get_downstream(asset_name, depth=depth)
            if downstream:
                prefix = "└── " if direction == "both" else "├── "
                label = "[downstream]" if direction == "both" else "[downstream]"
                lines.append(f"{prefix}{label}")

                for i, asset in enumerate(sorted(downstream)):
                    is_last = i == len(downstream) - 1
                    tree_prefix = "    " if is_last else "│   "
                    branch_prefix = "└── " if is_last else "├── "

                    asset_obj = self.assets.get(asset, Asset(asset))
                    status_icon = "✓" if asset_obj.status == "success" else "✗"

                    lines.append(
                        f"{tree_prefix}{branch_prefix}[{status_icon}] {asset} ({asset_obj.asset_type})"
                    )

        return "\n".join(lines)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Root asset to display at the top of the tree.
    </PyParameter>

    <PyParameter name="&#x22;direction&#x22;" type="&#x22;str&#x22;" value="&#x22;'both'&#x22;">
      Scope of lineage to include:

      * "upstream": Show only dependencies (parents above)
      * "downstream": Show only dependents (children below)
      * "both": Show both directions (default)
    </PyParameter>

    <PyParameter name="&#x22;depth&#x22;" type="&#x22;Optional[int]&#x22;" value="&#x22;None&#x22;">
      Maximum depth to display. None means unlimited.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Multi-line string containing ASCII tree visualization.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;to_dot&#x22;" type="&#x22;(self) -> str&#x22;">
  Generate Graphviz DOT format representation of the graph.

  DOT is the native format for Graphviz, a widely-used graph visualization
  tool. The output can be rendered to PNG, SVG, PDF, and other formats.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > dot = graph.to\_dot()
    > > > with open("lineage.dot", "w") as f:
    > > > ...     f.write(dot)
    > > >
    > > > Render: dot -Tpng lineage.dot -o lineage.png [#render-dot--tpng-lineagedot--o-lineagepng]
  </Callout>

  <Callout title="&#x22;Styling&#x22;" type="&#x22;styling&#x22;">
    * Nodes are styled boxes with colors by asset\_type:
      * lightblue: ingestion
      * lightgreen: transform
      * lightcoral: publish
      * lightgray: unknown
    * Border colors indicate status:
      * green: success
      * orange: warning
      * red: failure
      * gray: unknown
    * Layout direction is Left-to-Right (rankdir="LR")
  </Callout>

  <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
    [https://graphviz.org/documentation/](https://graphviz.org/documentation/) for Graphviz documentation.
  </Callout>

  <PySourceCode>
    ```python
    def to_dot(self) -> str:
        """Generate Graphviz DOT format representation of the graph.

        DOT is the native format for Graphviz, a widely-used graph visualization
        tool. The output can be rendered to PNG, SVG, PDF, and other formats.

        Returns:
            DOT format string suitable for writing to a .dot file.

        Example:
            >>> dot = graph.to_dot()
            >>> with open("lineage.dot", "w") as f:
            ...     f.write(dot)
            >>> # Render: dot -Tpng lineage.dot -o lineage.png

        Styling:
            - Nodes are styled boxes with colors by asset_type:
              - lightblue: ingestion
              - lightgreen: transform
              - lightcoral: publish
              - lightgray: unknown
            - Border colors indicate status:
              - green: success
              - orange: warning
              - red: failure
              - gray: unknown
            - Layout direction is Left-to-Right (rankdir="LR")

        See Also:
            https://graphviz.org/documentation/ for Graphviz documentation.

        """
        lines = ["digraph {", '  rankdir="LR";']

        # Add nodes with styling
        for asset_name, asset in self.assets.items():
            color = {
                "ingestion": "lightblue",
                "transform": "lightgreen",
                "publish": "lightcoral",
                "unknown": "lightgray",
            }.get(asset.asset_type, "lightgray")

            status_color = {
                "success": "green",
                "warning": "orange",
                "failure": "red",
                "unknown": "gray",
            }.get(asset.status, "gray")

            lines.append(
                f'  "{asset_name}" [label="{asset_name}", '
                f'shape="box", style="filled", fillcolor="{color}", '
                f'color="{status_color}", penwidth="2"];'
            )

        # Add edges
        for source, targets in self.edges.items():
            for target in targets:
                lines.append(f'  "{source}" -> "{target}";')

        lines.append("}")
        return "\n".join(lines)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    DOT format string suitable for writing to a .dot file.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;to_mermaid&#x22;" type="&#x22;(self) -> str&#x22;">
  Generate Mermaid diagram format for documentation integration.

  Mermaid is a markdown-native diagram syntax supported by GitHub,
  GitLab, Notion, and many other documentation platforms.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > mermaid = graph.to\_mermaid()
    > > > print("`mermaid")
    > > > print(mermaid)
    > > > print("`")
  </Callout>

  <Callout title="&#x22;Styling&#x22;" type="&#x22;styling&#x22;">
    * Node shapes indicate asset\_type:
      * \[(\{name} - Ingestion)]: Cylinder for ingestion
      * \[\{name} - Transform]: Box for transform
      * (\{name} - Publish): Rounded for publish
      * \[\{name}]: Default box
    * Asset names are converted to safe identifiers by replacing
      hyphens and dots with underscores.
  </Callout>

  <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
    [https://mermaid.js.org/](https://mermaid.js.org/) for Mermaid syntax documentation.
  </Callout>

  <PySourceCode>
    ````python
    def to_mermaid(self) -> str:
        """Generate Mermaid diagram format for documentation integration.

        Mermaid is a markdown-native diagram syntax supported by GitHub,
        GitLab, Notion, and many other documentation platforms.

        Returns:
            Mermaid format string suitable for embedding in markdown.

        Example:
            >>> mermaid = graph.to_mermaid()
            >>> print("\```mermaid")
            >>> print(mermaid)
            >>> print("\```")

        Styling:
            - Node shapes indicate asset_type:
              - [({name} - Ingestion)]: Cylinder for ingestion
              - [{name} - Transform]: Box for transform
              - ({name} - Publish): Rounded for publish
              - [{name}]: Default box
            - Asset names are converted to safe identifiers by replacing
              hyphens and dots with underscores.

        See Also:
            https://mermaid.js.org/ for Mermaid syntax documentation.

        """
        lines = ["graph TD"]

        # Add nodes
        for asset_name, asset in self.assets.items():
            shape = {
                "ingestion": "[({} - Ingestion)]",
                "transform": "[{} - Transform]",
                "publish": "({} - Publish)",
                "unknown": "[{}]",
            }.get(asset.asset_type, "[{}]")

            lines.append(f'  {self._safe_id(asset_name)}"{shape.format(asset_name)}"')

        # Add edges
        for source, targets in self.edges.items():
            for target in targets:
                lines.append(f"  {self._safe_id(source)} --> {self._safe_id(target)}")

        return "\n".join(lines)
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Mermaid format string suitable for embedding in markdown.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;to_json&#x22;" type="&#x22;(self) -> str&#x22;">
  Generate JSON serialization of the graph.

  Produces a machine-readable representation suitable for programmatic
  consumption, API responses, or caching.

  <Callout title="&#x22;Schema&#x22;" type="&#x22;schema&#x22;">
    \{
    "assets": \{
    "asset\_name": \{
    "type": "ingestion|transform|publish|unknown",
    "status": "success|warning|failure|unknown",
    "description": "..."
    }
    },
    "edges": \{
    "source\_asset": \["target\_asset1", "target\_asset2"]
    }
    }
  </Callout>

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > json\_str = graph.to\_json()
    > > > import json
    > > > data = json.loads(json\_str)
    > > > print(data\["assets"]\["bronze.orders"]\["type"])
    > > > 'ingestion'
  </Callout>

  <PySourceCode>
    ```python
    def to_json(self) -> str:
        """Generate JSON serialization of the graph.

        Produces a machine-readable representation suitable for programmatic
        consumption, API responses, or caching.

        Returns:
            JSON format string with indentation for readability.

        Schema:
            {
                "assets": {
                    "asset_name": {
                        "type": "ingestion|transform|publish|unknown",
                        "status": "success|warning|failure|unknown",
                        "description": "..."
                    }
                },
                "edges": {
                    "source_asset": ["target_asset1", "target_asset2"]
                }
            }

        Example:
            >>> json_str = graph.to_json()
            >>> import json
            >>> data = json.loads(json_str)
            >>> print(data["assets"]["bronze.orders"]["type"])
            'ingestion'

        """
        data = {
            "assets": {
                name: {
                    "type": asset.asset_type,
                    "status": asset.status,
                    "description": asset.description,
                }
                for name, asset in self.assets.items()
            },
            "edges": dict(self.edges),
        }
        return json.dumps(data, indent=2)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    JSON format string with indentation for readability.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_safe_id&#x22;" type="&#x22;(name) -> str&#x22;">
  Convert asset name to a Mermaid-safe identifier.

  Mermaid identifiers cannot contain hyphens or dots. This method
  replaces them with underscores for compatibility.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > LineageGraph.\_safe\_id("bronze.stg-orders")
    > > > 'bronze\_stg\_orders'
    > > > LineageGraph.\_safe\_id("silver.fct\_orders")
    > > > 'silver\_fct\_orders'
  </Callout>

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    This is an internal helper method used by to\_mermaid().
  </Callout>

  <PySourceCode>
    ```python
    @staticmethod
    def _safe_id(name: str) -> str:
        """Convert asset name to a Mermaid-safe identifier.

        Mermaid identifiers cannot contain hyphens or dots. This method
        replaces them with underscores for compatibility.

        Args:
            name: Original asset name (may contain hyphens, dots).

        Returns:
            Sanitized identifier safe for Mermaid syntax.

        Example:
            >>> LineageGraph._safe_id("bronze.stg-orders")
            'bronze_stg_orders'
            >>> LineageGraph._safe_id("silver.fct_orders")
            'silver_fct_orders'

        Note:
            This is an internal helper method used by to_mermaid().

        """
        return name.replace("-", "_").replace(".", "_")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Original asset name (may contain hyphens, dots).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Sanitized identifier safe for Mermaid syntax.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, assets=dict(), edges=(lambda: defaultdict(list))()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;assets&#x22;" type="&#x22;dict[str, Asset]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;edges&#x22;" type="&#x22;dict[str, list[str]]&#x22;" value="&#x22;(lambda: defaultdict(list))()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

# OpenMetadataLineageGraph (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/graph/OpenMetadataLineageGraph)



Simple directed graph for OpenMetadata lineage extraction.

Maintains assets and directed edges between them. Supports querying
downstream dependencies and exporting to multiple formats.

Attributes [#attributes]

<PyAttribute name="&#x22;assets&#x22;" type="&#x22;dict[str, Asset]&#x22;" value="&#x22;field(default_factory=dict)&#x22;">
  Dictionary mapping asset name to Asset object.
</PyAttribute>

<PyAttribute name="&#x22;edges&#x22;" type="&#x22;dict[str, list[str]]&#x22;" value="&#x22;field(default_factory=(lambda: defaultdict(list)))&#x22;">
  Dictionary mapping source asset to list of target assets.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;add_asset&#x22;" type="&#x22;(self, name, asset_type='unknown', status='unknown') -> None&#x22;">
  Add an asset node when it does not already exist.

  <PySourceCode>
    ```python
    def add_asset(self, name: str, asset_type: str = "unknown", status: str = "unknown") -> None:
        """Add an asset node when it does not already exist.

        Args:
            name: Unique asset identifier.
            asset_type: Type classification for the asset.
            status: Current status of the asset.

        Returns:
            None

        """
        if name not in self.assets:
            self.assets[name] = Asset(name=name, asset_type=asset_type, status=status)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Unique asset identifier.
    </PyParameter>

    <PyParameter name="&#x22;asset_type&#x22;" type="&#x22;str&#x22;" value="&#x22;'unknown'&#x22;">
      Type classification for the asset.
    </PyParameter>

    <PyParameter name="&#x22;status&#x22;" type="&#x22;str&#x22;" value="&#x22;'unknown'&#x22;">
      Current status of the asset.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;">
    None
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;add_edge&#x22;" type="&#x22;(self, source, target) -> None&#x22;">
  Add a directed edge between two assets.

  Creates asset nodes if they don't exist. Prevents duplicate edges.

  <PySourceCode>
    ```python
    def add_edge(self, source: str, target: str) -> None:
        """Add a directed edge between two assets.

        Creates asset nodes if they don't exist. Prevents duplicate edges.

        Args:
            source: Source asset name (upstream).
            target: Target asset name (downstream).

        Returns:
            None

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
      Source asset name (upstream).
    </PyParameter>

    <PyParameter name="&#x22;target&#x22;" type="&#x22;str&#x22;" value="undefined">
      Target asset name (downstream).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;">
    None
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_downstream&#x22;" type="&#x22;(self, asset_name, depth=None) -> set[str]&#x22;">
  Return all downstream assets reachable from one asset.

  Performs BFS traversal to find all downstream dependencies.

  <PySourceCode>
    ```python
    def get_downstream(self, asset_name: str, depth: int | None = None) -> set[str]:
        """Return all downstream assets reachable from one asset.

        Performs BFS traversal to find all downstream dependencies.

        Args:
            asset_name: Starting asset name.
            depth: Maximum traversal depth (None for unlimited).

        Returns:
            set[str]: Set of downstream asset names.

        """
        downstream: set[str] = set()
        visited: set[str] = set()
        queue = deque([(asset_name, 0)])

        while queue:
            current, current_depth = queue.popleft()
            if current in visited:
                continue
            visited.add(current)

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
      Starting asset name.
    </PyParameter>

    <PyParameter name="&#x22;depth&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;">
      Maximum traversal depth (None for unlimited).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;set&#x22;">
    set\[str]: Set of downstream asset names.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;to_json&#x22;" type="&#x22;(self) -> str&#x22;">
  Export the graph as JSON.

  <PySourceCode>
    ```python
    def to_json(self) -> str:
        """Export the graph as JSON.

        Returns:
            str: JSON string with assets and edges.

        """
        return json.dumps(
            {
                "assets": {
                    name: {
                        "type": asset.asset_type,
                        "status": asset.status,
                        "description": asset.description,
                    }
                    for name, asset in self.assets.items()
                },
                "edges": dict(self.edges),
            },
            indent=2,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    JSON string with assets and edges.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;to_dot&#x22;" type="&#x22;(self) -> str&#x22;">
  Export the graph as Graphviz DOT.

  <PySourceCode>
    ```python
    def to_dot(self) -> str:
        """Export the graph as Graphviz DOT.

        Returns:
            str: DOT format string for Graphviz rendering.

        """
        lines = ["digraph {", '  rankdir="LR";']
        for asset_name, asset in self.assets.items():
            color = {
                "ingestion": "lightblue",
                "transform": "lightgreen",
                "publish": "lightcoral",
                "unknown": "lightgray",
            }.get(asset.asset_type, "lightgray")
            lines.append(
                f'  "{asset_name}" [label="{asset_name}", shape="box", style="filled", '
                f'fillcolor="{color}"];'
            )
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
    DOT format string for Graphviz rendering.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;to_mermaid&#x22;" type="&#x22;(self) -> str&#x22;">
  Export the graph as Mermaid.

  <PySourceCode>
    ```python
    def to_mermaid(self) -> str:
        """Export the graph as Mermaid.

        Returns:
            str: Mermaid diagram syntax string.

        """
        lines = ["graph TD"]
        for asset_name in self.assets:
            lines.append(f'  {self._safe_id(asset_name)}["{asset_name}"]')
        for source, targets in self.edges.items():
            for target in targets:
                lines.append(f"  {self._safe_id(source)} --> {self._safe_id(target)}")
        return "\n".join(lines)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Mermaid diagram syntax string.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_safe_id&#x22;" type="&#x22;(name) -> str&#x22;">
  Convert an asset name into a Mermaid-safe identifier.

  <PySourceCode>
    ```python
    @staticmethod
    def _safe_id(name: str) -> str:
        """Convert an asset name into a Mermaid-safe identifier.

        Args:
            name: Original asset name.

        Returns:
            str: Sanitized identifier for Mermaid syntax.

        """
        return name.replace("-", "_").replace(".", "_")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Original asset name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Sanitized identifier for Mermaid syntax.
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

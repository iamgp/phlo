"""In-memory lineage graph used by OpenMetadata extraction flows.

Provides a simple directed graph implementation for tracking data lineage
between assets. Supports export to JSON, DOT (Graphviz), and Mermaid formats.

Example:
    >>> from phlo_openmetadata.graph import OpenMetadataLineageGraph
    >>> graph = OpenMetadataLineageGraph()
    >>> graph.add_edge("source_table", "transformed_table")
    >>> print(graph.to_mermaid())

"""

from __future__ import annotations

import json
from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass
class Asset:
    """Represents one asset in the OpenMetadata lineage graph.

    Attributes:
        name: Unique identifier for the asset.
        asset_type: Type of asset (e.g., 'ingestion', 'transform', 'publish').
        status: Current status of the asset.
        description: Optional description of the asset.

    Example:
        >>> asset = Asset(name="bronze.orders", asset_type="ingestion")
        >>> asset.name
        'bronze.orders'

    """

    name: str
    asset_type: str = "unknown"
    status: str = "unknown"
    description: str | None = None


@dataclass
class OpenMetadataLineageGraph:
    """Simple directed graph for OpenMetadata lineage extraction.

        Maintains assets and directed edges between them. Supports querying
    downstream dependencies and exporting to multiple formats.

    Attributes:
            assets: Dictionary mapping asset name to Asset object.
            edges: Dictionary mapping source asset to list of target assets.

    Example:
            >>> graph = OpenMetadataLineageGraph()
            >>> graph.add_edge("bronze.orders", "silver.orders_cleaned")
            >>> downstream = graph.get_downstream("bronze.orders")

    """

    assets: dict[str, Asset] = field(default_factory=dict)
    edges: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))

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

    @staticmethod
    def _safe_id(name: str) -> str:
        """Convert an asset name into a Mermaid-safe identifier.

        Args:
            name: Original asset name.

        Returns:
            str: Sanitized identifier for Mermaid syntax.

        """
        return name.replace("-", "_").replace(".", "_")

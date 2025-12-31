"""Build and analyze asset lineage graphs."""

from __future__ import annotations

import json
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class Asset:
    """Represents an asset node in the lineage graph."""

    name: str
    asset_type: str = "unknown"  # ingestion, transform, publish
    status: str = "unknown"  # success, warning, failure
    description: Optional[str] = None


@dataclass
class LineageGraph:
    """Graph of asset dependencies and lineage."""

    assets: dict[str, Asset] = field(default_factory=dict)
    edges: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))

    def add_asset(self, name: str, asset_type: str = "unknown", status: str = "unknown") -> None:
        """Add an asset to the graph."""
        if name not in self.assets:
            self.assets[name] = Asset(name=name, asset_type=asset_type, status=status)

    def add_edge(self, source: str, target: str) -> None:
        """Add an edge from source to target (source -> target)."""
        self.add_asset(source)
        self.add_asset(target)
        if target not in self.edges[source]:
            self.edges[source].append(target)

    def get_upstream(self, asset_name: str, depth: Optional[int] = None) -> Set[str]:
        """Get all upstream assets (dependencies)."""
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

    def get_downstream(self, asset_name: str, depth: Optional[int] = None) -> Set[str]:
        """Get all downstream assets (dependents)."""
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

    def get_impact(self, asset_name: str) -> dict:
        """Analyze impact of changes to an asset."""
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

    def to_ascii_tree(
        self, asset_name: str, direction: str = "both", depth: Optional[int] = None
    ) -> str:
        """
        Generate ASCII tree representation of lineage.

        Args:
            asset_name: Root asset to show
            direction: "upstream", "downstream", or "both"
            depth: Maximum depth to show
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

    def to_dot(self) -> str:
        """Generate Graphviz DOT format."""
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

    def to_mermaid(self) -> str:
        """Generate Mermaid format for documentation."""
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

    def to_json(self) -> str:
        """Generate JSON representation."""
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

    @staticmethod
    def _safe_id(name: str) -> str:
        """Convert asset name to safe identifier."""
        return name.replace("-", "_").replace(".", "_")


# Global lineage graph instance
_lineage_graph: Optional[LineageGraph] = None


def get_lineage_graph() -> LineageGraph:
    """Get or create global lineage graph."""
    global _lineage_graph
    if _lineage_graph is None:
        _lineage_graph = _build_lineage_from_dagster()
    return _lineage_graph


def _build_lineage_from_dagster() -> LineageGraph:
    """Build lineage graph from Dagster instance.

    Note: This method builds an empty graph that can be populated manually.
    Full Dagster integration requires accessing the running Dagster instance's
    GraphQL API or Definitions object directly, which is not available here.
    """
    graph = LineageGraph()

    # Return empty graph - lineage is built dynamically when
    # running within the Dagster context where Definitions are available
    logger.debug("Lineage graph initialized (empty - populate via Dagster context)")

    return graph

"""In-memory lineage graph used by OpenMetadata extraction flows."""

from __future__ import annotations

import json
from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass
class Asset:
    """Represents one asset in the OpenMetadata lineage graph."""

    name: str
    asset_type: str = "unknown"
    status: str = "unknown"
    description: str | None = None


@dataclass
class OpenMetadataLineageGraph:
    """Simple directed graph for OpenMetadata lineage extraction."""

    assets: dict[str, Asset] = field(default_factory=dict)
    edges: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))

    def add_asset(self, name: str, asset_type: str = "unknown", status: str = "unknown") -> None:
        """Add an asset node when it does not already exist."""
        if name not in self.assets:
            self.assets[name] = Asset(name=name, asset_type=asset_type, status=status)

    def add_edge(self, source: str, target: str) -> None:
        """Add a directed edge between two assets."""
        self.add_asset(source)
        self.add_asset(target)
        if target not in self.edges[source]:
            self.edges[source].append(target)

    def get_downstream(self, asset_name: str, depth: int | None = None) -> set[str]:
        """Return all downstream assets reachable from one asset."""
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
        """Export the graph as JSON."""
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
        """Export the graph as Graphviz DOT."""
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
        """Export the graph as Mermaid."""
        lines = ["graph TD"]
        for asset_name in self.assets:
            lines.append(f'  {self._safe_id(asset_name)}["{asset_name}"]')
        for source, targets in self.edges.items():
            for target in targets:
                lines.append(f"  {self._safe_id(source)} --> {self._safe_id(target)}")
        return "\n".join(lines)

    @staticmethod
    def _safe_id(name: str) -> str:
        """Convert an asset name into a Mermaid-safe identifier."""
        return name.replace("-", "_").replace(".", "_")

"""Hook plugin for updating the lineage graph."""

from __future__ import annotations

from typing import Any

from phlo.hooks import LineageEvent
from phlo.plugins.base import PluginMetadata
from phlo.plugins.hooks import HookFilter, HookPlugin, HookRegistration

from phlo_lineage.graph import get_lineage_graph


class LineageHookPlugin(HookPlugin):
    """Update the lineage graph from lineage hook events."""

    @property
    def metadata(self) -> PluginMetadata:
        """Metadata for the lineage hook plugin."""

        return PluginMetadata(
            name="lineage",
            version="0.1.0",
            description="Hook handlers for lineage updates",
        )

    def get_hooks(self) -> list[HookRegistration]:
        """Register the lineage update hook handler."""

        return [
            HookRegistration(
                hook_name="lineage_updates",
                handler=self._handle_lineage,
                filters=HookFilter(event_types={"lineage.edges"}),
            )
        ]

    def _handle_lineage(self, event: Any) -> None:
        """Apply lineage edges to the graph store."""

        if not isinstance(event, LineageEvent):
            return
        graph = get_lineage_graph()
        for source, target in event.edges:
            graph.add_edge(source, target)

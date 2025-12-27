"""Hook plugin for updating the lineage graph."""

from __future__ import annotations

from typing import Any

from phlo.hooks import LineageEvent
from phlo.plugins.base import PluginMetadata
from phlo.plugins.hooks import HookFilter, HookPlugin, HookRegistration

from phlo_lineage.graph import get_lineage_graph


class LineageHookPlugin(HookPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="lineage",
            version="0.1.0",
            description="Hook handlers for lineage updates",
        )

    def get_hooks(self) -> list[HookRegistration]:
        return [
            HookRegistration(
                hook_name="lineage_updates",
                handler=self._handle_lineage,
                filters=HookFilter(event_types={"lineage.edges"}),
            )
        ]

    def _handle_lineage(self, event: Any) -> None:
        if not isinstance(event, LineageEvent):
            return
        graph = get_lineage_graph()
        for source, target in event.edges:
            graph.add_edge(source, target)

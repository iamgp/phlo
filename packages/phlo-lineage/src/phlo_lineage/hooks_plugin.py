"""Hook plugin for updating the lineage graph."""

from __future__ import annotations

from typing import Any

from phlo.hooks import LineageEvent
from phlo.logging import get_logger
from phlo.plugins.base import PluginMetadata
from phlo.plugins.hooks import HookFilter, HookPlugin, HookRegistration

from phlo_lineage.graph import get_lineage_graph
from phlo_lineage.store import LineageStore, resolve_lineage_db_url

logger = get_logger(__name__)


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

        connection_string = resolve_lineage_db_url()
        if not connection_string:
            return

        try:
            store = LineageStore(connection_string)
            store.record_asset_edges(
                event.edges,
                asset_keys=event.asset_keys,
                metadata=event.metadata,
                tags=event.tags,
            )
        except Exception as exc:
            logger.warning("Failed to persist asset lineage edges: %s", exc)

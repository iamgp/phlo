"""Hook plugin for updating the lineage graph from events.

This module implements the LineageHookPlugin class, which integrates with the
Phlo hooks system to receive lineage events and update both the in-memory graph
and persistent store. It enables real-time lineage tracking as assets are
materialized in the pipeline.

Event Handling:
    The plugin subscribes to lineage_events hook type and specifically filters
    for lineage.edges events. When received, it:
    1. Updates the in-memory LineageGraph (immediate visibility)
    2. Persists edges to PostgreSQL LineageStore (durability)

Architecture:
    - Implements HookPlugin interface for plugin system integration
    - Uses lazy database connection resolution
    - Gracefully handles missing database configuration (logs only)
    - Failures in persistence don't affect in-memory graph updates

Performance:
    In-memory graph updates are synchronous and fast (O(1) per edge).
    Database persistence involves network round-trips and should be
    considered in high-throughput scenarios.

Example:
    The plugin is auto-discovered via entry points. No manual registration
    is required. Events are emitted by the orchestration layer during
    asset materialization.

See Also:
    phlo.hooks for the event system.
    phlo.plugins.hooks for plugin interface definitions.
    phlo_lineage.graph.get_lineage_graph() for the in-memory graph.

"""

from __future__ import annotations

from typing import Any

from phlo.hooks import LineageEvent
from phlo.logging import get_logger
from phlo.plugins.base import PluginMetadata
from phlo.plugins.hooks import HookFilter, HookPlugin, HookRegistration

from phlo_lineage.graph import get_lineage_graph
from phlo_lineage.store import LineageStore, resolve_lineage_db_url_with_postgres_fallback

logger = get_logger(__name__)


class LineageHookPlugin(HookPlugin):
    """Hook plugin that synchronizes lineage events to graph and database.

    This plugin subscribes to lineage events from the Phlo event system and
    ensures lineage information is propagated to both the in-memory graph
    (for immediate visibility) and the persistent store (for durability).

    Event Processing:
        When a LineageEvent is received:
        1. Edges are immediately added to the in-memory graph
        2. If database is configured, edges are persisted to PostgreSQL
        3. All operations are logged at appropriate levels

    Failure Handling:
        - Non-lineage events are silently ignored
        - Database connection failures are logged but don't crash processing
        - In-memory graph updates succeed even if persistence fails
        - Errors include rich context (edge count, asset keys)

    Registration:
        The plugin is auto-discovered via the phlo.hooks entry point.
        It registers for lineage_updates hook with a filter for
        lineage.edges event types.

    Attributes:
        metadata: PluginMetadata with name="lineage", version="0.1.0"

    Example:
        The plugin operates automatically once registered. Events are
        typically emitted by the orchestration layer:

        >>> from phlo.hooks import LineageEvent
        >>> event = LineageEvent(
        ...     edges=[("bronze.orders", "silver.stg_orders")],
        ...     asset_keys=["bronze.orders", "silver.stg_orders"],
        ... )
        >>> # Event is automatically processed by LineageHookPlugin

    See Also:
        phlo.plugins.hooks.HookPlugin for the base interface.

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for discovery and identification.

        Returns:
            PluginMetadata with:
                - name: "lineage"
                - version: "0.1.0"
                - description: "Hook handlers for lineage updates"

        Example:
            >>> plugin = LineageHookPlugin()
            >>> meta = plugin.metadata
            >>> print(meta.name)
            'lineage'

        """
        return PluginMetadata(
            name="lineage",
            version="0.1.0",
            description="Hook handlers for lineage updates",
        )

    def get_hooks(self) -> list[HookRegistration]:
        """Register hook handlers with the Phlo event system.

        Returns a list of HookRegistration objects defining which events
        this plugin wants to receive and which handler method to invoke.

        Returns:
            List containing one HookRegistration:
                - hook_name: "lineage_updates"
                - handler: self._handle_lineage method
                - filters: HookFilter(event_types={"lineage.edges"})

        Filtering:
            The filter ensures this plugin only receives lineage.edges
            event types, ignoring other lineage-related events.

        Example:
            >>> plugin = LineageHookPlugin()
            >>> hooks = plugin.get_hooks()
            >>> print(len(hooks))
            1
            >>> print(hooks[0].hook_name)
            'lineage_updates'

        See Also:
            phlo.plugins.hooks.HookRegistration for registration structure.

        """
        return [
            HookRegistration(
                hook_name="lineage_updates",
                handler=self._handle_lineage,
                filters=HookFilter(event_types={"lineage.edges"}),
            )
        ]

    def _handle_lineage(self, event: Any) -> None:
        """Process a lineage event and update graph and database.

        This is the core event handler method. It receives lineage events,
        updates the in-memory graph immediately, and attempts to persist
        to the database if configured.

        Args:
            event: Hook event payload. Must be a LineageEvent instance;
                other types are silently ignored.

        Processing Flow:
            1. Type check: Ignore non-LineageEvent objects
            2. Log start with edge count and asset key count
            3. Update in-memory graph via get_lineage_graph()
            4. Resolve database connection string
            5. If no database: log skip message and return
            6. Persist edges via LineageStore
            7. Log success with persisted edge count
            8. On exception: log warning with error details

        Logging:
            - INFO: lineage_sync_started, lineage_sync_succeeded
            - WARNING: lineage_sync_skipped_missing_db_url, Failed to persist

        Side Effects:
            - Modifies global _lineage_graph singleton
            - Writes to PostgreSQL phlo.asset_lineage_edges table
            - Emits structured log records

        Example:
            >>> from phlo.hooks import LineageEvent
            >>> event = LineageEvent(
            ...     event_type="lineage.edges",
            ...     edges=[("a", "b"), ("b", "c")],
            ...     asset_keys=["a", "b", "c"],
            ... )
            >>> plugin = LineageHookPlugin()
            >>> plugin._handle_lineage(event)

        Note:
            This method is called automatically by the hooks system.
            Manual invocation is primarily useful for testing.

        """
        if not isinstance(event, LineageEvent):
            return
        edge_count = len(event.edges)
        asset_key_count = len(event.asset_keys or [])
        graph = get_lineage_graph()
        for source, target in event.edges:
            graph.add_edge(source, target)

        connection_string = resolve_lineage_db_url_with_postgres_fallback()
        if not connection_string:
            logger.info(
                "lineage_sync_skipped_missing_db_url",
                event_type=event.event_type,
                edge_count=edge_count,
                asset_key_count=asset_key_count,
            )
            return

        logger.info(
            "lineage_sync_started",
            event_type=event.event_type,
            edge_count=edge_count,
            asset_key_count=asset_key_count,
        )
        try:
            store = LineageStore(connection_string)
            persisted_edges = store.record_asset_edges(
                event.edges,
                asset_keys=event.asset_keys,
                metadata=event.metadata,
                tags=event.tags,
            )
            logger.info(
                "lineage_sync_succeeded",
                event_type=event.event_type,
                edge_count=edge_count,
                asset_key_count=asset_key_count,
                persisted_edge_count=persisted_edges,
            )
        except Exception as exc:
            logger.warning(
                "Failed to persist asset lineage edges: %s",
                exc,
                event_type=event.event_type,
                edge_count=edge_count,
                asset_key_count=asset_key_count,
            )

"""Lineage sink capability provider for phlo-lineage.

This module implements the PhloLineageSink class, which wraps the low-level
LineageStore and graph functionality into a standardized capability interface.
It provides a simplified API for recording lineage events and querying lineage
information through the Phlo capability system.

The lineage sink enables:
    - Asset edge recording (source -> target dependencies)
    - Row-level lineage tracking with parent relationships
    - Column-level lineage mapping persistence
    - Graph retrieval for visualization
    - Row journey queries (ancestors and descendants)

Architecture:
    PhloLineageSink is exposed as a capability provider through the plugin
    system (see resource_provider.py). It wraps LineageStore for persistence
    and LineageGraph for in-memory analysis.

Example:
    >>> from phlo_lineage.lineage_sink import PhloLineageSink
    >>> sink = PhloLineageSink()
    >>>
    >>> # Record asset dependencies
    >>> sink.record_asset_edges([
    ...     ("bronze.orders", "silver.stg_orders"),
    ...     ("silver.stg_orders", "gold.fct_orders"),
    ... ])
    >>>
    >>> # Get the current graph
    >>> graph = sink.get_asset_graph()
    >>> print(f"Total assets: {len(graph.assets)}")

"""

from __future__ import annotations

from typing import Any

from phlo_lineage.graph import get_lineage_graph
from phlo_lineage.store import (
    ColumnLineage,
    LineageStore,
    resolve_lineage_db_url_with_postgres_fallback,
)


class PhloLineageSink:
    """Capability wrapper around phlo-lineage store and graph functionality.

    This class provides a simplified, capability-friendly interface to the
    lineage system. It handles connection management internally and exposes
    high-level methods for recording and querying lineage data.

    The sink is designed to be used as a capability provider in the Phlo
    plugin system, but can also be instantiated directly for programmatic use.

    Capabilities Provided:
        - Asset lineage edge recording
        - Row-level provenance tracking
        - Column-level mapping persistence
        - Graph access for visualization
        - Row journey analysis (ancestors/descendants)

    Configuration:
        Requires the PHLO_LINEAGE_DB_URL environment variable or standard
        PostgreSQL connection variables (POSTGRES_HOST, POSTGRES_PORT, etc.).

    Raises:
        RuntimeError: If database URL cannot be resolved when attempting
            to record or query data.

    Example:
        >>> sink = PhloLineageSink()
        >>>
        >>> # Record row lineage
        >>> sink.record_row_lineage(
        ...     row_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        ...     table_name="bronze.orders",
        ...     source_type="dlt",
        ...     parent_row_ids=[],
        ... )
        >>>
        >>> # Query row journey
        >>> journey = sink.get_row_journey(row_id="01ARZ3NDEKTSV4RRFFQ69G5FAV")
        >>> print(f"Ancestors: {len(journey['ancestors'])}")

    """

    def record_asset_edges(
        self,
        edges: list[tuple[str, str]],
        *,
        asset_keys: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
    ) -> int:
        """Persist directed asset lineage edges to the store.

        Records data flow relationships (source -> target) in the lineage
        database. Also creates or updates node entries for all assets
        mentioned in the edges.

        Args:
            edges: List of (source, target) tuples representing data flow
                direction. Each tuple indicates that target depends on source.
            asset_keys: Optional additional asset keys to register as nodes
                even if not connected by edges.
            metadata: Optional dictionary of metadata to attach to all edges
                in this batch. Common keys: run_id, timestamp, source_system.
            tags: Optional dictionary of string tags for categorization.

        Returns:
            Number of edges successfully persisted.

        Raises:
            RuntimeError: If the lineage database is not configured.
            Exception: Re-raised from LineageStore if database operation fails.

        Example:
            >>> sink = PhloLineageSink()
            >>> count = sink.record_asset_edges(
            ...     edges=[
            ...         ("bronze.orders", "silver.stg_orders"),
            ...         ("silver.stg_orders", "gold.fct_orders"),
            ...     ],
            ...     metadata={"run_id": "manual-001"},
            ... )
            >>> print(f"Recorded {count} edges")

        """
        return self._get_store().record_asset_edges(
            edges,
            asset_keys=asset_keys,
            metadata=metadata,
            tags=tags,
        )

    def record_row_lineage(
        self,
        *,
        row_id: str,
        table_name: str,
        source_type: str,
        parent_row_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Persist a single row-level lineage record.

        Records the provenance of an individual data row, including its origin
        and any parent rows it was derived from.

        Args:
            row_id: ULID string identifying the row. Should be generated via
                generate_row_id() or extracted from _phlo_row_id column.
            table_name: Fully qualified table name (e.g., "bronze.orders",
                "silver.stg_orders").
            source_type: Origin classification:
                - "dlt": Data loaded via dlt (data load tool)
                - "dbt": Data transformed via dbt
                - "external": Data from external systems
                - "manual": User-inserted data
            parent_row_ids: List of ULIDs for parent rows this row was derived
                from. Empty or None for root-level source rows.
            metadata: Optional dictionary with additional context such as
                run_id, partition keys, or processing timestamps.

        Raises:
            RuntimeError: If the lineage database is not configured.
            Exception: Re-raised from LineageStore if database operation fails.

        Example:
            >>> sink = PhloLineageSink()
            >>> sink.record_row_lineage(
            ...     row_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
            ...     table_name="bronze.orders",
            ...     source_type="dlt",
            ...     parent_row_ids=[],
            ...     metadata={"source": "api", "batch_id": "batch-001"},
            ... )

        """
        self._get_store().record_row(
            row_id=row_id,
            table_name=table_name,
            source_type=source_type,
            parent_row_ids=parent_row_ids,
            metadata=metadata,
        )

    def record_column_lineage(self, mappings: list[dict[str, Any]]) -> int:
        """Persist column-level lineage mappings.

        Records relationships between columns in upstream and downstream assets.
        Each mapping indicates that data from a source column flows into a target
        column.

        Args:
            mappings: List of dictionaries representing column lineage mappings.
                Each dict should contain:
                - source_asset: Upstream table/model name
                - source_column: Column name in source
                - target_asset: Downstream table/model name
                - target_column: Column name in target
                - source_type (optional): Origin of mapping, default "dbt_heuristic"
                - metadata (optional): Dictionary with additional context

        Returns:
            Number of mappings successfully persisted.

        Raises:
            RuntimeError: If the lineage database is not configured.
            Exception: Re-raised from LineageStore if database operation fails.

        Example:
            >>> sink = PhloLineageSink()
            >>> mappings = [
            ...     {
            ...         "source_asset": "bronze.orders",
            ...         "source_column": "order_id",
            ...         "target_asset": "silver.stg_orders",
            ...         "target_column": "order_id",
            ...         "source_type": "dbt_heuristic",
            ...         "metadata": {"confidence": 0.95},
            ...     },
            ... ]
            >>> count = sink.record_column_lineage(mappings)

        Note:
            The mappings parameter accepts raw dictionaries for convenience,
            which are converted to ColumnLineage dataclasses internally.

        """
        return self._get_store().record_column_lineage(
            [
                ColumnLineage(
                    source_asset=str(mapping["source_asset"]),
                    source_column=str(mapping["source_column"]),
                    target_asset=str(mapping["target_asset"]),
                    target_column=str(mapping["target_column"]),
                    source_type=str(mapping.get("source_type") or "dbt_heuristic"),
                    metadata=mapping.get("metadata")
                    if isinstance(mapping.get("metadata"), dict | type(None))
                    else None,
                )
                for mapping in mappings
            ]
        )

    def get_asset_graph(self) -> Any:
        """Return the current in-memory asset lineage graph.

        Retrieves the global LineageGraph singleton, which is lazily loaded
        from the persistent store on first access.

        Returns:
            LineageGraph instance containing all known assets and edges.
            May be empty if no lineage database is configured or if the
            database contains no lineage data.

        Example:
            >>> sink = PhloLineageSink()
            >>> graph = sink.get_asset_graph()
            >>>
            >>> # Analyze dependencies
            >>> upstream = graph.get_upstream("gold.fct_orders")
            >>> downstream = graph.get_downstream("bronze.orders")
            >>>
            >>> # Export visualization
            >>> dot = graph.to_dot()

        See Also:
            phlo_lineage.graph.LineageGraph for graph analysis methods.

        """
        return get_lineage_graph()

    def get_row_journey(self, *, row_id: str, depth: int = 10) -> Any:
        """Query the complete lineage journey for a single row.

        Retrieves current row information, all ancestor rows (upstream), and
        all descendant rows (downstream) in a single call.

        Args:
            row_id: ULID string identifying the row to query.
            depth: Maximum traversal depth for ancestor and descendant queries.
                Default is 10. Increase for deep lineage chains, decrease for
                performance with shallow queries.

        Returns:
            Dictionary with three keys:
                - current: Dict with row's own lineage info, or None if not found
                - ancestors: List of ancestor row dicts sorted by time desc
                - descendants: List of descendant row dicts sorted by time asc

        Raises:
            RuntimeError: If the lineage database is not configured.
            Exception: Re-raised from LineageStore if database query fails.

        Example:
            >>> sink = PhloLineageSink()
            >>> journey = sink.get_row_journey(
            ...     row_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
            ...     depth=5,
            ... )
            >>>
            >>> if journey["current"]:
            ...     print(f"Row in table: {journey['current']['table_name']}")
            ...     print(f"Ancestors: {len(journey['ancestors'])}")
            ...     print(f"Descendants: {len(journey['descendants'])}")

        Use Case:
            This method is ideal for data debugging and impact analysis:
            - Trace a problematic row back to its source
            - Determine which downstream reports depend on a row
            - Validate data transformation chains

        """
        store = self._get_store()
        return {
            "current": store.get_row(row_id),
            "ancestors": store.get_ancestors(row_id, max_depth=depth),
            "descendants": store.get_descendants(row_id, max_depth=depth),
        }

    @staticmethod
    def _get_store() -> LineageStore:
        """Retrieve or create a configured LineageStore instance.

        Resolves the database connection string from environment variables
        and returns a LineageStore instance.

        Returns:
            Configured LineageStore ready for operations.

        Raises:
            RuntimeError: If no lineage database URL can be resolved from
                environment variables (LINEAGE_DB_URL, PHLO_LINEAGE_DB_URL,
                or standard PostgreSQL variables).

        Note:
            This is a static method that creates a new store instance on each
            call. The LineageStore class itself manages schema caching.

        Example:
            >>> store = PhloLineageSink._get_store()
            >>> # Use store directly for advanced operations
            >>> rows = store.get_table_rows("bronze.orders", limit=10)

        See Also:
            resolve_lineage_db_url_with_postgres_fallback() for URL resolution logic.

        """
        connection_string = resolve_lineage_db_url_with_postgres_fallback()
        if not connection_string:
            raise RuntimeError("Lineage sink requires PHLO_LINEAGE_DB_URL to be configured.")
        return LineageStore(connection_string)

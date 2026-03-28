"""Lineage sink capability provider for phlo-lineage."""

from __future__ import annotations

from typing import Any

from phlo_lineage.graph import get_lineage_graph
from phlo_lineage.store import (
    ColumnLineage,
    LineageStore,
    resolve_lineage_db_url_with_postgres_fallback,
)


class PhloLineageSink:
    """Capability wrapper around the phlo-lineage store and graph."""

    def record_asset_edges(
        self,
        edges: list[tuple[str, str]],
        *,
        asset_keys: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
    ) -> int:
        """Persist directed asset lineage edges."""
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
        """Persist one row-level lineage record."""
        self._get_store().record_row(
            row_id=row_id,
            table_name=table_name,
            source_type=source_type,
            parent_row_ids=parent_row_ids,
            metadata=metadata,
        )

    def record_column_lineage(self, mappings: list[dict[str, Any]]) -> int:
        """Persist column-level lineage mappings."""
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
        """Return the current in-memory asset lineage graph."""
        return get_lineage_graph()

    def get_row_journey(self, *, row_id: str, depth: int = 10) -> Any:
        """Return current, ancestor, and descendant lineage for one row."""
        store = self._get_store()
        return {
            "current": store.get_row(row_id),
            "ancestors": store.get_ancestors(row_id, max_depth=depth),
            "descendants": store.get_descendants(row_id, max_depth=depth),
        }

    @staticmethod
    def _get_store() -> LineageStore:
        """Return a configured lineage store."""
        connection_string = resolve_lineage_db_url_with_postgres_fallback()
        if not connection_string:
            raise RuntimeError("Lineage sink requires PHLO_LINEAGE_DB_URL to be configured.")
        return LineageStore(connection_string)

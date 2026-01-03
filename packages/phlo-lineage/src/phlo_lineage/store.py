"""Row-level lineage store for Phlo.

Tracks individual row provenance across the data pipeline using ULIDs.
Stores lineage metadata in PostgreSQL for deterministic querying.

Example:
    >>> from phlo_lineage.store import LineageStore
    >>> store = LineageStore("postgresql://...")
    >>> store.record_row("01ARZ3NDEKTSV4RRFFQ69G5FAV", "bronze.dlt_events", "dlt")
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import psycopg2
import ulid

from phlo.logging import get_logger

logger = get_logger(__name__)

_LINEAGE_DB_KEYS = (
    "LINEAGE_DB_URL",
    "PHLO_LINEAGE_DB_URL",
    "DAGSTER_PG_DB_CONNECTION_STRING",
)


def resolve_lineage_db_url() -> str | None:
    """Resolve the lineage database URL from environment variables."""
    for key in _LINEAGE_DB_KEYS:
        value = os.environ.get(key)
        if value:
            return value
    return None


def generate_row_id() -> str:
    """Generate a new ULID for a row.

    ULIDs are:
    - Lexicographically sortable (timestamp prefix)
    - Globally unique (128-bit)
    - URL-safe (Crockford's Base32)
    """
    return str(ulid.ULID())


class LineageStore:
    """Row-level lineage store backed by PostgreSQL.

    Provides CRUD operations for tracking row provenance.
    Schema is auto-created on first use - zero configuration needed.
    """

    _schema_initialized: bool = False

    def __init__(self, connection_string: str):
        """Initialize LineageStore.

        Args:
            connection_string: PostgreSQL connection string
                e.g., "postgresql://user:pass@localhost:5432/dagster"
        """
        self.connection_string = connection_string

    def _ensure_schema(self) -> None:
        """Ensure schema exists, creating it if necessary.

        Called automatically on first database operation.
        Uses class-level flag to only run once per process.
        """
        if LineageStore._schema_initialized:
            return

        try:
            self.setup_schema()
            LineageStore._schema_initialized = True
        except Exception as e:
            # Schema might already exist (concurrent init), that's OK
            if "already exists" in str(e).lower():
                LineageStore._schema_initialized = True
            else:
                logger.warning(f"Lineage schema init failed (non-fatal): {e}")

    def setup_schema(self) -> None:
        """Create the lineage schema and tables if they don't exist."""
        sql_path = Path(__file__).parent / "sql" / "001_create_schema.sql"

        with open(sql_path) as f:
            schema_sql = f.read()

        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
            conn.commit()

        logger.info("Lineage schema setup complete")

    def record_row(
        self,
        row_id: str,
        table_name: str,
        source_type: str = "dlt",
        parent_row_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record a single row's lineage.

        Args:
            row_id: ULID of the row
            table_name: Fully qualified table name (e.g., "bronze.dlt_events")
            source_type: Origin type ("dlt", "dbt", "external")
            parent_row_ids: List of parent row ULIDs (for transforms/aggregations)
            metadata: Additional metadata (run_id, partition, etc.)
        """
        self._ensure_schema()
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO phlo.row_lineage
                    (row_id, table_name, source_type, parent_row_ids, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (row_id) DO UPDATE SET
                        table_name = EXCLUDED.table_name,
                        source_type = EXCLUDED.source_type,
                        parent_row_ids = EXCLUDED.parent_row_ids,
                        metadata = EXCLUDED.metadata
                    """,
                    (
                        row_id,
                        table_name,
                        source_type,
                        parent_row_ids,
                        json.dumps(metadata) if metadata else None,
                    ),
                )
            conn.commit()

    def record_rows_batch(
        self,
        rows: list[dict[str, Any]],
        table_name: str,
        source_type: str = "dlt",
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Record multiple rows' lineage in a batch.

        Args:
            rows: List of row dicts, each must have "_phlo_row_id" key
            table_name: Fully qualified table name
            source_type: Origin type
            metadata: Metadata applied to all rows

        Returns:
            Number of rows recorded
        """
        if not rows:
            return 0

        values = []
        for row in rows:
            row_id = row.get("_phlo_row_id")
            if not row_id:
                continue
            values.append(
                (
                    row_id,
                    table_name,
                    source_type,
                    None,  # parent_row_ids
                    json.dumps(metadata) if metadata else None,
                )
            )

        if not values:
            return 0

        self._ensure_schema()
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                # Use execute_values for efficient batch insert
                from psycopg2.extras import execute_values

                execute_values(
                    cur,
                    """
                    INSERT INTO phlo.row_lineage
                    (row_id, table_name, source_type, parent_row_ids, metadata)
                    VALUES %s
                    ON CONFLICT (row_id) DO NOTHING
                    """,
                    values,
                )
            conn.commit()

        return len(values)

    def record_asset_nodes(
        self,
        asset_keys: list[str],
        *,
        asset_type: str | None = None,
        status: str | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
        tags: dict[str, Any] | None = None,
    ) -> int:
        """Record asset nodes seen in lineage events."""
        if not asset_keys:
            return 0

        unique_keys = sorted(set(asset_keys))
        values = [
            (
                asset_key,
                asset_type,
                status,
                description,
                json.dumps(metadata) if metadata else None,
                json.dumps(tags) if tags else None,
            )
            for asset_key in unique_keys
        ]

        self._ensure_schema()
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                from psycopg2.extras import execute_values

                execute_values(
                    cur,
                    """
                    INSERT INTO phlo.asset_lineage_nodes
                    (asset_key, asset_type, status, description, metadata, tags)
                    VALUES %s
                    ON CONFLICT (asset_key) DO UPDATE SET
                        asset_type = COALESCE(EXCLUDED.asset_type, phlo.asset_lineage_nodes.asset_type),
                        status = COALESCE(EXCLUDED.status, phlo.asset_lineage_nodes.status),
                        description = COALESCE(
                            EXCLUDED.description, phlo.asset_lineage_nodes.description
                        ),
                        metadata = COALESCE(EXCLUDED.metadata, phlo.asset_lineage_nodes.metadata),
                        tags = COALESCE(EXCLUDED.tags, phlo.asset_lineage_nodes.tags),
                        updated_at = NOW()
                    """,
                    values,
                )
            conn.commit()

        return len(values)

    def record_asset_edges(
        self,
        edges: list[tuple[str, str]],
        *,
        asset_keys: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        tags: dict[str, Any] | None = None,
    ) -> int:
        """Record asset lineage edges."""
        if not edges and not asset_keys:
            return 0

        node_keys: set[str] = set(asset_keys or [])
        for source, target in edges:
            node_keys.add(source)
            node_keys.add(target)

        if node_keys:
            self.record_asset_nodes(
                list(node_keys),
                metadata=metadata,
                tags=tags,
            )

        if not edges:
            return 0

        values = [
            (
                source,
                target,
                json.dumps(metadata) if metadata else None,
                json.dumps(tags) if tags else None,
            )
            for source, target in edges
        ]

        self._ensure_schema()
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                from psycopg2.extras import execute_values

                execute_values(
                    cur,
                    """
                    INSERT INTO phlo.asset_lineage_edges
                    (source_asset, target_asset, metadata, tags)
                    VALUES %s
                    ON CONFLICT (source_asset, target_asset) DO UPDATE SET
                        metadata = COALESCE(EXCLUDED.metadata, phlo.asset_lineage_edges.metadata),
                        tags = COALESCE(EXCLUDED.tags, phlo.asset_lineage_edges.tags),
                        updated_at = NOW()
                    """,
                    values,
                )
            conn.commit()

        return len(values)

    def list_asset_nodes(self) -> list[dict[str, Any]]:
        """List all asset nodes."""
        self._ensure_schema()
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT asset_key, asset_type, status, description, metadata, tags,
                           created_at, updated_at
                    FROM phlo.asset_lineage_nodes
                    """
                )
                rows = cur.fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            results.append(
                {
                    "asset_key": row[0],
                    "asset_type": row[1],
                    "status": row[2],
                    "description": row[3],
                    "metadata": row[4],
                    "tags": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                    "updated_at": row[7].isoformat() if row[7] else None,
                }
            )
        return results

    def list_asset_edges(self) -> list[dict[str, Any]]:
        """List all asset lineage edges."""
        self._ensure_schema()
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT source_asset, target_asset, metadata, tags, created_at, updated_at
                    FROM phlo.asset_lineage_edges
                    """
                )
                rows = cur.fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            results.append(
                {
                    "source_asset": row[0],
                    "target_asset": row[1],
                    "metadata": row[2],
                    "tags": row[3],
                    "created_at": row[4].isoformat() if row[4] else None,
                    "updated_at": row[5].isoformat() if row[5] else None,
                }
            )
        return results

    def get_row(self, row_id: str) -> dict[str, Any] | None:
        """Get lineage info for a single row.

        Args:
            row_id: ULID of the row

        Returns:
            Dict with row lineage info, or None if not found
        """
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT row_id, table_name, source_type, parent_row_ids,
                           created_at, metadata
                    FROM phlo.row_lineage
                    WHERE row_id = %s
                    """,
                    (row_id,),
                )
                row = cur.fetchone()

        if not row:
            return None

        return {
            "row_id": row[0],
            "table_name": row[1],
            "source_type": row[2],
            "parent_row_ids": row[3] or [],
            "created_at": row[4].isoformat() if row[4] else None,
            "metadata": row[5],
        }

    def get_ancestors(self, row_id: str, max_depth: int = 10) -> list[dict[str, Any]]:
        """Get all ancestor rows recursively.

        Uses a recursive CTE to traverse parent relationships.

        Args:
            row_id: ULID of the starting row
            max_depth: Maximum traversal depth

        Returns:
            List of ancestor row lineage records
        """
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    WITH RECURSIVE ancestors AS (
                        -- Base case: get parents of the starting row
                        SELECT rl.row_id, rl.table_name, rl.source_type,
                               rl.parent_row_ids, rl.created_at, rl.metadata,
                               1 as depth
                        FROM phlo.row_lineage rl
                        WHERE rl.row_id = ANY(
                            SELECT unnest(parent_row_ids)
                            FROM phlo.row_lineage
                            WHERE row_id = %s
                        )

                        UNION ALL

                        -- Recursive case: get parents of parents
                        SELECT rl.row_id, rl.table_name, rl.source_type,
                               rl.parent_row_ids, rl.created_at, rl.metadata,
                               a.depth + 1
                        FROM phlo.row_lineage rl
                        INNER JOIN ancestors a
                            ON rl.row_id = ANY(a.parent_row_ids)
                        WHERE a.depth < %s
                    )
                    SELECT DISTINCT row_id, table_name, source_type,
                           parent_row_ids, created_at, metadata
                    FROM ancestors
                    ORDER BY created_at DESC
                    """,
                    (row_id, max_depth),
                )
                rows = cur.fetchall()

        return [
            {
                "row_id": row[0],
                "table_name": row[1],
                "source_type": row[2],
                "parent_row_ids": row[3] or [],
                "created_at": row[4].isoformat() if row[4] else None,
                "metadata": row[5],
            }
            for row in rows
        ]

    def get_descendants(self, row_id: str, max_depth: int = 10) -> list[dict[str, Any]]:
        """Get all descendant rows recursively.

        Args:
            row_id: ULID of the starting row
            max_depth: Maximum traversal depth

        Returns:
            List of descendant row lineage records
        """
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    WITH RECURSIVE descendants AS (
                        -- Base case: find rows that have this row as parent
                        SELECT rl.row_id, rl.table_name, rl.source_type,
                               rl.parent_row_ids, rl.created_at, rl.metadata,
                               1 as depth
                        FROM phlo.row_lineage rl
                        WHERE %s = ANY(rl.parent_row_ids)

                        UNION ALL

                        -- Recursive case: find children of children
                        SELECT rl.row_id, rl.table_name, rl.source_type,
                               rl.parent_row_ids, rl.created_at, rl.metadata,
                               d.depth + 1
                        FROM phlo.row_lineage rl
                        INNER JOIN descendants d ON d.row_id = ANY(rl.parent_row_ids)
                        WHERE d.depth < %s
                    )
                    SELECT DISTINCT row_id, table_name, source_type,
                           parent_row_ids, created_at, metadata
                    FROM descendants
                    ORDER BY created_at ASC
                    """,
                    (row_id, max_depth),
                )
                rows = cur.fetchall()

        return [
            {
                "row_id": row[0],
                "table_name": row[1],
                "source_type": row[2],
                "parent_row_ids": row[3] or [],
                "created_at": row[4].isoformat() if row[4] else None,
                "metadata": row[5],
            }
            for row in rows
        ]

    def get_table_rows(self, table_name: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent rows for a table.

        Args:
            table_name: Fully qualified table name
            limit: Maximum rows to return

        Returns:
            List of row lineage records
        """
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT row_id, table_name, source_type, parent_row_ids,
                           created_at, metadata
                    FROM phlo.row_lineage
                    WHERE table_name = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (table_name, limit),
                )
                rows = cur.fetchall()

        return [
            {
                "row_id": row[0],
                "table_name": row[1],
                "source_type": row[2],
                "parent_row_ids": row[3] or [],
                "created_at": row[4].isoformat() if row[4] else None,
                "metadata": row[5],
            }
            for row in rows
        ]

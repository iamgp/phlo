"""Row-level and column-level lineage store for Phlo.

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
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import psycopg2
import ulid

from phlo.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ColumnLineage:
    """A single column-to-column lineage mapping between two assets."""

    source_asset: str
    source_column: str
    target_asset: str
    target_column: str
    source_type: str = "dbt_heuristic"
    metadata: dict[str, Any] | None = None


_LINEAGE_DB_KEYS = (
    "LINEAGE_DB_URL",
    "PHLO_LINEAGE_DB_URL",
    "DAGSTER_PG_DB_CONNECTION_STRING",
)


def resolve_lineage_db_url() -> str | None:
    """Resolve the lineage database URL from environment or Postgres defaults."""
    for key in _LINEAGE_DB_KEYS:
        value = os.environ.get(key)
        if value:
            return value
    host, port = _resolve_postgres_host(
        os.environ.get("POSTGRES_HOST", "postgres"),
        int(os.environ.get("POSTGRES_PORT", "5432")),
    )
    user = quote_plus(os.environ.get("POSTGRES_USER", "phlo"))
    password = quote_plus(os.environ.get("POSTGRES_PASSWORD", "phlo"))
    database = quote_plus(os.environ.get("POSTGRES_DB", "phlo"))
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def _resolve_postgres_host(host: str, port: int) -> tuple[str, int]:
    """Resolve Docker Postgres hostnames to localhost when running on the host."""
    if host in {"localhost", "127.0.0.1"}:
        return host, port
    try:
        socket.gethostbyname(host)
        return host, port
    except socket.gaierror:
        exposed_port = int(os.environ.get("POSTGRES_PORT", str(port)))
        logger.debug(
            "lineage_db_host_resolved_to_localhost",
            original_host=host,
            original_port=port,
            resolved_port=exposed_port,
        )
        return "localhost", exposed_port


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

        if self._schema_exists():
            LineageStore._schema_initialized = True
            return

        try:
            self.setup_schema()
            LineageStore._schema_initialized = True
        except Exception as e:
            if self._schema_exists() or "already exists" in str(e).lower():
                LineageStore._schema_initialized = True
            else:
                logger.warning("lineage_schema_init_failed", error=str(e))

    def _schema_exists(self) -> bool:
        """Return True when the lineage schema has already been created."""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            to_regclass('phlo.asset_lineage_nodes'),
                            to_regclass('phlo.asset_lineage_edges'),
                            to_regclass('phlo.column_lineage')
                        """
                    )
                    result = cur.fetchone()
        except Exception:
            return False
        if result is None:
            return False
        return all(value is not None for value in result)

    def setup_schema(self) -> None:
        """Create the lineage schema and tables if they don't exist.

        Executes all ``sql/*.sql`` files in sorted order to support
        incremental schema migrations.
        """
        sql_dir = Path(__file__).parent / "sql"
        sql_files = sorted(sql_dir.glob("*.sql"))

        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                for sql_file in sql_files:
                    cur.execute(sql_file.read_text())
            conn.commit()

        logger.info("lineage_schema_setup_complete", migration_count=len(sql_files))

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
        parent_count = len(parent_row_ids or [])
        logger.info(
            "lineage_record_row_started",
            table_name=table_name,
            source_type=source_type,
            parent_row_count=parent_count,
        )
        try:
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
            logger.info(
                "lineage_record_row_succeeded",
                table_name=table_name,
                source_type=source_type,
                parent_row_count=parent_count,
            )
        except Exception:
            logger.warning(
                "lineage_record_row_failed",
                table_name=table_name,
                source_type=source_type,
                parent_row_count=parent_count,
                exc_info=True,
            )
            raise

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

        requested_count = len(rows)
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

        inserted_count = len(values)
        skipped_count = requested_count - inserted_count
        logger.info(
            "lineage_record_rows_batch_started",
            table_name=table_name,
            source_type=source_type,
            requested_count=requested_count,
            insert_count=inserted_count,
            skipped_missing_row_id_count=skipped_count,
        )
        try:
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
            logger.info(
                "lineage_record_rows_batch_succeeded",
                table_name=table_name,
                source_type=source_type,
                requested_count=requested_count,
                insert_count=inserted_count,
                skipped_missing_row_id_count=skipped_count,
            )
        except Exception:
            logger.warning(
                "lineage_record_rows_batch_failed",
                table_name=table_name,
                source_type=source_type,
                requested_count=requested_count,
                insert_count=inserted_count,
                skipped_missing_row_id_count=skipped_count,
                exc_info=True,
            )
            raise

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

        requested_count = len(asset_keys)
        upsert_count = len(values)
        logger.info(
            "lineage_record_asset_nodes_started",
            requested_count=requested_count,
            upsert_count=upsert_count,
        )
        try:
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
            logger.info(
                "lineage_record_asset_nodes_succeeded",
                requested_count=requested_count,
                upsert_count=upsert_count,
            )
        except Exception:
            logger.warning(
                "lineage_record_asset_nodes_failed",
                requested_count=requested_count,
                upsert_count=upsert_count,
                exc_info=True,
            )
            raise

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

        edge_count = len(edges)
        explicit_asset_key_count = len(asset_keys or [])
        node_keys: set[str] = set(asset_keys or [])
        for source, target in edges:
            node_keys.add(source)
            node_keys.add(target)

        logger.info(
            "lineage_record_asset_edges_started",
            edge_count=edge_count,
            explicit_asset_key_count=explicit_asset_key_count,
            node_key_count=len(node_keys),
        )
        persisted_node_count = 0
        persisted_edge_count = 0
        try:
            if node_keys:
                persisted_node_count = self.record_asset_nodes(
                    list(node_keys),
                    metadata=metadata,
                    tags=tags,
                )

            if edges:
                values = [
                    (
                        source,
                        target,
                        json.dumps(metadata) if metadata else None,
                        json.dumps(tags) if tags else None,
                    )
                    for source, target in edges
                ]
                persisted_edge_count = len(values)
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
            logger.info(
                "lineage_record_asset_edges_succeeded",
                edge_count=edge_count,
                explicit_asset_key_count=explicit_asset_key_count,
                node_key_count=len(node_keys),
                persisted_node_count=persisted_node_count,
                persisted_edge_count=persisted_edge_count,
            )
        except Exception:
            logger.warning(
                "lineage_record_asset_edges_failed",
                edge_count=edge_count,
                explicit_asset_key_count=explicit_asset_key_count,
                node_key_count=len(node_keys),
                persisted_node_count=persisted_node_count,
                persisted_edge_count=persisted_edge_count,
                exc_info=True,
            )
            raise

        return persisted_edge_count

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

    # ------------------------------------------------------------------
    # Column-level lineage
    # ------------------------------------------------------------------

    def record_column_lineage(self, mappings: list[ColumnLineage]) -> int:
        """Batch-insert column lineage mappings.

        Uses ``execute_values`` for efficiency.  Duplicate primary keys
        are silently skipped (``ON CONFLICT DO NOTHING``).

        Args:
            mappings: Column lineage records to persist.

        Returns:
            Number of mappings submitted for insert.
        """
        if not mappings:
            return 0

        values = [
            (
                m.source_asset,
                m.source_column,
                m.target_asset,
                m.target_column,
                m.source_type,
                json.dumps(m.metadata) if m.metadata else None,
            )
            for m in mappings
        ]

        logger.info("column_lineage_record_started", mapping_count=len(values))
        try:
            self._ensure_schema()
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    from psycopg2.extras import execute_values

                    execute_values(
                        cur,
                        """
                        INSERT INTO phlo.column_lineage
                        (source_asset, source_column, target_asset, target_column,
                         source_type, metadata)
                        VALUES %s
                        ON CONFLICT DO NOTHING
                        """,
                        values,
                    )
                conn.commit()
            logger.info("column_lineage_record_succeeded", mapping_count=len(values))
        except Exception:
            logger.warning(
                "column_lineage_record_failed",
                mapping_count=len(values),
                exc_info=True,
            )
            raise

        return len(values)

    def get_upstream_columns(
        self,
        target_asset: str,
        target_column: str | None = None,
    ) -> list[ColumnLineage]:
        """Query upstream column lineage for a target asset.

        Args:
            target_asset: Asset key of the downstream asset.
            target_column: Optional column name to narrow the query.

        Returns:
            List of ``ColumnLineage`` records.
        """
        self._ensure_schema()

        if target_column is not None:
            query = """
                SELECT source_asset, source_column, target_asset, target_column,
                       source_type, metadata
                FROM phlo.column_lineage
                WHERE target_asset = %s AND target_column = %s
            """
            params: tuple[str, ...] = (target_asset, target_column)
        else:
            query = """
                SELECT source_asset, source_column, target_asset, target_column,
                       source_type, metadata
                FROM phlo.column_lineage
                WHERE target_asset = %s
            """
            params = (target_asset,)

        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

        return [
            ColumnLineage(
                source_asset=r[0],
                source_column=r[1],
                target_asset=r[2],
                target_column=r[3],
                source_type=r[4],
                metadata=r[5],
            )
            for r in rows
        ]

    def get_downstream_columns(
        self,
        source_asset: str,
        source_column: str | None = None,
    ) -> list[ColumnLineage]:
        """Query downstream column lineage for a source asset.

        Args:
            source_asset: Asset key of the upstream asset.
            source_column: Optional column name to narrow the query.

        Returns:
            List of ``ColumnLineage`` records.
        """
        self._ensure_schema()

        if source_column is not None:
            query = """
                SELECT source_asset, source_column, target_asset, target_column,
                       source_type, metadata
                FROM phlo.column_lineage
                WHERE source_asset = %s AND source_column = %s
            """
            params: tuple[str, ...] = (source_asset, source_column)
        else:
            query = """
                SELECT source_asset, source_column, target_asset, target_column,
                       source_type, metadata
                FROM phlo.column_lineage
                WHERE source_asset = %s
            """
            params = (source_asset,)

        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

        return [
            ColumnLineage(
                source_asset=r[0],
                source_column=r[1],
                target_asset=r[2],
                target_column=r[3],
                source_type=r[4],
                metadata=r[5],
            )
            for r in rows
        ]

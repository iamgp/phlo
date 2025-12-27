"""Publish Trino marts into Postgres with hook events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from psycopg2 import sql
from psycopg2.extras import execute_values

from phlo.config import get_settings
from phlo.hooks import PublishEventContext, PublishEventEmitter


@dataclass(frozen=True)
class TablePublishStats:
    """Summary stats for a published table."""

    row_count: int
    column_count: int


def publish_marts_to_postgres(
    *,
    context: Any,
    trino: Any,
    postgres: Any,
    tables_to_publish: dict[str, str],
    data_source: str,
    target_schema: str | None = None,
    batch_size: int = 10_000,
) -> dict[str, TablePublishStats]:
    """Copy Trino tables into Postgres and emit publish lifecycle events."""

    settings = get_settings()
    schema = target_schema or settings.postgres_mart_schema
    asset_key = _resolve_asset_key(context, data_source)
    emitter = PublishEventEmitter(
        PublishEventContext(
            asset_key=asset_key,
            target_system="postgres",
            tables=tables_to_publish,
            tags={"source": data_source, "target": "postgres"},
        )
    )

    emitter.emit_start()

    stats: dict[str, TablePublishStats] = {}
    try:
        _ensure_schema(postgres, schema)
        for target_table, source_table in tables_to_publish.items():
            row_count, column_count = _copy_table(
                trino=trino,
                postgres=postgres,
                source_table=source_table,
                target_schema=schema,
                target_table=target_table,
                batch_size=batch_size,
            )
            stats[target_table] = TablePublishStats(
                row_count=row_count,
                column_count=column_count,
            )
        emitter.emit_end(
            status="success",
            metrics={
                "tables": {
                    name: {"row_count": s.row_count, "column_count": s.column_count}
                    for name, s in stats.items()
                }
            },
        )
        return stats
    except Exception as exc:
        emitter.emit_end(status="failure", error=str(exc))
        raise


def _ensure_schema(postgres: Any, schema: str) -> None:
    """Create the target schema if it is missing."""

    with postgres.cursor() as cursor:
        cursor.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema)))
    postgres.commit()


def _split_trino_qualified_name(name: str) -> list[tuple[str, bool]]:
    """Split a Trino qualified name into parts and track quoted identifiers."""

    parts: list[tuple[str, bool]] = []
    buffer: list[str] = []
    in_quotes = False
    part_quoted = False
    index = 0
    while index < len(name):
        char = name[index]
        if char == '"':
            if in_quotes and index + 1 < len(name) and name[index + 1] == '"':
                buffer.append('"')
                index += 1
            else:
                in_quotes = not in_quotes
                part_quoted = True
        elif char == "." and not in_quotes:
            part = "".join(buffer)
            if not part:
                raise ValueError("Trino table name has an empty identifier part.")
            parts.append((part, part_quoted))
            buffer = []
            part_quoted = False
        elif not in_quotes and char.isspace():
            pass
        else:
            buffer.append(char)
        index += 1
    if in_quotes:
        raise ValueError("Trino table name has an unterminated quoted identifier.")
    part = "".join(buffer)
    if not part:
        raise ValueError("Trino table name has an empty identifier part.")
    parts.append((part, part_quoted))
    return parts


def _quote_trino_identifier(identifier: str, *, was_quoted: bool) -> str:
    """Quote a single Trino identifier, preserving case when already quoted."""

    if not identifier:
        raise ValueError("Trino identifier cannot be empty.")
    normalized = identifier if was_quoted else identifier.lower()
    escaped = normalized.replace('"', '""')
    return f'"{escaped}"'


def _quote_trino_qualified_name(name: str) -> str:
    """Quote a fully qualified Trino table name for safe SQL usage."""

    parts = _split_trino_qualified_name(name)
    return ".".join(
        _quote_trino_identifier(part, was_quoted=was_quoted) for part, was_quoted in parts
    )


def _copy_table(
    *,
    trino: Any,
    postgres: Any,
    source_table: str,
    target_schema: str,
    target_table: str,
    batch_size: int,
) -> tuple[int, int]:
    """Copy a single Trino table into Postgres and return row/column counts."""

    source_table_ref = _quote_trino_qualified_name(source_table)
    columns = _describe_trino_table(trino, source_table_ref)
    column_defs = [
        sql.SQL("{} {}").format(sql.Identifier(name), sql.SQL(pg_type))
        for name, pg_type, _expr in columns
    ]
    column_idents = [sql.Identifier(name) for name, _pg_type, _expr in columns]
    select_exprs = [expr for _name, _pg_type, expr in columns]

    with postgres.cursor() as cursor:
        cursor.execute(
            sql.SQL("DROP TABLE IF EXISTS {}.{}").format(
                sql.Identifier(target_schema),
                sql.Identifier(target_table),
            )
        )
        cursor.execute(
            sql.SQL("CREATE TABLE {}.{} ({})").format(
                sql.Identifier(target_schema),
                sql.Identifier(target_table),
                sql.SQL(", ").join(column_defs),
            )
        )
    postgres.commit()

    insert_query = sql.SQL("INSERT INTO {}.{} ({}) VALUES %s").format(
        sql.Identifier(target_schema),
        sql.Identifier(target_table),
        sql.SQL(", ").join(column_idents),
    )

    row_count = 0
    with trino.cursor() as trino_cursor:
        trino_cursor.execute(f"SELECT {', '.join(select_exprs)} FROM {source_table_ref}")
        with postgres.cursor() as pg_cursor:
            while True:
                rows = trino_cursor.fetchmany(batch_size)
                if not rows:
                    break
                execute_values(pg_cursor, insert_query, rows, page_size=batch_size)
                row_count += len(rows)
    postgres.commit()

    return row_count, len(columns)


def _describe_trino_table(trino: Any, source_table_ref: str) -> list[tuple[str, str, str]]:
    """Return column names, Postgres types, and Trino select expressions."""

    with trino.cursor() as cursor:
        cursor.execute(f"DESCRIBE {source_table_ref}")
        rows = cursor.fetchall()
    columns: list[tuple[str, str, str]] = []
    for row in rows:
        if not row or len(row) < 2:
            continue
        name = str(row[0])
        trino_type = str(row[1])
        pg_type, expr = _trino_type_to_postgres(name, trino_type)
        columns.append((name, pg_type, expr))
    return columns


def _trino_type_to_postgres(column: str, trino_type: str) -> tuple[str, str]:
    """Map a Trino column type to a Postgres type and select expression."""

    column_ref = _quote_trino_identifier(column, was_quoted=True)
    normalized = trino_type.lower()
    base = normalized.split("(")[0].strip()
    if "timestamp" in normalized and "time zone" in normalized:
        return "timestamptz", column_ref
    if base == "timestamptz":
        return "timestamptz", column_ref
    if base in {"varchar", "char", "string"}:
        return "text", column_ref
    if base in {"bigint"}:
        return "bigint", column_ref
    if base in {"integer", "int"}:
        return "integer", column_ref
    if base in {"smallint"}:
        return "smallint", column_ref
    if base in {"double", "double precision"}:
        return "double precision", column_ref
    if base in {"real"}:
        return "real", column_ref
    if base in {"boolean"}:
        return "boolean", column_ref
    if base in {"date"}:
        return "date", column_ref
    if base == "timestamp":
        return "timestamp", column_ref
    if base.startswith("decimal") or base == "numeric":
        return "numeric", column_ref
    if base in {"json", "array", "map", "row"}:
        return "jsonb", f"CAST({column_ref} AS JSON)"
    return "text", f"CAST({column_ref} AS VARCHAR)"


def _resolve_asset_key(context: Any, data_source: str) -> str | None:
    """Resolve the Dagster asset key for publish events."""

    asset_key = getattr(context, "asset_key", None)
    if asset_key is None:
        return f"publish_{data_source}_marts"
    if hasattr(asset_key, "path") and asset_key.path:
        return "/".join(str(part) for part in asset_key.path)
    return str(asset_key)

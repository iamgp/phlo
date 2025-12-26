from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from psycopg2 import sql
from psycopg2.extras import execute_values

from phlo.config import get_settings
from phlo.hooks import PublishEvent, get_hook_bus


@dataclass(frozen=True)
class TablePublishStats:
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
    settings = get_settings()
    schema = target_schema or settings.postgres_mart_schema
    hook_bus = get_hook_bus()
    asset_key = _resolve_asset_key(context, data_source)

    hook_bus.emit(
        PublishEvent(
            event_type="publish.start",
            asset_key=asset_key,
            target_system="postgres",
            tables=tables_to_publish,
            status="started",
            tags={"source": data_source, "target": "postgres"},
        )
    )

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
        hook_bus.emit(
            PublishEvent(
                event_type="publish.end",
                asset_key=asset_key,
                target_system="postgres",
                tables=tables_to_publish,
                status="success",
                metrics={
                    "tables": {
                        name: {"row_count": s.row_count, "column_count": s.column_count}
                        for name, s in stats.items()
                    }
                },
                tags={"source": data_source, "target": "postgres"},
            )
        )
        return stats
    except Exception as exc:
        hook_bus.emit(
            PublishEvent(
                event_type="publish.end",
                asset_key=asset_key,
                target_system="postgres",
                tables=tables_to_publish,
                status="failure",
                error=str(exc),
                tags={"source": data_source, "target": "postgres"},
            )
        )
        raise


def _ensure_schema(postgres: Any, schema: str) -> None:
    with postgres.cursor() as cursor:
        cursor.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema)))
    postgres.commit()


def _copy_table(
    *,
    trino: Any,
    postgres: Any,
    source_table: str,
    target_schema: str,
    target_table: str,
    batch_size: int,
) -> tuple[int, int]:
    columns = _describe_trino_table(trino, source_table)
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
        trino_cursor.execute(f"SELECT {', '.join(select_exprs)} FROM {source_table}")
        with postgres.cursor() as pg_cursor:
            while True:
                rows = trino_cursor.fetchmany(batch_size)
                if not rows:
                    break
                execute_values(pg_cursor, insert_query, rows, page_size=batch_size)
                row_count += len(rows)
    postgres.commit()

    return row_count, len(columns)


def _describe_trino_table(trino: Any, source_table: str) -> list[tuple[str, str, str]]:
    with trino.cursor() as cursor:
        cursor.execute(f"DESCRIBE {source_table}")
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
    normalized = trino_type.lower()
    base = normalized.split("(")[0].strip()
    if base in {"varchar", "char", "string"}:
        return "text", column
    if base in {"bigint"}:
        return "bigint", column
    if base in {"integer", "int"}:
        return "integer", column
    if base in {"smallint"}:
        return "smallint", column
    if base in {"double", "double precision"}:
        return "double precision", column
    if base in {"real"}:
        return "real", column
    if base in {"boolean"}:
        return "boolean", column
    if base in {"date"}:
        return "date", column
    if base == "timestamp":
        return "timestamp", column
    if "timestamp" in base and "time zone" in base:
        return "timestamptz", column
    if base.startswith("decimal") or base == "numeric":
        return "numeric", column
    if base in {"json", "array", "map", "row"}:
        return "jsonb", f"CAST({column} AS JSON)"
    return "text", f"CAST({column} AS VARCHAR)"


def _resolve_asset_key(context: Any, data_source: str) -> str | None:
    asset_key = getattr(context, "asset_key", None)
    if asset_key is None:
        return f"publish_{data_source}_marts"
    if hasattr(asset_key, "path") and asset_key.path:
        return "/".join(str(part) for part in asset_key.path)
    return str(asset_key)

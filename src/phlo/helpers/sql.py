"""Small SQL construction and safety helpers."""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import Any

from phlo.exceptions import PhloConfigError
from phlo.helpers.partitions import PartitionScope

_DANGEROUS_SQL = re.compile(
    r"\b(insert|update|delete|drop|create|alter|truncate|merge|grant|revoke)\b",
    re.IGNORECASE,
)
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def quote_identifier(identifier: str, *, quote_char: str = '"') -> str:
    """Quote one SQL identifier part."""
    escaped = identifier.replace(quote_char, quote_char * 2)
    return f"{quote_char}{escaped}{quote_char}"


def table_ref_sql(*parts: str, quote_parts: bool = False) -> str:
    """Render a table reference from catalog/schema/table parts."""
    clean = [part for part in parts if part]
    if quote_parts:
        return ".".join(quote_identifier(part) for part in clean)
    for part in clean:
        if not all(_IDENTIFIER.match(segment) for segment in part.split(".")):
            raise PhloConfigError(
                message=f"Unsafe SQL identifier: {part}",
                suggestions=["Pass quote_parts=True or use simple identifier names."],
            )
    return ".".join(clean)


def literal(value: Any) -> str:
    """Render a conservative SQL literal for helper-generated predicates."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int | float):
        return str(value)
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def where_and(*predicates: str | None) -> str:
    """Join optional predicates into a WHERE clause body."""
    return " AND ".join(f"({predicate})" for predicate in predicates if predicate)


def limit_sql(sql: str, *, limit: int | None) -> str:
    """Apply a LIMIT clause when one is not already present."""
    stripped = sql.strip().rstrip(";")
    if limit is None:
        return stripped
    if re.search(r"\blimit\s+\d+\s*$", stripped, flags=re.IGNORECASE):
        return stripped
    return f"{stripped} LIMIT {int(limit)}"


def render_partition_predicate(scope: PartitionScope) -> str | None:
    """Render a SQL predicate for a partition scope."""
    if scope.full_table:
        return None
    column = table_ref_sql(scope.partition_column)
    if scope.partition_key:
        return f"{column} = {literal(scope.partition_key)}"
    predicates: list[str] = []
    if scope.start:
        predicates.append(f"{column} >= {literal(scope.start)}")
    if scope.end:
        predicates.append(f"{column} <= {literal(scope.end)}")
    if scope.rolling_window_days:
        start = (datetime.now(UTC).date() - timedelta(days=scope.rolling_window_days)).isoformat()
        predicates.append(f"{column} >= {literal(start)}")
    return where_and(*predicates) or None


def partition_where_clause(scope: PartitionScope) -> str:
    """Render a full WHERE clause for a partition scope."""
    predicate = render_partition_predicate(scope)
    return f"WHERE {predicate}" if predicate else ""


def apply_where(sql: str, *predicates: str | None) -> str:
    """Append helper predicates to a SELECT query."""
    predicate = where_and(*predicates)
    stripped = sql.strip().rstrip(";")
    if not predicate:
        return stripped
    keyword = " AND " if re.search(r"\bwhere\b", stripped, re.IGNORECASE) else " WHERE "
    return f"{stripped}{keyword}{predicate}"


def validate_read_only_sql(sql: str) -> str:
    """Validate that SQL is a single read-only statement."""
    stripped = sql.strip().rstrip(";")
    if not stripped:
        raise PhloConfigError(message="SQL query cannot be empty")
    if ";" in stripped:
        raise PhloConfigError(
            message="SQL query must contain a single statement",
            suggestions=["Remove additional statements and rerun the query."],
        )
    if _DANGEROUS_SQL.search(stripped):
        raise PhloConfigError(
            message="SQL query must be read-only",
            suggestions=["Use SELECT/SHOW/DESCRIBE queries in helper read paths."],
        )
    return stripped


def select_columns(table: str, columns: Iterable[str] = ("*",), *, limit: int | None = None) -> str:
    """Build a simple read-only SELECT statement."""
    rendered_columns = ", ".join(columns)
    return limit_sql(f"SELECT {rendered_columns} FROM {table_ref_sql(table)}", limit=limit)

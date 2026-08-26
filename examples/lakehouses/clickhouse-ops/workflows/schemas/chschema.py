"""Dual-view table schemas for the ClickHouse table store.

The pinned phlo-dlt/phlo-clickhouse pair consumes ``table_schema`` twice with
incompatible expectations: ``ensure_table`` renders DDL from ``fields[].type``
while parquet coercion casts through ``fields[].field_type`` (pyarrow). No
single shipped schema class provides both, so each field below carries the two
views side by side. When phlo-clickhouse grows a
``schema_from_validation_schema`` converter, this module collapses into plain
``validation_schema=`` usage.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pyarrow as pa

STR = pa.string()
INT = pa.int64()
TS = pa.timestamp("us", tz="UTC")


@dataclass(frozen=True)
class ChField:
    """One column: ClickHouse DDL type plus pyarrow coercion type."""

    name: str
    type: str
    field_type: object = field(default=STR)


@dataclass(frozen=True)
class ChSchema:
    """Iterable of :class:`ChField` satisfying both schema consumers."""

    fields: list[ChField]


PLATFORM_EVENTS = ChSchema(
    fields=[
        ChField("event_id", "String", STR),
        ChField("tenant_id", "String", STR),
        ChField("event_type", "String", STR),
        ChField("occurred_at", "DateTime64(6)", TS),
        ChField("occurred_hour", "DateTime64(6)", TS),
        ChField("latency_ms", "Int64", INT),
    ]
)

ACCESS_LOGS = ChSchema(
    fields=[
        ChField("request_id", "String", STR),
        ChField("tenant_id", "String", STR),
        ChField("path", "String", STR),
        ChField("status_code", "Int64", INT),
        ChField("duration_ms", "Int64", INT),
        ChField("occurred_at", "DateTime64(6)", TS),
    ]
)

TENANTS = ChSchema(
    fields=[
        ChField("tenant_id", "String", STR),
        ChField("tenant_name", "String", STR),
        ChField("tier", "String", STR),
        ChField("plan", "String", STR),
    ]
)

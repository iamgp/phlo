"""ClickHouse publish target for mart publishing."""

from __future__ import annotations

from dataclasses import dataclass, field

from phlo_clickhouse.resource import ClickHouseResource


@dataclass
class ClickHousePublishTarget:
    """Publish target backed by ClickHouse."""

    resource: ClickHouseResource = field(default_factory=ClickHouseResource)
    target_system: str = "clickhouse"
    default_schema: str = "marts"

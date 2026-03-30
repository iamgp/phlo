"""ClickHouse publish target for mart publishing.

This module defines the publish target implementation for ClickHouse,
enabling data marts to be published to ClickHouse tables.

Example:
    Creating a ClickHouse publish target:

    >>> from phlo_clickhouse.publish_target import ClickHousePublishTarget
    >>> target = ClickHousePublishTarget()
    >>> target.target_system
    'clickhouse'

"""

from __future__ import annotations

from dataclasses import dataclass, field

from phlo_clickhouse.resource import ClickHouseResource


@dataclass
class ClickHousePublishTarget:
    """Publish target backed by ClickHouse.

    Provides configuration for publishing data marts to ClickHouse tables.
    Uses a ClickHouseResource for database connections and operations.

    Attributes:
        resource: ClickHouseResource instance for database operations.
            Defaults to a new ClickHouseResource instance.
        target_system: Target system identifier. Always "clickhouse".
        default_schema: Default database/schema for publishing.
            Defaults to "marts".

    Example:
        >>> target = ClickHousePublishTarget()
        >>> target.target_system
        'clickhouse'
        >>> target.default_schema
        'marts'

    """

    resource: ClickHouseResource = field(default_factory=ClickHouseResource)
    target_system: str = "clickhouse"
    default_schema: str = "marts"

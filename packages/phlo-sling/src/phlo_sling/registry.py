"""Registry for Sling replication table configurations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from phlo_sling.settings import get_settings


@dataclass(frozen=True)
class ReplicationConfig:
    """Configuration describing a registered Sling replication stream.

    Attributes:
        stream_name: Source stream identifier (e.g., 'public.users').
        table_name: Target table-store table name.
        source_conn: Sling source connection name or URL.
        target_conn: Sling target connection name or URL.
        mode: Replication mode (full-refresh, incremental, snapshot, backfill).
        primary_key: Column(s) used as primary key for merge operations.
        update_key: Column used as cursor for incremental replication.
        group_name: Dagster/asset group name for generated assets.
        object: Target object path (for file-based targets).
        select: Column selection list. Empty means all columns.
        where: SQL WHERE clause for source filtering.
        source_options: Additional Sling source options.
        target_options: Additional Sling target options.
    """

    stream_name: str
    table_name: str
    source_conn: str
    target_conn: str | None = None
    mode: str = "incremental"
    primary_key: list[str] = field(default_factory=list)
    update_key: str | None = None
    group_name: str = "sling"
    object: str | None = None
    select: list[str] = field(default_factory=list)
    where: str | None = None
    source_options: dict[str, Any] = field(default_factory=dict)
    target_options: dict[str, Any] = field(default_factory=dict)

    @property
    def full_table_name(self) -> str:
        """Return fully qualified table name with default namespace.

        Returns:
            Namespace-prefixed table name.
        """
        return f"{get_settings().sling_default_namespace}.{self.table_name}"

    @property
    def asset_key(self) -> str:
        """Return the Phlo asset key for this replication stream."""
        return f"sling_{self.table_name}"

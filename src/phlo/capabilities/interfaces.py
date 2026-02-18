"""Runtime capability interfaces used by capability providers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class TableStore(Protocol):
    """Protocol for table-store providers used by ingestion components."""

    def ensure_table(
        self,
        *,
        table_name: str,
        schema: Any,
        partition_spec: Any = None,
        override_ref: str | None = None,
    ) -> Any:
        """Ensure a destination table exists."""

    def append_parquet(
        self,
        *,
        table_name: str,
        data_path: str | Path,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Append staged parquet data to a destination table."""

    def merge_parquet(
        self,
        *,
        table_name: str,
        data_path: str | Path,
        unique_key: str,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Merge staged parquet data into a destination table."""

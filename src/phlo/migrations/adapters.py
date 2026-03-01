"""Source adapters for data migration reads."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterator, Protocol

from phlo.capabilities import get_capability_registry
from phlo.migrations.specs import MigrationSource


class SourceAdapter(Protocol):
    """Protocol for migration source readers."""

    @property
    def source_type(self) -> str:
        """Identifier for this adapter (for example csv, postgres)."""

    def validate_config(self, source: MigrationSource) -> list[str]:
        """Validate source configuration and return errors."""

    def read_chunks(
        self,
        source: MigrationSource,
        *,
        chunk_size: int = 50_000,
    ) -> Iterator[list[dict[str, Any]]]:
        """Yield row chunks from the source."""

    def estimate_row_count(self, source: MigrationSource) -> int | None:
        """Estimate source row count if possible."""


class CsvSourceAdapter:
    """CSV source adapter implementation."""

    @property
    def source_type(self) -> str:
        return "csv"

    def validate_config(self, source: MigrationSource) -> list[str]:
        errors: list[str] = []
        if not source.path:
            errors.append("source.path is required for csv source")
            return errors
        csv_path = Path(source.path)
        if not csv_path.exists():
            errors.append(f"CSV file not found: {csv_path}")
        if source.query:
            errors.append("source.query is not supported for csv source")
        if source.table:
            errors.append("source.table is not supported for csv source")
        return errors

    def read_chunks(
        self,
        source: MigrationSource,
        *,
        chunk_size: int = 50_000,
    ) -> Iterator[list[dict[str, Any]]]:
        if not source.path:
            raise ValueError("source.path is required for csv source")

        csv_path = Path(source.path)
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            buffer: list[dict[str, Any]] = []
            for row in reader:
                buffer.append(dict(row))
                if len(buffer) >= chunk_size:
                    yield buffer
                    buffer = []
            if buffer:
                yield buffer

    def estimate_row_count(self, source: MigrationSource) -> int | None:
        if not source.path:
            return None
        csv_path = Path(source.path)
        if not csv_path.exists():
            return None

        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            line_count = sum(1 for _ in handle)
        return max(0, line_count - 1)


_BUILTIN_ADAPTERS: dict[str, SourceAdapter] = {
    "csv": CsvSourceAdapter(),
}


def resolve_source_adapter(source_type: str) -> SourceAdapter | None:
    """Resolve a source adapter from built-ins and registered capabilities."""
    adapter = _BUILTIN_ADAPTERS.get(source_type)
    if adapter is not None:
        return adapter

    for spec in get_capability_registry().list_data_migration_sources():
        if spec.name != source_type:
            continue
        provider = spec.provider
        return provider if _is_source_adapter(provider) else None

    return None


def list_source_adapter_types() -> list[str]:
    """List all known source adapter types."""
    adapter_types = set(_BUILTIN_ADAPTERS.keys())
    for spec in get_capability_registry().list_data_migration_sources():
        adapter_types.add(spec.name)
    return sorted(adapter_types)


def _is_source_adapter(provider: Any) -> bool:
    return (
        hasattr(provider, "source_type")
        and hasattr(provider, "validate_config")
        and hasattr(provider, "read_chunks")
        and hasattr(provider, "estimate_row_count")
    )

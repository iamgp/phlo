"""Regression tests for migration executor edge cases."""

from __future__ import annotations

import types
from pathlib import Path

import pytest

from phlo.migrations import executor as migration_executor
from phlo.migrations.executor import (
    MigrationExecutionError,
    MigrationExecutor,
    _stage_chunk_parquet,
    _write_chunk_to_table_store,
)
from phlo.migrations.specs import (
    MigrationDestination,
    MigrationOptions,
    MigrationSource,
    MigrationSpec,
)


class _FakeAdapter:
    def validate_config(self, source: MigrationSource) -> list[str]:
        return []

    def read_chunks(self, source: MigrationSource, *, chunk_size: int = 50_000):
        yield []

    def estimate_row_count(self, source: MigrationSource) -> int | None:
        return 0


class _FakeRegistry:
    def list_table_stores(self) -> list[object]:
        return []


def _spec(*, write_mode: str = "append", dry_run: bool = False) -> MigrationSpec:
    return MigrationSpec(
        name="demo",
        version="1.0",
        description="demo",
        source=MigrationSource(type="csv", path="input.csv"),
        destination=MigrationDestination(table="warehouse.demo", write_mode=write_mode),
        options=MigrationOptions(dry_run=dry_run),
    )


def test_validate_respects_dry_run_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dry-run override bypasses table-store requirement during validation."""
    monkeypatch.setattr(migration_executor, "discover_capabilities", lambda: None)
    monkeypatch.setattr(migration_executor, "resolve_source_adapter", lambda _: _FakeAdapter())
    monkeypatch.setattr(migration_executor, "get_capability_registry", lambda: _FakeRegistry())

    executor = MigrationExecutor()
    errors_without_override = executor.validate(_spec(dry_run=False))
    assert any("No table store registered" in error for error in errors_without_override)

    errors_with_override = executor.validate(_spec(dry_run=False), dry_run_override=True)
    assert errors_with_override == []


def test_overwrite_mode_requires_overwrite_support(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Overwrite write mode fails fast when provider lacks overwrite support."""
    staged_path = tmp_path / "chunk.parquet"
    staged_path.write_text("stub", encoding="utf-8")
    monkeypatch.setattr(migration_executor, "_stage_chunk_parquet", lambda _: staged_path)

    class AppendOnlyStore:
        def __init__(self) -> None:
            self.append_calls = 0

        def append_parquet(self, *, table_name: str, data_path: Path) -> None:
            self.append_calls += 1

    store = AppendOnlyStore()
    with pytest.raises(MigrationExecutionError, match="requires table store support"):
        _write_chunk_to_table_store(
            table_store=store,
            table_name="warehouse.demo",
            write_mode="overwrite",
            unique_key=None,
            chunk=[{"id": "1"}],
            first_chunk=True,
        )

    assert store.append_calls == 0
    assert not staged_path.exists()


def test_stage_chunk_parquet_cleans_temp_file_on_write_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Temporary parquet path is removed when write_table fails."""
    staged_path = tmp_path / "broken.parquet"

    class _TmpFile:
        def __init__(self, name: str) -> None:
            self.name = name

    class _TmpContext:
        def __enter__(self) -> _TmpFile:
            staged_path.write_text("tmp", encoding="utf-8")
            return _TmpFile(str(staged_path))

        def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
            return None

    monkeypatch.setattr(
        migration_executor.tempfile,
        "NamedTemporaryFile",
        lambda **_: _TmpContext(),
    )

    fake_pa = types.ModuleType("pyarrow")

    class _FakeTable:
        @staticmethod
        def from_pylist(rows):  # type: ignore[no-untyped-def]
            return rows

    fake_pa.Table = _FakeTable  # type: ignore[attr-defined]
    fake_pq = types.ModuleType("pyarrow.parquet")

    def _raise_write_error(table, path):  # type: ignore[no-untyped-def]
        raise RuntimeError("write failed")

    fake_pq.write_table = _raise_write_error  # type: ignore[attr-defined]

    monkeypatch.setitem(__import__("sys").modules, "pyarrow", fake_pa)
    monkeypatch.setitem(__import__("sys").modules, "pyarrow.parquet", fake_pq)

    with pytest.raises(RuntimeError, match="write failed"):
        _stage_chunk_parquet([{"id": "1"}])

    assert not staged_path.exists()

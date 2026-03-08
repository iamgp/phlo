"""Tests for multi-file DLT staging and write helpers."""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pyarrow as pa
from pyiceberg.schema import Schema
from pyiceberg.types import NestedField, StringType

from phlo_dlt.dlt_helpers import merge_to_table_store, stage_to_parquet
from phlo_dlt.registry import TableConfig


def test_stage_to_parquet_collects_all_files_across_load_packages(tmp_path) -> None:
    context = SimpleNamespace(
        log=SimpleNamespace(
            info=lambda *_args, **_kwargs: None,
            debug=lambda *_args, **_kwargs: None,
        )
    )
    relative_file = tmp_path / "staging" / "part-1.parquet"
    absolute_file = tmp_path / "part-2.parquet"
    relative_file.parent.mkdir(parents=True, exist_ok=True)
    relative_file.write_text("", encoding="utf-8")
    absolute_file.write_text("", encoding="utf-8")
    load_info = SimpleNamespace(
        load_packages=[
            SimpleNamespace(
                jobs={"completed_jobs": [SimpleNamespace(file_path="staging/part-1.parquet")]}
            ),
            SimpleNamespace(
                jobs={"completed_jobs": [SimpleNamespace(file_path=str(absolute_file))]}
            ),
        ]
    )
    pipeline = SimpleNamespace(
        pipeline_name="test_pipeline",
        run=lambda _source, loader_file_format="parquet": load_info,
    )

    parquet_paths, _elapsed = stage_to_parquet(context, pipeline, object(), tmp_path)

    assert parquet_paths == [relative_file.resolve(), absolute_file]


def test_merge_to_table_store_appends_all_files(tmp_path) -> None:
    left_path = tmp_path / "left.parquet"
    right_path = tmp_path / "right.parquet"
    pd.DataFrame([{"name": "alpha"}]).to_parquet(left_path)
    pd.DataFrame([{"name": "beta"}]).to_parquet(right_path)

    append_calls: list[str] = []

    class TableStoreStub:
        def ensure_table(self, **_kwargs):
            return None

        def append_parquet(
            self, *, table_name: str, data_path: str, override_ref: str | None = None
        ):
            append_calls.append(data_path)
            return {"rows_inserted": 1, "rows_deleted": 0}

    context = SimpleNamespace(log=SimpleNamespace(info=lambda *_args, **_kwargs: None))
    metrics = merge_to_table_store(
        context=context,
        table_store=TableStoreStub(),
        table_config=TableConfig(
            table_name="entries",
            table_schema=Schema(
                NestedField(field_id=1, name="name", field_type=StringType(), required=False)
            ),
            validation_schema=None,
            unique_key="name",
            group_name="raw",
        ),
        parquet_paths=[left_path, right_path],
        branch_name="main",
        merge_strategy="append",
    )

    assert metrics == {"rows_inserted": 2, "rows_deleted": 0}
    assert len(append_calls) == 2


def test_merge_to_table_store_supports_pyarrow_table_schema(tmp_path) -> None:
    parquet_path = tmp_path / "pokemon.parquet"
    pd.DataFrame([{"pokemon_id": 1, "name": "bulbasaur"}]).to_parquet(parquet_path)

    append_calls: list[str] = []

    class TableStoreStub:
        def ensure_table(self, **_kwargs):
            return None

        def append_parquet(
            self, *, table_name: str, data_path: str, override_ref: str | None = None
        ):
            append_calls.append(data_path)
            return {"rows_inserted": 1, "rows_deleted": 0}

    context = SimpleNamespace(log=SimpleNamespace(info=lambda *_args, **_kwargs: None))
    metrics = merge_to_table_store(
        context=context,
        table_store=TableStoreStub(),
        table_config=TableConfig(
            table_name="pokemon_species",
            table_schema=pa.schema(
                [
                    pa.field("pokemon_id", pa.int64()),
                    pa.field("name", pa.string()),
                ]
            ),
            validation_schema=None,
            unique_key="pokemon_id",
            group_name="pokemon",
        ),
        parquet_paths=[parquet_path],
        branch_name="main",
        merge_strategy="append",
    )

    assert metrics == {"rows_inserted": 1, "rows_deleted": 0}
    assert len(append_calls) == 1

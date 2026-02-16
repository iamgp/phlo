"""Unit tests for dbt transform translator.

These tests do not require a dbt manifest or running services.
"""

import subprocess
from pathlib import Path

import pytest
from phlo.logging import get_logger
from phlo_dbt.transformer import DbtTransformer
from phlo_dbt.translator import DbtSpecTranslator


def test_custom_dbt_translator_asset_key_model() -> None:
    translator = DbtSpecTranslator()
    asset_key = translator.get_asset_key(
        {"name": "stg_nightscout_entries", "resource_type": "model"}
    )
    assert asset_key == "stg_nightscout_entries"


def test_custom_dbt_translator_asset_key_source_dagster_assets_maps_to_dlt() -> None:
    translator = DbtSpecTranslator()
    asset_key = translator.get_asset_key(
        {"resource_type": "source", "source_name": "dagster_assets", "name": "entries"}
    )
    assert asset_key == "dlt_entries"


@pytest.mark.parametrize(
    ("props", "expected"),
    [
        ({"name": "anything", "fqn": ["project", "bronze", "stg_entries"]}, "bronze"),
        ({"name": "anything", "fqn": ["project", "staging", "stg_entries"]}, "silver"),
        ({"name": "anything", "path": "models/silver/stg_entries.sql"}, "silver"),
        ({"name": "anything", "path": "models/marts/mrt_patient_summary.sql"}, "marts"),
    ],
)
def test_custom_dbt_translator_group_name_prefers_folder(props: dict, expected: str) -> None:
    translator = DbtSpecTranslator()
    assert translator.get_group_name(props) == expected


@pytest.mark.parametrize(
    ("model_name", "expected"),
    [
        ("stg_nightscout_entries", "silver"),
        ("dim_patients", "gold"),
        ("fct_glucose_readings", "gold"),
        ("mrt_patient_summary", "marts"),
        ("unknown_model", "transform"),
    ],
)
def test_custom_dbt_translator_group_name_fallbacks(model_name: str, expected: str) -> None:
    translator = DbtSpecTranslator()
    assert translator.get_group_name({"name": model_name}) == expected


def test_custom_dbt_translator_description_does_not_embed_compiled_sql_by_default() -> None:
    translator = DbtSpecTranslator()
    description = translator.get_description(
        {"name": "model_x", "description": "Doc", "compiled_code": "select 1 as x"}
    )
    assert "select 1 as x" not in description


def test_custom_dbt_translator_metadata_compiled_sql_is_capped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PHLO_DBT_COMPILED_SQL_MAX_BYTES", "64")
    translator = DbtSpecTranslator()

    compiled_code = "select '" + ("x" * 10_000) + "' as big"
    metadata = translator.get_metadata({"name": "model_x", "compiled_code": compiled_code})

    assert "phlo/compiled_sql" in metadata
    assert metadata["phlo/compiled_sql_truncated"] is True
    assert "TRUNCATED compiled SQL" in metadata["phlo/compiled_sql"]


def test_run_transform_skip_build_returns_success(tmp_path: Path) -> None:
    transformer = DbtTransformer(
        context=None,
        logger=get_logger("test_dbt_transformer_skip_build"),
        project_dir=tmp_path,
        profiles_dir=tmp_path,
    )
    run_calls: list[list[str]] = []

    def fake_run_command(args: list[str], env: dict[str, str] | None = None):
        run_calls.append(args)
        return subprocess.CompletedProcess(
            args=["dbt"] + args,
            returncode=0,
            stdout="PASS=1 WARN=0 ERROR=0 SKIP=0 TOTAL=1",
            stderr="",
        )

    transformer._run_command = fake_run_command  # type: ignore[method-assign]

    result = transformer.run_transform(parameters={"skip_build": True, "generate_docs": False})

    assert result.status == "success"
    assert result.models_built == 0
    assert result.models_failed == 0
    assert result.tests_passed == 0
    assert result.tests_failed == 0
    assert result.metadata["dbt_output"] == ""
    assert run_calls == []

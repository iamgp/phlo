"""Unit tests for dbt transform translator.

These tests do not require a dbt manifest or running services.
"""

import pytest
from phlo_dbt.translator import DbtSpecTranslator


def test_custom_dbt_translator_asset_key_model() -> None:
    translator = DbtSpecTranslator()
    asset_key = translator.get_asset_key({"name": "stg_nightscout_entries", "resource_type": "model"})
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

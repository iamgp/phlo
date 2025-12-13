from __future__ import annotations

from pathlib import Path

import pytest

from phlo.cli.scaffold import create_ingestion_workflow, parse_field_specs


def test_parse_field_specs_validates_and_dedupes() -> None:
    specs = parse_field_specs(["User ID:str!", "created_at:datetime", "user_id:int"])
    assert [s.name for s in specs] == ["user_id", "created_at"]
    assert specs[0].nullable is False


def test_scaffold_generates_no_todos_and_is_syntax_valid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "workflows" / "schemas").mkdir(parents=True)
    (tmp_path / "workflows" / "ingestion").mkdir(parents=True)

    created = create_ingestion_workflow(
        domain="Weather",
        table_name="observations",
        unique_key="id",
        cron="0 */1 * * *",
        api_base_url="https://api.example.com",
        fields=["temperature:float", "created_at:datetime?"],
    )

    for rel_path in created:
        contents = (tmp_path / rel_path).read_text()
        assert "TODO" not in contents
        compile(contents, rel_path, "exec")

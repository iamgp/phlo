from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from phlo_dlt.scaffold import (
    _resolve_schema_base_import,
    create_ingestion_workflow,
    parse_field_specs,
)


def test_parse_field_specs_validates_and_dedupes() -> None:
    """Normalizes field specs and keeps first occurrence for duplicate names."""
    specs = parse_field_specs(["User ID:str!", "created_at:datetime", "user_id:int"])
    assert [s.name for s in specs] == ["user_id", "created_at"]
    assert specs[0].nullable is False


def test_scaffold_schema_base_comes_from_quality_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keeps generated schema imports behind the quality-provider capability."""
    import phlo.plugins.discovery as discovery

    class FakeQualityProvider:
        def get_schema_base_import(self) -> tuple[str, str]:
            return ("example_quality.schemas", "ExampleSchema")

    monkeypatch.setattr(discovery, "discover_plugins", lambda: None, raising=False)
    monkeypatch.setattr(
        discovery,
        "get_quality_provider",
        lambda name: FakeQualityProvider() if name == "pandera" else None,
        raising=False,
    )

    assert _resolve_schema_base_import() == ("example_quality.schemas", "ExampleSchema")


def test_phlo_dlt_does_not_depend_on_pandera_packages() -> None:
    """Quality providers own Pandera dependencies; phlo-dlt only consumes capability metadata."""
    pyproject = tomllib.loads(Path("packages/phlo-dlt/pyproject.toml").read_text())
    dependencies = pyproject["project"]["dependencies"]

    assert "pandera" not in {dependency.split(">=", 1)[0] for dependency in dependencies}
    assert "phlo-pandera" not in {dependency.split(">=", 1)[0] for dependency in dependencies}


def test_scaffold_generates_no_todos_and_is_syntax_valid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Generates scaffold files without placeholders and with valid Python syntax.

    Args:
        tmp_path: Temporary filesystem root for generated files.
        monkeypatch: Pytest fixture for changing current working directory.
    """
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

    asset_path = next(
        (tmp_path / rel_path for rel_path in created if "workflows/ingestion/" in rel_path),
        None,
    )
    assert asset_path is not None
    asset_contents = asset_path.read_text()
    assert "return rest_api(" in asset_contents
    assert "client={" in asset_contents
    assert "resources=[" in asset_contents


def test_scaffold_uses_unique_key_field_type_when_declared(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Lets API schemas declare integer primary keys such as Fake Store product ids."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "workflows" / "schemas").mkdir(parents=True)
    (tmp_path / "workflows" / "ingestion").mkdir(parents=True)

    created = create_ingestion_workflow(
        domain="commerce",
        table_name="products",
        unique_key="id",
        api_base_url="https://fakestoreapi.com",
        fields=["id:int", "title:str", "price:float"],
    )

    schema_path = tmp_path / "workflows" / "schemas" / "commerce.py"
    test_path = next(tmp_path / path for path in created if path.startswith("tests/"))

    assert "from phlo_pandera.schemas import PhloSchema" in schema_path.read_text()
    assert "class RawProducts(PhloSchema):" in schema_path.read_text()
    assert 'id: Series[int] = pa.Field(description="Unique key", nullable=False)' in (
        schema_path.read_text()
    )
    assert '"id": 1' in test_path.read_text()

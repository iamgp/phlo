import ast
from pathlib import Path

import pytest
from click.testing import CliRunner

from phlo.cli.main import cli
from phlo.cli.templates.registry import get_template, list_templates


def test_registry_contains_existing_templates() -> None:
    names = [template.metadata.name for template in list_templates()]

    assert "minimal" in names
    assert "basic" in names


def test_get_template_rejects_unknown_template() -> None:
    with pytest.raises(KeyError, match="unknown-template"):
        get_template("unknown-template")


def test_minimal_template_generates_project(tmp_path) -> None:
    project_dir = tmp_path / "demo"
    result = CliRunner().invoke(cli, ["init", str(project_dir), "--template", "minimal"])

    assert result.exit_code == 0, result.output
    assert (project_dir / "phlo.yaml").exists()
    assert (project_dir / "workflows" / "__init__.py").exists()


def test_basic_template_generates_dbt_project(tmp_path) -> None:
    project_dir = tmp_path / "demo"
    result = CliRunner().invoke(cli, ["init", str(project_dir), "--template", "basic"])

    assert result.exit_code == 0, result.output
    assert (project_dir / "workflows" / "transforms" / "dbt" / "dbt_project.yml").exists()


def test_init_list_templates_outputs_metadata() -> None:
    result = CliRunner().invoke(cli, ["init", "--list-templates"])

    assert result.exit_code == 0
    assert "minimal" in result.output
    assert "basic" in result.output
    assert "dbt-ready Phlo project" in result.output


def _assert_python_files_parse(project_dir: Path) -> None:
    for path in project_dir.rglob("*.py"):
        ast.parse(path.read_text(), filename=str(path))


def test_csv_batch_template_generates_runnable_files(tmp_path) -> None:
    project_dir = tmp_path / "csv-demo"
    result = CliRunner().invoke(cli, ["init", str(project_dir), "--template", "csv-batch"])

    assert result.exit_code == 0, result.output
    assert (project_dir / "data" / "events.csv").exists()
    assert (project_dir / "workflows" / "ingestion" / "csv" / "events.py").exists()
    assert (project_dir / "workflows" / "schemas" / "csv.py").exists()
    _assert_python_files_parse(project_dir)


def test_api_ingestion_template_generates_runnable_files(tmp_path) -> None:
    project_dir = tmp_path / "api-demo"
    result = CliRunner().invoke(cli, ["init", str(project_dir), "--template", "api-ingestion"])

    assert result.exit_code == 0, result.output
    assert (project_dir / "workflows" / "ingestion" / "api" / "events.py").exists()
    assert (project_dir / "workflows" / "schemas" / "api.py").exists()
    _assert_python_files_parse(project_dir)

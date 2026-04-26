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

import ast
import importlib
import subprocess
import sys
import tomllib
from collections.abc import Iterator
from contextlib import contextmanager
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


@contextmanager
def _generated_project_import_path(project_dir: Path) -> Iterator[None]:
    sys.path.insert(0, str(project_dir))
    for module_name in list(sys.modules):
        if module_name == "workflows" or module_name.startswith("workflows."):
            sys.modules.pop(module_name)
    try:
        yield
    finally:
        sys.path.remove(str(project_dir))
        for module_name in list(sys.modules):
            if module_name == "workflows" or module_name.startswith("workflows."):
                sys.modules.pop(module_name)


def _assert_generated_module_imports(project_dir: Path, module_name: str) -> None:
    with _generated_project_import_path(project_dir):
        importlib.import_module(module_name)


def _project_dependencies(project_dir: Path) -> list[str]:
    pyproject = tomllib.loads((project_dir / "pyproject.toml").read_text())
    return pyproject["project"]["dependencies"]


def test_csv_batch_template_generates_runnable_files(tmp_path) -> None:
    project_dir = tmp_path / "csv-demo"
    result = CliRunner().invoke(cli, ["init", str(project_dir), "--template", "csv-batch"])

    assert result.exit_code == 0, result.output
    assert (project_dir / "data" / "events.csv").exists()
    assert (project_dir / "workflows" / "ingestion" / "csv" / "events.py").exists()
    assert (project_dir / "workflows" / "schemas" / "csv.py").exists()
    _assert_python_files_parse(project_dir)
    _assert_generated_module_imports(project_dir, "workflows.ingestion.csv.events")


def test_csv_batch_template_prints_metadata_next_steps(tmp_path) -> None:
    project_dir = tmp_path / "csv-demo"
    result = CliRunner().invoke(cli, ["init", str(project_dir), "--template", "csv-batch"])

    assert result.exit_code == 0, result.output
    assert "phlo test" in result.output
    assert "phlo materialize dlt_events" in result.output
    assert "phlo workflow check" not in result.output
    assert "phlo dev" not in result.output


@pytest.mark.parametrize(
    ("template_name", "expected_dependencies"),
    [
        ("minimal", ["phlo"]),
        ("basic", ["phlo", "phlo-dbt"]),
        ("csv-batch", ["phlo", "phlo-dlt", "phlo-pandera"]),
        ("api-ingestion", ["phlo", "phlo-dlt", "phlo-pandera"]),
        ("observability-demo", ["phlo", "phlo-dlt", "phlo-pandera", "phlo-otel"]),
    ],
)
def test_template_writes_required_packages_to_pyproject(
    tmp_path, template_name: str, expected_dependencies: list[str]
) -> None:
    project_dir = tmp_path / template_name
    result = CliRunner().invoke(cli, ["init", str(project_dir), "--template", template_name])

    assert result.exit_code == 0, result.output
    assert _project_dependencies(project_dir) == expected_dependencies


@pytest.mark.parametrize("template_name", ["minimal", "basic"])
def test_existing_templates_print_metadata_next_steps(tmp_path, template_name: str) -> None:
    project_dir = tmp_path / template_name
    result = CliRunner().invoke(cli, ["init", str(project_dir), "--template", template_name])

    assert result.exit_code == 0, result.output
    assert "phlo services init" in result.output
    assert "phlo workflow create" in result.output


def test_api_ingestion_template_generates_runnable_files(tmp_path) -> None:
    project_dir = tmp_path / "api-demo"
    result = CliRunner().invoke(cli, ["init", str(project_dir), "--template", "api-ingestion"])

    assert result.exit_code == 0, result.output
    assert (project_dir / "workflows" / "ingestion" / "api" / "events.py").exists()
    assert (project_dir / "workflows" / "schemas" / "api.py").exists()
    _assert_python_files_parse(project_dir)
    _assert_generated_module_imports(project_dir, "workflows.ingestion.api.events")


@pytest.mark.parametrize(
    ("template_name", "expected_path"),
    [
        ("dbt-medallion", "workflows/transforms/dbt/models/silver/stg_events.sql"),
        ("sling-replication", "replication/sling.yaml"),
        ("observability-demo", "workflows/ingestion/observability/events.py"),
    ],
)
def test_gallery_templates_generate_expected_files(
    tmp_path, template_name: str, expected_path: str
) -> None:
    project_dir = tmp_path / template_name
    result = CliRunner().invoke(cli, ["init", str(project_dir), "--template", template_name])

    assert result.exit_code == 0, result.output
    assert (project_dir / expected_path).exists()
    _assert_python_files_parse(project_dir)
    if template_name == "observability-demo":
        _assert_generated_module_imports(project_dir, "workflows.ingestion.observability.events")


def test_template_missing_package_prints_install_hint(monkeypatch, tmp_path) -> None:
    def fake_find_spec(name: str):
        return None if name == "phlo_sling" else object()

    monkeypatch.setattr("phlo.cli.templates.registry.importlib.util.find_spec", fake_find_spec)

    result = CliRunner().invoke(
        cli, ["init", str(tmp_path / "demo"), "--template", "sling-replication"]
    )

    assert result.exit_code != 0
    assert "phlo-sling" in result.output
    assert "uv pip install" in result.output


def test_unknown_template_prints_clean_error(tmp_path) -> None:
    result = CliRunner().invoke(
        cli, ["init", str(tmp_path / "demo"), "--template", "unknown-template"]
    )

    assert result.exit_code != 0
    assert "unknown-template" in result.output
    assert "Available templates:" in result.output
    assert "Traceback" not in result.output


def test_unknown_template_real_command_has_no_plugin_traceback_noise(tmp_path) -> None:
    result = subprocess.run(
        [
            "uv",
            "run",
            "phlo",
            "init",
            str(tmp_path / "demo"),
            "--template",
            "nope",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr

    assert result.returncode != 0
    assert "Unknown template 'nope'" in output
    assert "Available templates:" in output
    assert "plugin_load_failed" not in output
    assert "Traceback" not in output

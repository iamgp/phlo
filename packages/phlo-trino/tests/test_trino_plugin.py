"""Tests for Trino service plugin."""

from pathlib import Path
from fnmatch import fnmatch
import tomllib

from phlo_trino.plugin import TrinoServicePlugin


def test_trino_service_definition():
    """Validate Trino service definition fields."""

    plugin = TrinoServicePlugin()
    service_definition = plugin.service_definition

    assert service_definition["name"] == "trino"
    assert service_definition["category"] == "core"


def test_trino_rebuilds_the_launcher_with_current_go():
    service_definition = TrinoServicePlugin().service_definition

    assert service_definition["image"] == "phlo/trino:483-launcher318-go1.26.5"
    assert service_definition["build"] == {
        "context": "./trino",
        "dockerfile": "Dockerfile",
    }
    assert {"source": "Dockerfile", "dest": "trino/Dockerfile"} in service_definition["files"]


def test_trino_runtime_files_are_included_in_package_data():
    """Every file copied into .phlo/trino must be present in installed wheels."""

    project_root = Path(__file__).parents[1]
    pyproject = tomllib.loads((project_root / "pyproject.toml").read_text())
    package_data = set(pyproject["tool"]["setuptools"]["package-data"]["phlo_trino"])

    service_definition = TrinoServicePlugin().service_definition
    file_sources = {file_spec["source"] for file_spec in service_definition["files"]}

    for source in file_sources:
        if "*" in source:
            continue
        assert any(fnmatch(source, pattern) for pattern in package_data)

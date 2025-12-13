from __future__ import annotations

import json
from pathlib import Path

import pytest

from phlo.cli.publishing import scaffold_publishing_config


def _write_manifest(path: Path, model_names: list[str]) -> None:
    nodes = {}
    for name in model_names:
        nodes[f"model.test.{name}"] = {"resource_type": "model", "name": name, "columns": {}}
    path.write_text(json.dumps({"nodes": nodes}))


def test_scaffold_publishing_config_is_idempotent() -> None:
    existing = {
        "publishing": {
            "demo": {
                "name": "publish_demo_marts",
                "group": "publishing",
                "description": "custom description",
                "dependencies": ["mrt_existing"],
                "tables": {"mrt_existing": "marts.mrt_existing"},
            }
        }
    }

    updated = scaffold_publishing_config(
        existing_config=existing,
        model_names=["mrt_existing", "mrt_new"],
        source_key="demo",
        iceberg_schema="marts",
        group="publishing",
        asset_name="publish_demo_marts",
        description="ignored",
    )

    entry = updated["publishing"]["demo"]
    assert entry["description"] == "custom description"
    assert entry["tables"]["mrt_existing"] == "marts.mrt_existing"
    assert entry["tables"]["mrt_new"] == "marts.mrt_new"
    assert entry["dependencies"] == ["mrt_existing", "mrt_new"]


def test_scaffold_command_writes_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from click.testing import CliRunner

    from phlo.cli.publishing import publishing

    monkeypatch.chdir(tmp_path)

    manifest_path = tmp_path / "manifest.json"
    _write_manifest(manifest_path, ["mrt_a", "stg_b"])

    runner = CliRunner()
    result = runner.invoke(
        publishing,
        [
            "scaffold",
            "--manifest",
            str(manifest_path),
            "--output",
            "publishing.yaml",
            "--select",
            "mrt_*",
            "--source",
            "demo",
        ],
    )
    assert result.exit_code == 0, result.output

    output_path = tmp_path / "publishing.yaml"
    contents = output_path.read_text()
    assert "publishing:" in contents
    assert "demo:" in contents
    assert "mrt_a:" in contents
    assert "stg_b" not in contents

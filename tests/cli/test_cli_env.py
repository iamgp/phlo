from __future__ import annotations

from click.testing import CliRunner

from phlo.cli.env import env


def test_env_export_rejects_malformed_project_config(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "phlo.yaml").write_text("env: [\n")

    result = CliRunner().invoke(env, ["export"])

    assert result.exit_code == 1
    assert "Failed to read" in result.output
    assert "Traceback" not in result.output

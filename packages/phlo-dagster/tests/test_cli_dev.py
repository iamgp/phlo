from __future__ import annotations

from subprocess import CompletedProcess

from click.testing import CliRunner

from phlo_dagster.cli_dev import dev


def test_phlo_dev_loads_project_env_for_dagster_subprocess(monkeypatch, tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\nversion = '0.1.0'\n")
    (tmp_path / "phlo.yaml").write_text(
        "env:\n  CLIENT_EXPORTS_KE_QC_OUTPUT_DIR: data/client_exports/ke_qc\n"
    )
    workflows_dir = tmp_path / "workflows"
    workflows_dir.mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CLIENT_EXPORTS_KE_QC_OUTPUT_DIR", raising=False)

    captured_env: dict[str, str | None] = {}

    def fake_run(cmd: list[str], check: bool) -> CompletedProcess[str]:
        captured_env["PHLO_WORKFLOWS_PATH"] = __import__("os").environ.get("PHLO_WORKFLOWS_PATH")
        captured_env["WORKFLOWS_PATH"] = __import__("os").environ.get("WORKFLOWS_PATH")
        captured_env["PHLO_PROJECT_PATH"] = __import__("os").environ.get("PHLO_PROJECT_PATH")
        captured_env["CLIENT_EXPORTS_KE_QC_OUTPUT_DIR"] = __import__("os").environ.get(
            "CLIENT_EXPORTS_KE_QC_OUTPUT_DIR"
        )
        return CompletedProcess(cmd, 0)

    monkeypatch.setattr("phlo_dagster.cli_dev.subprocess.run", fake_run)

    result = CliRunner().invoke(dev, ["--workflows-path", "workflows"])

    assert result.exit_code == 0
    assert captured_env == {
        "PHLO_WORKFLOWS_PATH": "workflows",
        "WORKFLOWS_PATH": "workflows",
        "PHLO_PROJECT_PATH": str(tmp_path),
        "CLIENT_EXPORTS_KE_QC_OUTPUT_DIR": "data/client_exports/ke_qc",
    }

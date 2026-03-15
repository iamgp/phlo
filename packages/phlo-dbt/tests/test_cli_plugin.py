"""Tests for dbt CLI commands."""

from __future__ import annotations

from subprocess import CompletedProcess
from types import SimpleNamespace

from click.testing import CliRunner

from phlo_dbt.cli_plugin import DbtCliPlugin, dbt_group


def test_dbt_cli_plugin_metadata() -> None:
    plugin = DbtCliPlugin()

    assert plugin.metadata.name == "dbt"
    assert plugin.get_cli_commands()[0].name == "dbt"


def test_dbt_run_uses_active_orchestrator_container_by_default(monkeypatch, tmp_path) -> None:
    project_dir = tmp_path / "workflows" / "transforms" / "dbt"
    profiles_dir = project_dir / "profiles"
    profiles_dir.mkdir(parents=True)
    (project_dir / "dbt_project.yml").write_text("name: demo\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("phlo_dbt.cli_plugin.ensure_phlo_dir", lambda: tmp_path / ".phlo")
    monkeypatch.setattr("phlo_dbt.cli_plugin.get_project_name", lambda: "demo")
    monkeypatch.setattr(
        "phlo_dbt.cli_plugin.get_active_orchestrator",
        lambda: SimpleNamespace(exec_service_name=lambda: "orchestrator"),
    )
    monkeypatch.setattr(
        "phlo_dbt.cli_plugin.compose_base_cmd",
        lambda **_kwargs: ["docker", "compose", "-p", "demo"],
    )
    monkeypatch.setattr(
        "phlo_dbt.cli_plugin.get_settings",
        lambda: SimpleNamespace(dbt_project_path=project_dir, dbt_profiles_path=profiles_dir),
        raising=False,
    )
    monkeypatch.setattr(
        "phlo_dbt.settings.get_settings",
        lambda: SimpleNamespace(dbt_project_path=project_dir, dbt_profiles_path=profiles_dir),
    )

    captured: list[list[str]] = []
    monkeypatch.setattr(
        "phlo_dbt.cli_plugin.subprocess",
        SimpleNamespace(
            run=lambda cmd, check=False, cwd=None: captured.append(cmd) or CompletedProcess(cmd, 0)
        ),
    )

    result = CliRunner().invoke(dbt_group, ["run", "--select", "dim_pokemon"])

    assert result.exit_code == 0
    assert captured == [
        [
            "docker",
            "compose",
            "-p",
            "demo",
            "exec",
            "-T",
            "orchestrator",
            "dbt",
            "run",
            "--project-dir",
            "/app/workflows/transforms/dbt",
            "--profiles-dir",
            "/app/workflows/transforms/dbt/profiles",
            "--target",
            "dev",
            "--select",
            "dim_pokemon",
        ]
    ]


def test_dbt_run_local_uses_host_dbt(monkeypatch, tmp_path) -> None:
    project_dir = tmp_path / "workflows" / "transforms" / "dbt"
    profiles_dir = project_dir / "profiles"
    profiles_dir.mkdir(parents=True)
    (project_dir / "dbt_project.yml").write_text("name: demo\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "phlo_dbt.settings.get_settings",
        lambda: SimpleNamespace(dbt_project_path=project_dir, dbt_profiles_path=profiles_dir),
    )
    monkeypatch.setattr("phlo_dbt.cli_plugin.ensure_dbt_profile", lambda *_args, **_kwargs: None)

    captured: list[tuple[list[str], str | None]] = []
    monkeypatch.setattr(
        "phlo_dbt.cli_plugin.subprocess",
        SimpleNamespace(
            run=lambda cmd, cwd=None, check=False: captured.append((cmd, cwd))
            or CompletedProcess(cmd, 0)
        ),
    )

    result = CliRunner().invoke(dbt_group, ["run", "--local", "--select", "dim_pokemon"])

    assert result.exit_code == 0
    assert captured == [
        (
            [
                "dbt",
                "run",
                "--profiles-dir",
                str(profiles_dir),
                "--target",
                "dev",
                "--select",
                "dim_pokemon",
            ],
            str(project_dir),
        )
    ]


def test_dbt_run_container_requires_exec_service(monkeypatch, tmp_path) -> None:
    project_dir = tmp_path / "workflows" / "transforms" / "dbt"
    profiles_dir = project_dir / "profiles"
    profiles_dir.mkdir(parents=True)
    (project_dir / "dbt_project.yml").write_text("name: demo\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("phlo_dbt.cli_plugin.ensure_phlo_dir", lambda: tmp_path / ".phlo")
    monkeypatch.setattr(
        "phlo_dbt.cli_plugin.get_active_orchestrator",
        lambda: SimpleNamespace(exec_service_name=lambda: None),
    )
    monkeypatch.setattr(
        "phlo_dbt.settings.get_settings",
        lambda: SimpleNamespace(dbt_project_path=project_dir, dbt_profiles_path=profiles_dir),
    )

    result = CliRunner().invoke(dbt_group, ["run", "--select", "dim_pokemon"])

    assert result.exit_code != 0
    assert "does not expose a container execution service" in result.output


def test_dbt_run_joins_multiple_select_flags(monkeypatch, tmp_path) -> None:
    project_dir = tmp_path / "workflows" / "transforms" / "dbt"
    profiles_dir = project_dir / "profiles"
    profiles_dir.mkdir(parents=True)
    (project_dir / "dbt_project.yml").write_text("name: demo\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("phlo_dbt.cli_plugin.ensure_phlo_dir", lambda: tmp_path / ".phlo")
    monkeypatch.setattr("phlo_dbt.cli_plugin.get_project_name", lambda: "demo")
    monkeypatch.setattr(
        "phlo_dbt.cli_plugin.get_active_orchestrator",
        lambda: SimpleNamespace(exec_service_name=lambda: "orchestrator"),
    )
    monkeypatch.setattr(
        "phlo_dbt.cli_plugin.compose_base_cmd",
        lambda **_kwargs: ["docker", "compose", "-p", "demo"],
    )
    monkeypatch.setattr(
        "phlo_dbt.settings.get_settings",
        lambda: SimpleNamespace(dbt_project_path=project_dir, dbt_profiles_path=profiles_dir),
    )

    captured: list[list[str]] = []
    monkeypatch.setattr(
        "phlo_dbt.cli_plugin.subprocess",
        SimpleNamespace(
            run=lambda cmd, check=False, cwd=None: captured.append(cmd) or CompletedProcess(cmd, 0)
        ),
    )

    result = CliRunner().invoke(
        dbt_group,
        ["run", "--select", "stg_pokemon", "--select", "dim_pokemon"],
    )

    assert result.exit_code == 0
    assert captured[0][-2:] == ["--select", "stg_pokemon dim_pokemon"]

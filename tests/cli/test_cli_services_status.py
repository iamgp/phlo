from __future__ import annotations

from subprocess import CompletedProcess

from click.testing import CliRunner

from phlo.cli.commands.services import status as status_module


def test_services_status_empty_compose_output_has_next_step(monkeypatch, tmp_path) -> None:
    phlo_dir = tmp_path / ".phlo"
    phlo_dir.mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status_module, "require_container_backend", lambda _backend=None: None)
    monkeypatch.setattr(status_module, "ensure_compose_project", lambda: phlo_dir)
    monkeypatch.setattr(status_module, "get_project_name", lambda: "demo")
    monkeypatch.setattr(
        status_module,
        "compose_base_cmd",
        lambda **_kwargs: ["docker", "compose", "-p", "demo"],
    )
    monkeypatch.setattr(
        status_module,
        "run_compose",
        lambda cmd, **_kwargs: CompletedProcess(cmd, 0, stdout="SERVICE   STATUS    PORTS\n"),
    )

    result = CliRunner().invoke(status_module.status_cmd)

    assert result.exit_code == 0
    assert "SERVICE   STATUS    PORTS" in result.output
    assert "No services are running." in result.output
    assert "Run: phlo services start" in result.output


def test_services_status_uses_service_names(monkeypatch, tmp_path) -> None:
    phlo_dir = tmp_path / ".phlo"
    phlo_dir.mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status_module, "require_container_backend", lambda _backend=None: None)
    monkeypatch.setattr(status_module, "ensure_compose_project", lambda: phlo_dir)
    monkeypatch.setattr(status_module, "get_project_name", lambda: "demo")

    captured: dict[str, list[str]] = {}

    def fake_compose_base_cmd(**_kwargs) -> list[str]:
        return ["docker-compose", "-p", "demo"]

    def fake_run_compose(cmd, **_kwargs):
        captured["cmd"] = cmd
        return CompletedProcess(
            cmd,
            0,
            stdout="SERVICE    STATUS                    PORTS\npostgres   Up 1 second (healthy)    0.0.0.0:5432->5432/tcp\n",
        )

    monkeypatch.setattr(status_module, "compose_base_cmd", fake_compose_base_cmd)
    monkeypatch.setattr(status_module, "run_compose", fake_run_compose)

    result = CliRunner().invoke(status_module.status_cmd)

    assert result.exit_code == 0
    assert any("{{.Service}}" in part for part in captured["cmd"])
    assert "postgres" in result.output
    assert "demo-postgres-1" not in result.output


def test_services_status_requires_initialized_project(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status_module, "require_container_backend", lambda _backend=None: None)

    result = CliRunner().invoke(status_module.status_cmd)

    assert result.exit_code == 1
    assert "Phlo services have not been initialized" in result.output
    assert "Missing: .phlo/" in result.output
    assert "Run: phlo services init" in result.output

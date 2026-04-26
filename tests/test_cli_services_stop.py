from __future__ import annotations

from subprocess import CompletedProcess

from click.testing import CliRunner

from phlo.cli.commands.services.stop import stop_cmd


def test_services_stop_uses_podman_backend(monkeypatch, tmp_path) -> None:
    phlo_dir = tmp_path / ".phlo"
    phlo_dir.mkdir()
    (phlo_dir / "docker-compose.yml").write_text("services:\n  postgres: {}\n")
    (phlo_dir / ".env").write_text("")
    monkeypatch.chdir(tmp_path)

    calls: list[list[str]] = []

    def _fake_run_compose(
        cmd: list[str],
        *,
        check: bool = False,
        capture_output: bool = False,
    ) -> CompletedProcess:
        calls.append(cmd)
        return CompletedProcess(cmd, 0)

    monkeypatch.setattr(
        "phlo.cli.commands.services.stop.require_container_backend",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr("phlo.cli.commands.services.stop.ensure_phlo_dir", lambda: phlo_dir)
    monkeypatch.setattr("phlo.cli.commands.services.stop.get_project_name", lambda: "demo")
    monkeypatch.setattr("phlo.cli.commands.services.stop.run_compose", _fake_run_compose)
    monkeypatch.setattr(
        "phlo.cli.commands.services.stop._emit_service_lifecycle_events",
        lambda *args, **kwargs: None,
    )

    result = CliRunner().invoke(stop_cmd, ["--backend", "podman"])

    assert result.exit_code == 0, result.output
    assert calls
    assert calls[0][:2] == ["podman", "compose"]
    assert calls[0][-1] == "down"

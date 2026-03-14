"""Tests for MinIO CLI commands."""

from __future__ import annotations

from pathlib import Path
from subprocess import CompletedProcess, TimeoutExpired

from click.testing import CliRunner

from phlo_minio.cli import minio_group
from phlo_minio.cli_plugin import MinioCliPlugin


def test_minio_cli_plugin_metadata() -> None:
    plugin = MinioCliPlugin()

    assert plugin.metadata.name == "minio"
    assert plugin.get_cli_commands()[0].name == "minio"


def test_minio_ls_runs_mc(monkeypatch) -> None:
    def _run_command(cmd, **_kwargs):
        if cmd[:2] == ["docker", "info"]:
            return CompletedProcess(cmd, 0, stdout="", stderr="")
        assert cmd[-3:] == ["mc", "ls", "local/warehouse/"]
        return CompletedProcess(cmd, 0, stdout="bucket\n", stderr="")

    monkeypatch.setattr("phlo_minio.cli.ensure_phlo_dir", lambda: Path("/tmp/project/.phlo"))
    monkeypatch.setattr("phlo_minio.cli.get_project_name", lambda: "demo")
    monkeypatch.setattr("phlo_minio.cli.which", lambda _name: "/usr/bin/docker")
    monkeypatch.setattr(
        "phlo_minio.cli.compose_base_cmd",
        lambda **_kwargs: ["docker", "compose", "-p", "demo"],
    )
    monkeypatch.setattr("phlo_minio.cli.run_command", _run_command)

    result = CliRunner().invoke(minio_group, ["ls", "local/warehouse/"])

    assert result.exit_code == 0
    assert result.output == "bucket\n"


def test_minio_admin_info_runs_mc(monkeypatch) -> None:
    def _run_command(cmd, **_kwargs):
        if cmd[:2] == ["docker", "info"]:
            return CompletedProcess(cmd, 0, stdout="", stderr="")
        assert cmd[-5:] == ["mc", "admin", "info", "--json", "local/"]
        return CompletedProcess(cmd, 0, stdout='{"status":"ok"}\n', stderr="")

    monkeypatch.setattr("phlo_minio.cli.ensure_phlo_dir", lambda: Path("/tmp/project/.phlo"))
    monkeypatch.setattr("phlo_minio.cli.get_project_name", lambda: "demo")
    monkeypatch.setattr("phlo_minio.cli.which", lambda _name: "/usr/bin/docker")
    monkeypatch.setattr(
        "phlo_minio.cli.compose_base_cmd",
        lambda **_kwargs: ["docker", "compose", "-p", "demo"],
    )
    monkeypatch.setattr("phlo_minio.cli.run_command", _run_command)

    result = CliRunner().invoke(minio_group, ["admin", "info", "--json", "local/"])

    assert result.exit_code == 0
    assert result.output == '{"status":"ok"}\n'


def test_minio_shell_passthrough(monkeypatch) -> None:
    captured: list[list[str]] = []

    monkeypatch.setattr("phlo_minio.cli.ensure_phlo_dir", lambda: Path("/tmp/project/.phlo"))
    monkeypatch.setattr("phlo_minio.cli.get_project_name", lambda: "demo")
    monkeypatch.setattr("phlo_minio.cli.which", lambda _name: "/usr/bin/docker")
    monkeypatch.setattr(
        "phlo_minio.cli.compose_base_cmd",
        lambda **_kwargs: ["docker", "compose", "-p", "demo"],
    )
    monkeypatch.setattr(
        "phlo_minio.cli.run_command",
        lambda cmd, **_kwargs: CompletedProcess(cmd, 0, stdout="", stderr=""),
    )

    def _subprocess_run(cmd, check):
        captured.append(cmd)
        return CompletedProcess(cmd, 0, stdout=None, stderr=None)

    monkeypatch.setattr("phlo_minio.cli.subprocess.run", _subprocess_run)

    result = CliRunner().invoke(minio_group, ["cp", "local/a.txt", "local/bucket/a.txt"])

    assert result.exit_code == 0
    assert captured == [
        [
            "docker",
            "compose",
            "-p",
            "demo",
            "exec",
            "minio",
            "mc",
            "cp",
            "local/a.txt",
            "local/bucket/a.txt",
        ]
    ]


def test_minio_ls_timeout(monkeypatch) -> None:
    def _run_command(cmd, **_kwargs):
        if cmd[:2] == ["docker", "info"]:
            return CompletedProcess(cmd, 0, stdout="", stderr="")
        raise TimeoutExpired(cmd=cmd, timeout=30)

    monkeypatch.setattr("phlo_minio.cli.ensure_phlo_dir", lambda: Path("/tmp/project/.phlo"))
    monkeypatch.setattr("phlo_minio.cli.get_project_name", lambda: "demo")
    monkeypatch.setattr("phlo_minio.cli.which", lambda _name: "/usr/bin/docker")
    monkeypatch.setattr(
        "phlo_minio.cli.compose_base_cmd",
        lambda **_kwargs: ["docker", "compose", "-p", "demo"],
    )
    monkeypatch.setattr("phlo_minio.cli.run_command", _run_command)

    result = CliRunner().invoke(minio_group, ["ls", "local/warehouse/"])

    assert result.exit_code != 0
    assert "List timed out after 30 seconds." in result.output

from __future__ import annotations

from pathlib import Path
from subprocess import CompletedProcess

import pytest

from phlo.cli.infrastructure.container_backend import (
    DockerBackend,
    PodmanBackend,
    select_container_backend,
    select_project_container_backend,
)
from phlo.config_schema import InfrastructureConfig


def test_docker_backend_compose_base_cmd_includes_env_files(tmp_path: Path) -> None:
    phlo_dir = tmp_path / ".phlo"
    phlo_dir.mkdir()
    (phlo_dir / "docker-compose.yml").write_text("services: {}\n")
    (phlo_dir / ".env").write_text("POSTGRES_PORT=5432\n")
    (phlo_dir / ".env.local").write_text("POSTGRES_PASSWORD=secret\n")

    cmd = DockerBackend().compose_base_cmd(
        phlo_dir=phlo_dir,
        project_name="demo",
        profiles=("observability",),
    )

    assert cmd == [
        "docker",
        "compose",
        "-p",
        "demo",
        "-f",
        str(phlo_dir / "docker-compose.yml"),
        "--env-file",
        str(phlo_dir / ".env"),
        "--env-file",
        str(phlo_dir / ".env.local"),
        "--profile",
        "observability",
    ]


def test_podman_backend_compose_base_cmd_uses_podman(tmp_path: Path) -> None:
    phlo_dir = tmp_path / ".phlo"
    phlo_dir.mkdir()
    (phlo_dir / "docker-compose.yml").write_text("services: {}\n")
    (phlo_dir / ".env").write_text("")

    cmd = PodmanBackend().compose_base_cmd(
        phlo_dir=phlo_dir,
        project_name="demo",
    )

    assert cmd[:2] == ["podman", "compose"]
    assert str(phlo_dir / "docker-compose.yml") in cmd


def test_podman_backend_lists_containers_with_podman_compose_labels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def _run(cmd: list[str], **_kwargs) -> CompletedProcess:
        calls.append(cmd)
        if "label=com.docker.compose.project=demo" in cmd:
            return CompletedProcess(cmd, 0, stdout="[]", stderr="")
        if "label=io.podman.compose.project=demo" in cmd:
            return CompletedProcess(
                cmd,
                0,
                stdout=(
                    '[{"Names":["demo_postgres_1"],"State":"running",'
                    '"Labels":{"io.podman.compose.project":"demo",'
                    '"io.podman.compose.service":"postgres"},'
                    '"Ports":"0.0.0.0:5432->5432/tcp"}]'
                ),
                stderr="",
            )
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(
        "phlo.cli.infrastructure.container_backend.subprocess.run",
        _run,
    )

    containers = PodmanBackend().list_project_containers("demo")

    assert [container.service for container in containers] == ["postgres"]
    assert containers[0].name == "demo_postgres_1"
    assert any("label=io.podman.compose.project=demo" in call for call in calls)


def test_select_backend_defaults_to_docker(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PHLO_CONTAINER_BACKEND", raising=False)

    backend = select_container_backend(cli_backend=None, config_backend=None)

    assert isinstance(backend, DockerBackend)


def test_select_backend_uses_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PHLO_CONTAINER_BACKEND", "podman")

    backend = select_container_backend(cli_backend=None, config_backend=None)

    assert backend.name == "podman"


def test_select_backend_cli_overrides_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PHLO_CONTAINER_BACKEND", "podman")

    backend = select_container_backend(cli_backend="docker", config_backend=None)

    assert backend.name == "docker"


def test_select_project_backend_uses_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PHLO_CONTAINER_BACKEND", raising=False)

    class Config:
        container_backend = "podman"

    monkeypatch.setattr(
        "phlo.infrastructure.config.load_infrastructure_config",
        lambda *_args: Config(),
    )

    backend = select_project_container_backend()

    assert backend.name == "podman"


def test_select_backend_rejects_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PHLO_CONTAINER_BACKEND", "containerd")

    with pytest.raises(ValueError, match="containerd"):
        select_container_backend(cli_backend=None, config_backend=None)


def test_infrastructure_config_accepts_container_backend() -> None:
    config = InfrastructureConfig(container_backend="podman")

    assert config.container_backend == "podman"

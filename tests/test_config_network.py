from __future__ import annotations

import socket

from phlo.config.env import load_project_env, project_env_value
from phlo.config.network import resolve_url


def test_project_env_files_load_with_local_and_os_precedence(tmp_path, monkeypatch) -> None:
    phlo_dir = tmp_path / ".phlo"
    phlo_dir.mkdir()
    (phlo_dir / ".env").write_text("TRINO_PORT=8080\nPOSTGRES_DB=phlo\n")
    (phlo_dir / ".env.local").write_text("TRINO_PORT=18080\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("POSTGRES_DB", "override")

    env = load_project_env()

    assert env["TRINO_PORT"] == "18080"
    assert env["POSTGRES_DB"] == "override"
    assert project_env_value("TRINO_PORT") == "18080"


def test_resolve_url_uses_project_env_port_for_unresolvable_service(tmp_path, monkeypatch) -> None:
    phlo_dir = tmp_path / ".phlo"
    phlo_dir.mkdir()
    (phlo_dir / ".env.local").write_text("TRINO_PORT=18080\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TRINO_PORT", raising=False)

    def raise_unresolvable(_host: str) -> str:
        raise socket.gaierror()

    monkeypatch.setattr("phlo.config.network.socket.gethostbyname", raise_unresolvable)

    assert resolve_url("http://trino:8080/v1/info", port_env_var="TRINO_PORT") == (
        "http://localhost:18080/v1/info"
    )

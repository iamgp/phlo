from __future__ import annotations

import socket
from unittest.mock import Mock, patch

from phlo_api.observatory_api import dagster, loki, nessie, quality, trino
from phlo_api.observatory_api.observatory_models import ObservatoryExternalLink
from phlo_api.observatory_api.observatory_models import ObservatoryHealth
from phlo_api.observatory_api.observatory_services import (
    merge_service_links,
    native_service_override,
    resolve_env_default,
    service_links_from_compose,
)


def _write_project_env(tmp_path, content: str) -> None:
    phlo_dir = tmp_path / ".phlo"
    phlo_dir.mkdir()
    (phlo_dir / ".env.local").write_text(content)


def _raise_unresolvable(_host: str) -> str:
    raise socket.gaierror()


def test_observatory_api_urls_use_project_port_overrides(tmp_path, monkeypatch) -> None:
    _write_project_env(
        tmp_path,
        "\n".join(
            [
                "DAGSTER_PORT=3300",
                "NESSIE_PORT=29120",
                "LOKI_PORT=13100",
            ]
        ),
    )
    monkeypatch.chdir(tmp_path)
    for key in ("DAGSTER_GRAPHQL_URL", "NESSIE_URL", "LOKI_URL"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("phlo.config.network.socket.gethostbyname", _raise_unresolvable)

    assert dagster.resolve_dagster_url() == "http://localhost:3300/graphql"
    assert quality.resolve_dagster_url() == "http://localhost:3300/graphql"
    assert nessie.resolve_nessie_url() == "http://localhost:29120/api/v2"
    assert loki.resolve_loki_url() == "http://localhost:13100"


def test_resolve_trino_url_uses_project_port_for_capability_metadata(tmp_path, monkeypatch) -> None:
    _write_project_env(tmp_path, "TRINO_PORT=18080\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PHLO_QUERY_ENGINE_URL", raising=False)
    monkeypatch.delenv("TRINO_URL", raising=False)
    monkeypatch.setattr("phlo.config.network.socket.gethostbyname", _raise_unresolvable)

    with (
        patch("phlo_api.observatory_api.trino.discover_capabilities"),
        patch(
            "phlo_api.observatory_api.trino.resolve_capability",
            return_value=Mock(metadata={"host": "trino", "port": 8080}),
        ),
    ):
        assert trino.resolve_trino_url() == "http://localhost:18080"


def test_service_links_resolve_project_env_port_overrides(tmp_path, monkeypatch) -> None:
    phlo_dir = tmp_path / ".phlo"
    phlo_dir.mkdir()
    (phlo_dir / ".env").write_text("TRINO_PORT=18080\n")
    (phlo_dir / "docker-compose.yml").write_text(
        """
services:
  trino:
    ports:
      - "${TRINO_PORT:-10005}:8080"
"""
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PHLO_PROJECT_PATH", raising=False)

    assert resolve_env_default("${TRINO_PORT:-10005}") == "18080"
    assert service_links_from_compose(tmp_path, "trino") == [
        ObservatoryExternalLink(
            label=":18080",
            url="http://localhost:18080",
            kind="port",
        )
    ]


def test_native_service_override_uses_running_local_port(monkeypatch) -> None:
    monkeypatch.setenv("PHLO_API_PORT", "4000")
    monkeypatch.setattr(
        "phlo_api.observatory_api.observatory_services._local_port_status",
        lambda port: (
            "running",
            ObservatoryHealth(state="ok", message=f"Listening on localhost:{port}"),
        )
        if port == "4000"
        else None,
    )

    status, health, port = native_service_override(
        "phlo-api",
        "unknown",
        ObservatoryHealth(state="unknown", message="Runtime status unavailable"),
    )

    assert port == "4000"
    assert status == "running"
    assert health.state == "ok"


def test_merge_service_links_prefers_native_port() -> None:
    links = merge_service_links(
        [ObservatoryExternalLink(label=":3000", url="http://localhost:3000", kind="port")],
        [ObservatoryExternalLink(label=":3001", url="http://localhost:3001", kind="port")],
    )

    assert links[0].url == "http://localhost:3000"

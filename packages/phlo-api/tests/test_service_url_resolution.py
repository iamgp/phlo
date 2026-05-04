from __future__ import annotations

import socket
from unittest.mock import Mock, patch

from phlo_api.observatory_api import dagster, loki, nessie, quality, trino


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

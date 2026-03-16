from __future__ import annotations

import socket

from phlo_iceberg.settings import IcebergSettings


def test_get_pyiceberg_catalog_config_resolves_host_service_urls(monkeypatch) -> None:
    def _raise_unresolvable(_host: str) -> str:
        raise socket.gaierror()

    monkeypatch.setattr("phlo_iceberg.settings.socket.gethostbyname", _raise_unresolvable)
    monkeypatch.setenv("NESSIE_PORT", "19120")
    monkeypatch.setenv("MINIO_API_PORT", "9000")

    settings = IcebergSettings(
        iceberg_catalog_uri="http://nessie:19120/iceberg",
        iceberg_s3_endpoint="http://minio:9000",
    )

    config = settings.get_pyiceberg_catalog_config(ref="main")

    assert config["uri"] == "http://localhost:19120/iceberg/main"
    assert config["s3.endpoint"] == "http://localhost:9000"


def test_get_pyiceberg_catalog_config_preserves_resolvable_urls(monkeypatch) -> None:
    monkeypatch.setattr("phlo_iceberg.settings.socket.gethostbyname", lambda _host: "127.0.0.1")

    settings = IcebergSettings(
        iceberg_catalog_uri="http://localhost:19120/iceberg",
        iceberg_s3_endpoint="http://localhost:9000",
    )

    config = settings.get_pyiceberg_catalog_config(ref="dev")

    assert config["uri"] == "http://localhost:19120/iceberg/dev"
    assert config["s3.endpoint"] == "http://localhost:9000"

"""Tests for Sling connection auto-discovery."""

import json
import sys
from types import SimpleNamespace
from types import ModuleType

from phlo_sling.connections import (
    _resolve_s3_connection,
    export_sling_env,
    resolve_phlo_connections,
)


def test_export_sling_env_empty():
    """Empty connections produce empty env."""
    result = export_sling_env({})
    assert result == {}


def test_export_sling_env_format():
    """Connection config is exported as JSON strings."""
    connections = {
        "TEST_PG": {"type": "postgres", "host": "localhost", "port": 5432},
    }
    result = export_sling_env(connections)
    assert "TEST_PG" in result
    parsed = json.loads(result["TEST_PG"])
    assert parsed["type"] == "postgres"
    assert parsed["host"] == "localhost"


def test_resolve_phlo_connections_respects_auto_connections_setting(monkeypatch) -> None:
    """Auto-generated connections should be skipped when disabled."""
    monkeypatch.setattr(
        "phlo_sling.connections.get_settings",
        lambda: SimpleNamespace(sling_auto_connections=False),
    )
    monkeypatch.setattr(
        "phlo_sling.connections._resolve_postgres_connection",
        lambda: {"PHLO_POSTGRES": {"type": "postgres"}},
    )
    monkeypatch.setattr(
        "phlo_sling.connections._resolve_s3_connection",
        lambda: {"PHLO_S3": {"type": "s3"}},
    )

    assert resolve_phlo_connections() == {}


def test_resolve_s3_connection_uses_minio_root_credentials(monkeypatch) -> None:
    """MinIO-backed Sling connections should use the actual settings field names."""
    minio_settings = SimpleNamespace(
        minio_endpoint=lambda: "minio:9000",
        minio_root_user="minio",
        minio_root_password="secret",
        s3_region="us-east-1",
    )
    package = ModuleType("phlo_minio")
    settings_module = ModuleType("phlo_minio.settings")
    settings_module.get_settings = lambda: minio_settings
    package.settings = settings_module
    monkeypatch.setitem(sys.modules, "phlo_minio", package)
    monkeypatch.setitem(sys.modules, "phlo_minio.settings", settings_module)

    result = _resolve_s3_connection()

    assert result["PHLO_S3"]["access_key_id"] == "minio"
    assert result["PHLO_S3"]["secret_access_key"] == "secret"

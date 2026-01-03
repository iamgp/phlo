"""
Pytest configuration and shared fixtures for Phlo tests.

This conftest.py imports fixtures from phlo_testing and makes them available
to all tests in the repository.
"""

import os
import sys
from pathlib import Path

# Disable Telemetry aggressively at system level before any imports
# Note: Lowercase 'false' is safer for TOML-based config parsers in dlt
os.environ["DLT__RUNTIME__DLTHUB_TELEMETRY"] = "false"
os.environ["DLT__RUNTIME__DLTHUB_TELEMETRY_ENDPOINT"] = "http://localhost/donotcall"
os.environ["DLT_TELEMETRY_DISABLED"] = "1"
os.environ["DAGSTER_TELEMETRY_ENABLED"] = "False"
os.environ["DAGSTER_DISABLE_TELEMETRY"] = "True"
os.environ["DO_NOT_TRACK"] = "1"  # General standard

import pytest

# Add src to path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Add workspace package sources for local test runs (monorepo layout)
packages_dir = Path(__file__).parent / "packages"
if packages_dir.exists():
    for package_src in packages_dir.glob("*/src"):
        if str(package_src) not in sys.path:
            sys.path.insert(0, str(package_src))


def _register_workspace_plugins() -> None:
    try:
        from phlo_dlt.plugin import DltDagsterPlugin

        from phlo.discovery import get_global_registry
    except Exception:
        return

    registry = get_global_registry()
    registry.register_dagster_extension(DltDagsterPlugin(), replace=True)


_register_workspace_plugins()

# Import fixtures from phlo_testing - these are auto-discovered by pytest


@pytest.fixture(autouse=True)
def reset_test_env(monkeypatch):
    """Reset environment variables before each test."""
    monkeypatch.setenv("PHLO_ENV", "test")
    monkeypatch.setenv("PHLO_LOG_LEVEL", "DEBUG")
    # Disable DLT telemetry
    monkeypatch.setenv("DLT__RUNTIME__DLTHUB_TELEMETRY", "False")
    monkeypatch.setenv("DLT_TELEMETRY_DISABLED", "1")

    # Disable Dagster telemetry
    monkeypatch.setenv("DAGSTER_TELEMETRY_ENABLED", "False")
    monkeypatch.setenv("DAGSTER_DISABLE_TELEMETRY", "True")  # Older variants


@pytest.fixture(autouse=True)
def mock_dns(monkeypatch):
    """
    Mock DNS resolver to block external calls and force localhost for telemetry.
    This prevents 'NameResolutionError' in restricted environments.
    """
    import socket

    real_getaddrinfo = socket.getaddrinfo

    def side_effect(host, port, family=0, type=0, proto=0, flags=0):
        # Allow local
        if host in ["localhost", "127.0.0.1", "::1"]:
            return real_getaddrinfo(host, port, family, type, proto, flags)

        # Block telemetry domains by routing to localhost (fails fast)
        if hasattr(host, "lower") and any(
            x in host.lower() for x in ["scalevector", "dlthub", "dagster", "segment"]
        ):
            return real_getaddrinfo("127.0.0.1", port, family, type, proto, flags)

        # Allow other calls (like MinIO if it worked, but here it won't resolve if DNS is broken)
        # We try to let them pass, if they fail, they fail.
        return real_getaddrinfo(host, port, family, type, proto, flags)

    monkeypatch.setattr(socket, "getaddrinfo", side_effect)


@pytest.fixture
def project_root() -> Path:
    """Return path to project root."""
    return Path(__file__).parent


@pytest.fixture(scope="session")
def minio_service():
    """Spin up a MinIO container for integration tests."""
    try:
        import docker
        from testcontainers.minio import MinioContainer

        # Try to verify docker access early
        client = docker.from_env()
        client.ping()
    except (ImportError, Exception):
        # Fallback to None if Docker is unavailable (very common in CI/Sandbox)
        yield None
        return

    try:
        with MinioContainer("minio/minio:latest") as minio:
            yield minio
    except Exception:
        yield None


@pytest.fixture
def iceberg_catalog(minio_service, tmp_path):
    """
    Return a PyIceberg catalog.
    If minio_service is available, uses MinIO (S3).
    Otherwise, uses local filesystem.
    """
    from pyiceberg.catalog import load_catalog

    catalog_config = {
        "type": "sql",
        "uri": f"sqlite:///{tmp_path}/catalog.db",
    }

    if minio_service:
        warehouse_path = "s3://warehouse"
        catalog_config.update(
            {
                "warehouse": warehouse_path,
                "s3.endpoint": minio_service.get_url(),
                "s3.access-key-id": minio_service.access_key,
                "s3.secret-access-key": minio_service.secret_key,
                "s3.region": "us-east-1",
                "py-io-impl": "pyiceberg.io.fsspec.FsspecFileIO",
            }
        )
    else:
        # Local fallback
        warehouse_path = f"file://{tmp_path}/warehouse"
        catalog_config.update(
            {
                "warehouse": warehouse_path,
            }
        )

    catalog = load_catalog("default", **catalog_config)

    # Init warehouse
    if minio_service:
        import s3fs

        fs = s3fs.S3FileSystem(
            endpoint_url=minio_service.get_url(),
            key=minio_service.access_key,
            secret=minio_service.secret_key,
            client_kwargs={"region_name": "us-east-1"},
        )
        try:
            fs.mkdir("warehouse")
        except FileExistsError:
            pass
    else:
        (tmp_path / "warehouse").mkdir(exist_ok=True)

    return catalog

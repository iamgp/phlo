"""Tests for RustFS settings."""

from phlo_rustfs.settings import RustfsSettings


def test_rustfs_settings_defaults():
    """Validate default settings values."""
    settings = RustfsSettings()

    assert settings.rustfs_host == "localhost"
    assert settings.rustfs_access_key == "rustfsadmin"
    assert settings.rustfs_secret_key == "rustfsadmin"
    assert settings.rustfs_api_port == 9000
    assert settings.rustfs_console_port == 9001
    assert settings.s3_region == "us-east-1"


def test_rustfs_endpoint():
    """Validate endpoint format."""
    settings = RustfsSettings()
    endpoint = settings.rustfs_endpoint()

    assert endpoint == "localhost:9000"


def test_rustfs_endpoint_custom_port():
    """Validate endpoint with custom port."""
    settings = RustfsSettings(rustfs_api_port=19000)
    endpoint = settings.rustfs_endpoint()

    assert endpoint == "localhost:19000"


def test_rustfs_endpoint_custom_host():
    """Validate endpoint with custom host."""
    settings = RustfsSettings(rustfs_host="storage.local")
    endpoint = settings.rustfs_endpoint()

    assert endpoint == "localhost:9000"

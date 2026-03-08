"""Tests for RustFS service plugin."""

from phlo_rustfs.plugin import RustfsServicePlugin, RustfsSetupServicePlugin


def test_rustfs_service_definition():
    """Validate RustFS service definition fields."""
    plugin = RustfsServicePlugin()
    service_definition = plugin.service_definition

    assert service_definition["name"] == "rustfs"
    assert service_definition["category"] == "core"
    assert service_definition["default"] is False
    assert "rustfs/rustfs" in service_definition["image"]


def test_rustfs_plugin_metadata():
    """Validate RustFS plugin metadata."""
    plugin = RustfsServicePlugin()
    metadata = plugin.metadata

    assert metadata.name == "rustfs"
    assert metadata.version == "0.1.0"
    assert "storage" in metadata.tags
    assert "s3" in metadata.tags


def test_rustfs_setup_service_definition():
    """Validate RustFS setup service definition fields."""
    plugin = RustfsSetupServicePlugin()
    service_definition = plugin.service_definition

    assert service_definition["name"] == "rustfs-setup"
    assert service_definition["category"] == "core"
    assert "rustfs" in service_definition["depends_on"]


def test_rustfs_setup_plugin_metadata():
    """Validate RustFS setup plugin metadata."""
    plugin = RustfsSetupServicePlugin()
    metadata = plugin.metadata

    assert metadata.name == "rustfs-setup"
    assert "bootstrap" in metadata.tags

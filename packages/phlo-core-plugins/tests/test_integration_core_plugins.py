"""Integration tests for phlo-core-plugins."""

import pytest

pytestmark = pytest.mark.integration


def test_service_plugins_discoverable():
    """Test that ServicePlugin is discoverable."""
    from phlo.plugins import ServicePlugin

    assert ServicePlugin is not None


def test_hook_plugins_discoverable():
    """Test that hook plugins are discoverable."""
    from phlo.plugins.hooks import HookPlugin

    assert HookPlugin is not None


def test_plugin_metadata_structure():
    """Test PluginMetadata has required fields."""
    from phlo.plugins import PluginMetadata

    meta = PluginMetadata(
        name="test",
        version="1.0.0",
        description="Test plugin"
    )
    assert meta.name == "test"
    assert meta.version == "1.0.0"


def test_plugin_base_classes_accessible():
    """Test that plugin base classes are accessible."""
    from phlo.plugins.base import PluginMetadata
    from phlo.plugins import ServicePlugin

    assert PluginMetadata is not None
    assert ServicePlugin is not None

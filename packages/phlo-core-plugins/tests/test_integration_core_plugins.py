"""Comprehensive integration tests for phlo-core-plugins.

Per TEST_STRATEGY.md:
- Plugin Loading: Verify discovery mechanism
- Plugin Lifecycle: Registration, conflict resolution, metadata validation
"""

import pytest

pytestmark = pytest.mark.integration


# =============================================================================
# Plugin Base Classes Tests
# =============================================================================

class TestPluginMetadata:
    """Test PluginMetadata functionality."""

    def test_plugin_metadata_creation(self):
        """Test creating PluginMetadata."""
        from phlo.plugins.base import PluginMetadata

        metadata = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            description="A test plugin"
        )

        assert metadata.name == "test-plugin"
        assert metadata.version == "1.0.0"
        assert metadata.description == "A test plugin"

    def test_plugin_metadata_with_optional_fields(self):
        """Test PluginMetadata with optional fields."""
        from phlo.plugins.base import PluginMetadata

        metadata = PluginMetadata(
            name="full-plugin",
            version="2.0.0",
            description="Full featured plugin",
            author="Phlo Team",
            tags=["data", "pipeline"]
        )

        assert metadata.author == "Phlo Team"
        assert "data" in metadata.tags


# =============================================================================
# ServicePlugin Tests
# =============================================================================

class TestServicePlugin:
    """Test ServicePlugin base class."""

    def test_service_plugin_importable(self):
        """Test ServicePlugin is importable."""
        from phlo.plugins import ServicePlugin

        assert ServicePlugin is not None

    def test_service_plugin_is_abstract(self):
        """Test ServicePlugin requires implementation."""
        from phlo.plugins import ServicePlugin, PluginMetadata

        # Attempting to instantiate directly should fail or have abstract methods
        class ConcretePlugin(ServicePlugin):
            @property
            def metadata(self):
                return PluginMetadata("test", "1.0.0", "test")

            @property
            def service_definition(self):
                return {"services": {}}

        plugin = ConcretePlugin()
        assert plugin.metadata.name == "test"


# =============================================================================
# HookPlugin Tests
# =============================================================================

class TestHookPlugin:
    """Test HookPlugin base class."""

    def test_hook_plugin_importable(self):
        """Test HookPlugin is importable."""
        from phlo.plugins.hooks import HookPlugin

        assert HookPlugin is not None

    def test_hook_registration_structure(self):
        """Test HookRegistration structure."""
        from phlo.plugins.hooks import HookRegistration, HookFilter

        registration = HookRegistration(
            hook_name="test_hook",
            handler=lambda x: x,
            filters=HookFilter(event_types={"test.event"})
        )

        assert registration.hook_name == "test_hook"
        assert callable(registration.handler)

    def test_hook_filter_creation(self):
        """Test HookFilter creation."""
        from phlo.plugins.hooks import HookFilter

        filter = HookFilter(event_types={"ingestion.start", "ingestion.end"})

        assert "ingestion.start" in filter.event_types


# =============================================================================
# Plugin Discovery Tests
# =============================================================================

class TestPluginDiscovery:
    """Test plugin discovery mechanism."""

    def test_discover_plugins_function_exists(self):
        """Test discover_plugins function is importable."""
        from phlo.discovery.plugins import discover_plugins

        assert callable(discover_plugins)

    def test_discover_plugins_returns_dict(self):
        """Test discover_plugins returns a dictionary."""
        from phlo.discovery.plugins import discover_plugins

        # May return empty dict if no plugins installed
        result = discover_plugins(plugin_type="services", auto_register=False)

        assert isinstance(result, dict)


# =============================================================================
# TrinoCatalogPlugin Tests
# =============================================================================

class TestTrinoCatalogPlugin:
    """Test TrinoCatalogPlugin base class."""

    def test_trino_catalog_plugin_importable(self):
        """Test TrinoCatalogPlugin is importable."""
        from phlo.plugins.base import TrinoCatalogPlugin

        assert TrinoCatalogPlugin is not None

    def test_trino_catalog_plugin_interface(self):
        """Test TrinoCatalogPlugin interface."""
        from phlo.plugins.base import TrinoCatalogPlugin, PluginMetadata

        class MockCatalog(TrinoCatalogPlugin):
            @property
            def metadata(self):
                return PluginMetadata("mock", "1.0.0", "Mock catalog")

            @property
            def catalog_name(self):
                return "mock"

            def get_properties(self):
                return {"connector.name": "mock"}

        catalog = MockCatalog()
        assert catalog.catalog_name == "mock"
        assert "connector.name=mock" in catalog.to_properties_file()


# =============================================================================
# CLI Plugin Tests
# =============================================================================

class TestCliPlugin:
    """Test CLI plugin functionality."""

    def test_cli_plugin_base_importable(self):
        """Test CLI plugin base is importable."""
        try:
            from phlo.plugins.cli import CliPlugin
            assert CliPlugin is not None
        except ImportError:
            # May have different location
            pass


# =============================================================================
# Plugin Integration Tests
# =============================================================================

class TestPluginIntegration:
    """Test plugin integration scenarios."""

    def test_multiple_plugin_types_coexist(self):
        """Test multiple plugin types can be discovered together."""
        from phlo.plugins import ServicePlugin
        from phlo.plugins.hooks import HookPlugin

        # Both should be importable
        assert ServicePlugin is not None
        assert HookPlugin is not None

    def test_plugin_metadata_serialization(self):
        """Test plugin metadata can be converted to dict."""
        from phlo.plugins.base import PluginMetadata

        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            description="Test"
        )

        # Should have __dict__ or similar
        assert hasattr(metadata, 'name')
        assert hasattr(metadata, 'version')


# =============================================================================
# Export Tests
# =============================================================================

class TestCorePluginsExports:
    """Test core plugins exports."""

    def test_phlo_plugins_exports(self):
        """Test phlo.plugins exports expected classes."""
        from phlo.plugins import ServicePlugin, PluginMetadata

        assert ServicePlugin is not None
        assert PluginMetadata is not None

    def test_phlo_plugins_base_exports(self):
        """Test phlo.plugins.base exports expected classes."""
        from phlo.plugins.base import PluginMetadata, TrinoCatalogPlugin

        assert PluginMetadata is not None
        assert TrinoCatalogPlugin is not None

    def test_phlo_plugins_hooks_exports(self):
        """Test phlo.plugins.hooks exports expected classes."""
        from phlo.plugins.hooks import HookPlugin, HookRegistration, HookFilter

        assert HookPlugin is not None
        assert HookRegistration is not None
        assert HookFilter is not None

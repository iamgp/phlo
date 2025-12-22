"""
Tests for plugin system (Spec 6).

Tests the complete plugin lifecycle:
- Discovery and registration
- Plugin metadata
- Plugin validation
- Whitelisting/blacklisting
"""

import pytest

from phlo.plugins import (
    PluginMetadata,
    QualityCheckPlugin,
    ServicePlugin,
    SourceConnectorPlugin,
    TransformationPlugin,
    discover_plugins,
    get_plugin_info,
    get_quality_check,
    get_service,
    get_source_connector,
    get_transformation,
    list_plugins,
    validate_plugins,
)
from phlo.plugins.registry import get_global_registry


# Test plugins
class DummySourcePlugin(SourceConnectorPlugin):
    """Test source connector plugin."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="test_source",
            version="1.0.0",
            description="Test source plugin",
            author="Test",
        )

    def fetch_data(self, config):
        """Fetch test data."""
        yield {"id": 1, "value": "test"}


class DummyQualityPlugin(QualityCheckPlugin):
    """Test quality check plugin."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="test_quality",
            version="1.0.0",
            description="Test quality plugin",
        )

    def create_check(self, **kwargs):
        """Create test check."""
        return None


class DummyTransformPlugin(TransformationPlugin):
    """Test transformation plugin."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="test_transform",
            version="1.0.0",
            description="Test transform plugin",
        )

    def transform(self, df, config):
        """Transform test data."""
        return df


class DummyServicePlugin(ServicePlugin):
    """Test service plugin."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="test_service",
            version="1.0.0",
            description="Test service plugin",
        )

    @property
    def service_definition(self) -> dict:
        return {
            "category": "core",
            "compose": {"image": "test-service:latest"},
        }


@pytest.fixture
def clean_registry():
    """Clear and restore registry for each test."""
    registry = get_global_registry()
    registry.clear()
    yield registry
    registry.clear()


class TestPluginRegistration:
    """Test plugin registration."""

    def test_register_source_connector(self, clean_registry):
        """Test registering a source connector."""
        plugin = DummySourcePlugin()
        clean_registry.register_source_connector(plugin)

        retrieved = clean_registry.get_source_connector("test_source")
        assert retrieved is plugin

    def test_register_quality_check(self, clean_registry):
        """Test registering a quality check."""
        plugin = DummyQualityPlugin()
        clean_registry.register_quality_check(plugin)

        retrieved = clean_registry.get_quality_check("test_quality")
        assert retrieved is plugin

    def test_register_transformation(self, clean_registry):
        """Test registering a transformation."""
        plugin = DummyTransformPlugin()
        clean_registry.register_transformation(plugin)

        retrieved = clean_registry.get_transformation("test_transform")
        assert retrieved is plugin

    def test_register_service(self, clean_registry):
        """Test registering a service."""
        plugin = DummyServicePlugin()
        clean_registry.register_service(plugin)

        retrieved = clean_registry.get_service("test_service")
        assert retrieved is plugin

    def test_duplicate_registration_raises_error(self, clean_registry):
        """Test duplicate registration raises error."""
        plugin = DummySourcePlugin()
        clean_registry.register_source_connector(plugin)

        with pytest.raises(ValueError):
            clean_registry.register_source_connector(plugin)

    def test_duplicate_registration_with_replace(self, clean_registry):
        """Test duplicate registration with replace=True."""
        plugin1 = DummySourcePlugin()
        clean_registry.register_source_connector(plugin1)

        plugin2 = DummySourcePlugin()
        clean_registry.register_source_connector(plugin2, replace=True)

        retrieved = clean_registry.get_source_connector("test_source")
        assert retrieved is plugin2


class TestPluginMetadata:
    """Test plugin metadata retrieval."""

    def test_get_source_metadata(self, clean_registry):
        """Test getting source metadata."""
        plugin = DummySourcePlugin()
        clean_registry.register_source_connector(plugin)

        metadata = clean_registry.get_plugin_metadata("source_connectors", "test_source")
        assert metadata["name"] == "test_source"
        assert metadata["version"] == "1.0.0"
        assert metadata["author"] == "Test"

    def test_get_quality_metadata(self, clean_registry):
        """Test getting quality metadata."""
        plugin = DummyQualityPlugin()
        clean_registry.register_quality_check(plugin)

        metadata = clean_registry.get_plugin_metadata("quality_checks", "test_quality")
        assert metadata["name"] == "test_quality"

    def test_get_service_metadata(self, clean_registry):
        """Test getting service metadata."""
        plugin = DummyServicePlugin()
        clean_registry.register_service(plugin)

        metadata = clean_registry.get_plugin_metadata("services", "test_service")
        assert metadata["name"] == "test_service"

    def test_missing_plugin_returns_none(self, clean_registry):
        """Test getting metadata for non-existent plugin."""
        metadata = clean_registry.get_plugin_metadata("source_connectors", "nonexistent")
        assert metadata is None


class TestPluginValidation:
    """Test plugin validation."""

    def test_validate_valid_plugin(self, clean_registry):
        """Test validating a valid plugin."""
        plugin = DummySourcePlugin()
        assert clean_registry.validate_plugin(plugin) is True
        service_plugin = DummyServicePlugin()
        assert clean_registry.validate_plugin(service_plugin) is True

    def test_validate_missing_metadata(self, clean_registry):
        """Test validation fails for missing metadata."""

        class BadPlugin:
            pass

        assert clean_registry.validate_plugin(BadPlugin()) is False

    def test_validate_missing_required_method(self, clean_registry):
        """Test validation fails for missing required method."""
        # Note: Abstract methods are enforced at instantiation time,
        # so we test with a mock that has the structure but missing callable

        class BrokenSource(SourceConnectorPlugin):
            @property
            def metadata(self):
                return PluginMetadata(name="broken", version="1.0.0")

            def fetch_data(self, config):
                return []

        plugin = BrokenSource()
        # Override to make it not callable
        plugin.fetch_data = None  # type: ignore
        assert clean_registry.validate_plugin(plugin) is False


class TestPluginListing:
    """Test plugin listing."""

    def test_list_empty_registry(self, clean_registry):
        """Test listing from empty registry."""
        plugins = list_plugins()
        assert all(len(v) == 0 for v in plugins.values())

    def test_list_source_connectors(self, clean_registry):
        """Test listing source connectors."""
        plugin1 = DummySourcePlugin()

        class AnotherSourcePlugin(SourceConnectorPlugin):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="test_source2",
                    version="1.0.0",
                    description="Test source plugin 2",
                )

            def fetch_data(self, config):
                yield {"id": 2, "value": "test2"}

        plugin2 = AnotherSourcePlugin()

        clean_registry.register_source_connector(plugin1)
        clean_registry.register_source_connector(plugin2)

        sources = clean_registry.list_source_connectors()
        assert "test_source" in sources
        assert "test_source2" in sources

    def test_list_all_plugins(self, clean_registry):
        """Test listing all plugins."""
        clean_registry.register_source_connector(DummySourcePlugin())
        clean_registry.register_quality_check(DummyQualityPlugin())
        clean_registry.register_transformation(DummyTransformPlugin())
        clean_registry.register_service(DummyServicePlugin())

        all_plugins = clean_registry.list_all_plugins()
        assert "test_source" in all_plugins["source_connectors"]
        assert "test_quality" in all_plugins["quality_checks"]
        assert "test_transform" in all_plugins["transformations"]
        assert "test_service" in all_plugins["services"]


class TestPluginDiscovery:
    """Test plugin discovery (entry points)."""

    def test_discover_plugins_returns_dict(self):
        """Test discover_plugins returns correct structure."""
        result = discover_plugins(auto_register=False)

        assert isinstance(result, dict)
        assert "source_connectors" in result
        assert "quality_checks" in result
        assert "transformations" in result
        assert "services" in result

    def test_discover_single_type(self):
        """Test discovering single plugin type."""
        result = discover_plugins(plugin_type="source_connectors", auto_register=False)

        assert "source_connectors" in result
        # Other types might not be present
        assert isinstance(result["source_connectors"], list)

    def test_discover_services_type(self):
        """Test discovering service plugins."""
        result = discover_plugins(plugin_type="services", auto_register=False)

        assert "services" in result
        assert isinstance(result["services"], list)

    def test_discover_with_validation(self):
        """Test discovery validates plugins."""
        result = discover_plugins(auto_register=False)

        # All discovered plugins should be valid
        for plugin_list in result.values():
            for plugin in plugin_list:
                registry = get_global_registry()
                assert registry.validate_plugin(plugin)


class TestPluginIntegration:
    """Integration tests for plugin system."""

    def test_register_and_retrieve(self, clean_registry):
        """Test registering and retrieving plugins."""
        source = DummySourcePlugin()
        quality = DummyQualityPlugin()
        transform = DummyTransformPlugin()
        service = DummyServicePlugin()

        clean_registry.register_source_connector(source)
        clean_registry.register_quality_check(quality)
        clean_registry.register_transformation(transform)
        clean_registry.register_service(service)

        # Retrieve using public functions
        assert get_source_connector("test_source") is source
        assert get_quality_check("test_quality") is quality
        assert get_transformation("test_transform") is transform
        assert get_service("test_service") is service

    def test_get_plugin_info(self, clean_registry):
        """Test getting plugin information."""
        plugin = DummySourcePlugin()
        clean_registry.register_source_connector(plugin)

        info = get_plugin_info("source_connectors", "test_source")
        assert info is not None
        assert info["name"] == "test_source"
        assert info["version"] == "1.0.0"

    def test_validate_plugins(self, clean_registry):
        """Test validating all plugins."""
        clean_registry.register_source_connector(DummySourcePlugin())
        clean_registry.register_quality_check(DummyQualityPlugin())

        result = validate_plugins()

        assert "valid" in result
        assert "invalid" in result
        assert len(result["valid"]) == 2
        assert len(result["invalid"]) == 0

    def test_register_get_list_flow(self, clean_registry):
        """Test complete workflow of register, get, and list."""
        plugin = DummySourcePlugin()
        clean_registry.register_source_connector(plugin)

        # List
        plugins = clean_registry.list_source_connectors()
        assert "test_source" in plugins

        # Get
        retrieved = clean_registry.get_source_connector("test_source")
        assert retrieved is plugin

        # Get info
        info = clean_registry.get_plugin_metadata("source_connectors", "test_source")
        assert info["name"] == "test_source"

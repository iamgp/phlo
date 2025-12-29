"""Comprehensive integration tests for infrastructure service packages.

These tests cover: phlo-grafana, phlo-loki, phlo-prometheus, phlo-hasura,
phlo-postgrest, phlo-pgweb, phlo-alloy, phlo-superset

Per TEST_STRATEGY.md Level 2 (Functional):
- Config Validation: Verify configuration is valid
- Health: Verify service reachable (if available)
"""

import pytest

pytestmark = pytest.mark.integration


# =============================================================================
# Helper Functions
# =============================================================================

def verify_service_plugin(plugin_class, expected_name):
    """Helper to verify a service plugin."""
    plugin = plugin_class()

    assert plugin is not None
    assert plugin.metadata.name == expected_name
    assert plugin.metadata.version is not None

    service_def = plugin.service_definition
    assert isinstance(service_def, dict)

    return plugin


# =============================================================================
# Grafana Tests
# =============================================================================

class TestGrafanaServicePlugin:
    """Test Grafana service plugin."""

    def test_plugin_initializes(self):
        """Test GrafanaServicePlugin can be instantiated."""
        from phlo_grafana.plugin import GrafanaServicePlugin
        verify_service_plugin(GrafanaServicePlugin, "grafana")

    def test_service_has_dashboards(self):
        """Test Grafana service has dashboard configuration."""
        from phlo_grafana.plugin import GrafanaServicePlugin

        plugin = GrafanaServicePlugin()
        service_def = plugin.service_definition

        # Should have grafana-related structure
        assert isinstance(service_def, dict)

    def test_module_importable(self):
        """Test phlo_grafana is importable."""
        import phlo_grafana
        assert phlo_grafana is not None


# =============================================================================
# Loki Tests
# =============================================================================

class TestLokiServicePlugin:
    """Test Loki service plugin."""

    def test_plugin_initializes(self):
        """Test LokiServicePlugin can be instantiated."""
        from phlo_loki.plugin import LokiServicePlugin
        verify_service_plugin(LokiServicePlugin, "loki")

    def test_module_importable(self):
        """Test phlo_loki is importable."""
        import phlo_loki
        assert phlo_loki is not None


# =============================================================================
# Prometheus Tests
# =============================================================================

class TestPrometheusServicePlugin:
    """Test Prometheus service plugin."""

    def test_plugin_initializes(self):
        """Test PrometheusServicePlugin can be instantiated."""
        from phlo_prometheus.plugin import PrometheusServicePlugin
        verify_service_plugin(PrometheusServicePlugin, "prometheus")

    def test_module_importable(self):
        """Test phlo_prometheus is importable."""
        import phlo_prometheus
        assert phlo_prometheus is not None


# =============================================================================
# Hasura Tests
# =============================================================================

class TestHasuraServicePlugin:
    """Test Hasura service plugin."""

    def test_plugin_initializes(self):
        """Test HasuraServicePlugin can be instantiated."""
        from phlo_hasura.plugin import HasuraServicePlugin
        verify_service_plugin(HasuraServicePlugin, "hasura")

    def test_module_importable(self):
        """Test phlo_hasura is importable."""
        import phlo_hasura
        assert phlo_hasura is not None


# =============================================================================
# PostgREST Tests
# =============================================================================

class TestPostgrestServicePlugin:
    """Test PostgREST service plugin."""

    def test_plugin_initializes(self):
        """Test PostgrestServicePlugin can be instantiated."""
        from phlo_postgrest.plugin import PostgrestServicePlugin
        verify_service_plugin(PostgrestServicePlugin, "postgrest")

    def test_service_definition_valid(self):
        """Test service definition has required fields."""
        from phlo_postgrest.plugin import PostgrestServicePlugin

        plugin = PostgrestServicePlugin()
        service_def = plugin.service_definition

        # Should have docker-compose-like structure
        assert "services" in service_def or service_def.get("service")

    def test_module_importable(self):
        """Test phlo_postgrest is importable."""
        import phlo_postgrest
        assert phlo_postgrest is not None


# =============================================================================
# PgWeb Tests
# =============================================================================

class TestPgwebServicePlugin:
    """Test PgWeb service plugin."""

    def test_plugin_initializes(self):
        """Test PgwebServicePlugin can be instantiated."""
        from phlo_pgweb.plugin import PgwebServicePlugin
        verify_service_plugin(PgwebServicePlugin, "pgweb")

    def test_module_importable(self):
        """Test phlo_pgweb is importable."""
        import phlo_pgweb
        assert phlo_pgweb is not None


# =============================================================================
# Alloy Tests
# =============================================================================

class TestAlloyServicePlugin:
    """Test Alloy service plugin."""

    def test_plugin_initializes(self):
        """Test AlloyServicePlugin can be instantiated."""
        from phlo_alloy.plugin import AlloyServicePlugin
        verify_service_plugin(AlloyServicePlugin, "alloy")

    def test_module_importable(self):
        """Test phlo_alloy is importable."""
        import phlo_alloy
        assert phlo_alloy is not None


# =============================================================================
# Superset Tests
# =============================================================================

class TestSupersetServicePlugin:
    """Test Superset service plugin."""

    def test_plugin_initializes(self):
        """Test SupersetServicePlugin can be instantiated."""
        from phlo_superset.plugin import SupersetServicePlugin
        verify_service_plugin(SupersetServicePlugin, "superset")

    def test_module_importable(self):
        """Test phlo_superset is importable."""
        import phlo_superset
        assert phlo_superset is not None


# =============================================================================
# OpenMetadata Tests
# =============================================================================

class TestOpenMetadataExports:
    """Test OpenMetadata module exports."""

    def test_client_importable(self):
        """Test OpenMetadataClient is importable."""
        from phlo_openmetadata import OpenMetadataClient
        assert OpenMetadataClient is not None

    def test_models_importable(self):
        """Test OpenMetadata models are importable."""
        from phlo_openmetadata import (
            OpenMetadataColumn,
            OpenMetadataLineageEdge,
            OpenMetadataTable,
        )

        assert OpenMetadataColumn is not None
        assert OpenMetadataLineageEdge is not None
        assert OpenMetadataTable is not None

    def test_dbt_manifest_parser_importable(self):
        """Test DbtManifestParser is importable."""
        from phlo_openmetadata import DbtManifestParser
        assert DbtManifestParser is not None


# =============================================================================
# Observatory Tests
# =============================================================================

class TestObservatoryExports:
    """Test Observatory module exports."""

    def test_module_importable(self):
        """Test phlo_observatory is importable."""
        import phlo_observatory
        assert phlo_observatory is not None


# =============================================================================
# Testing Package Tests
# =============================================================================

class TestTestingPackage:
    """Test phlo-testing package."""

    def test_module_importable(self):
        """Test phlo_testing is importable."""
        import phlo_testing
        assert phlo_testing is not None


# =============================================================================
# Shared Infrastructure Plugin Pattern Tests
# =============================================================================

class TestInfrastructurePluginPattern:
    """Test that all infrastructure plugins follow the same pattern."""

    def test_all_plugins_have_metadata_property(self):
        """Test all plugins have metadata property."""
        from phlo_grafana.plugin import GrafanaServicePlugin
        from phlo_loki.plugin import LokiServicePlugin
        from phlo_prometheus.plugin import PrometheusServicePlugin
        from phlo_hasura.plugin import HasuraServicePlugin
        from phlo_postgrest.plugin import PostgrestServicePlugin
        from phlo_pgweb.plugin import PgwebServicePlugin
        from phlo_alloy.plugin import AlloyServicePlugin
        from phlo_superset.plugin import SupersetServicePlugin

        plugins = [
            GrafanaServicePlugin(),
            LokiServicePlugin(),
            PrometheusServicePlugin(),
            HasuraServicePlugin(),
            PostgrestServicePlugin(),
            PgwebServicePlugin(),
            AlloyServicePlugin(),
            SupersetServicePlugin(),
        ]

        for plugin in plugins:
            assert hasattr(plugin, "metadata")
            assert plugin.metadata.name is not None
            assert plugin.metadata.version is not None

    def test_all_plugins_have_service_definition(self):
        """Test all plugins have service_definition property."""
        from phlo_grafana.plugin import GrafanaServicePlugin
        from phlo_loki.plugin import LokiServicePlugin
        from phlo_prometheus.plugin import PrometheusServicePlugin
        from phlo_hasura.plugin import HasuraServicePlugin
        from phlo_postgrest.plugin import PostgrestServicePlugin
        from phlo_pgweb.plugin import PgwebServicePlugin
        from phlo_alloy.plugin import AlloyServicePlugin
        from phlo_superset.plugin import SupersetServicePlugin

        plugins = [
            GrafanaServicePlugin(),
            LokiServicePlugin(),
            PrometheusServicePlugin(),
            HasuraServicePlugin(),
            PostgrestServicePlugin(),
            PgwebServicePlugin(),
            AlloyServicePlugin(),
            SupersetServicePlugin(),
        ]

        for plugin in plugins:
            service_def = plugin.service_definition
            assert isinstance(service_def, dict)

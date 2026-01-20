"""Tests for core Phlo configuration."""

import os
from unittest.mock import patch

from phlo.config import Settings, _get_config


class TestConfigUnitTests:
    """Unit tests for core configuration loading and caching."""

    def test_config_loads_environment_variables_correctly(self):
        """Test that core settings load environment variables correctly."""
        env_vars = {
            "PHLO_LOG_LEVEL": "DEBUG",
            "PHLO_LOG_FORMAT": "json",
            "PLUGINS_ENABLED": "false",
            "PHLO_ORCHESTRATOR": "custom",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            test_config = Settings()

            assert test_config.phlo_log_level == "DEBUG"
            assert test_config.phlo_log_format == "json"
            assert test_config.plugins_enabled is False
            assert test_config.phlo_orchestrator == "custom"

    def test_config_handles_caching_and_returns_same_instance(self):
        """Test that config handles caching and returns the same instance."""
        env_vars = {
            "PHLO_LOG_LEVEL": "INFO",
            "PLUGINS_ENABLED": "true",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            _get_config.cache_clear()

            config1 = _get_config()
            config2 = _get_config()

            assert config1 is config2
            assert id(config1) == id(config2)

"""Tests for infrastructure configuration."""

import tempfile
from pathlib import Path

import pytest
import yaml

from phlo.config_schema import (
    InfrastructureConfig,
    ServiceConfig,
    get_default_infrastructure_config,
)
from phlo.infrastructure import clear_config_cache, get_container_name, load_infrastructure_config


def test_service_config_defaults():
    """Test ServiceConfig with defaults."""
    service = ServiceConfig(service_name="test-service")

    assert service.service_name == "test-service"
    assert service.container_name is None
    assert service.host == "localhost"
    assert service.internal_host is None
    assert service.get_internal_host() == "test-service"


def test_service_config_with_values():
    """Test ServiceConfig with explicit values."""
    service = ServiceConfig(
        service_name="dagster-webserver",
        container_name="custom-dagster",
        host="192.168.1.100",
        internal_host="dagster",
    )

    assert service.service_name == "dagster-webserver"
    assert service.container_name == "custom-dagster"
    assert service.host == "192.168.1.100"
    assert service.get_internal_host() == "dagster"


def test_service_config_container_name_validation():
    """Test container name validation."""
    with pytest.raises(ValueError, match="container_name cannot be empty"):
        ServiceConfig(service_name="test", container_name="")

    with pytest.raises(ValueError, match="must contain only alphanumeric"):
        ServiceConfig(service_name="test", container_name="invalid@name")

    with pytest.raises(ValueError, match="cannot start with hyphen"):
        ServiceConfig(service_name="test", container_name="-invalid")


def test_service_config_get_container_name():
    """Test get_container_name with pattern."""
    service = ServiceConfig(service_name="dagster-webserver")
    pattern = "{project}-{service}-1"

    assert service.get_container_name("myproject", pattern) == "myproject-dagster-webserver-1"


def test_service_config_get_container_name_with_override():
    """Test get_container_name with explicit override."""
    service = ServiceConfig(
        service_name="dagster-webserver",
        container_name="my-custom-container"
    )
    pattern = "{project}-{service}-1"

    assert service.get_container_name("myproject", pattern) == "my-custom-container"


def test_infrastructure_config_defaults():
    """Test InfrastructureConfig with defaults."""
    config = InfrastructureConfig()

    assert config.container_naming_pattern == "{project}-{service}-1"
    assert len(config.services) == 0
    assert config.network.driver == "bridge"


def test_infrastructure_config_pattern_validation():
    """Test pattern validation."""
    with pytest.raises(ValueError, match="must contain at least"):
        InfrastructureConfig(container_naming_pattern="invalid-pattern")


def test_infrastructure_config_get_service():
    """Test get_service method."""
    config = InfrastructureConfig(
        services={
            "dagster": ServiceConfig(service_name="dagster-webserver")
        }
    )

    service = config.get_service("dagster")
    assert service is not None
    assert service.service_name == "dagster-webserver"

    assert config.get_service("nonexistent") is None


def test_infrastructure_config_get_container_name():
    """Test get_container_name method."""
    config = InfrastructureConfig(
        container_naming_pattern="{project}-{service}-1",
        services={
            "dagster": ServiceConfig(service_name="dagster-webserver")
        }
    )

    name = config.get_container_name("dagster", "myproject")
    assert name == "myproject-dagster-webserver-1"

    assert config.get_container_name("nonexistent", "myproject") is None


def test_get_default_infrastructure_config():
    """Test default configuration generation."""
    config = get_default_infrastructure_config()

    assert len(config.services) == 9
    assert "dagster_webserver" in config.services
    assert "postgres" in config.services
    assert "trino" in config.services

    dagster = config.services["dagster_webserver"]
    assert dagster.service_name == "dagster-webserver"
    assert dagster.internal_host == "dagster-webserver"


def test_load_infrastructure_config_no_file():
    """Test loading config when no phlo.yaml exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        clear_config_cache()
        config = load_infrastructure_config(Path(tmpdir))

        assert len(config.services) == 9
        assert config.container_naming_pattern == "{project}-{service}-1"


def test_load_infrastructure_config_with_file():
    """Test loading config from phlo.yaml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "phlo.yaml"

        phlo_config = {
            "name": "test-project",
            "infrastructure": {
                "container_naming_pattern": "{project}_{service}",
                "services": {
                    "dagster_webserver": {
                        "service_name": "dagster-webserver",
                        "host": "localhost",
                        "internal_host": "dagster",
                    }
                }
            }
        }

        with open(config_path, "w") as f:
            yaml.dump(phlo_config, f)

        clear_config_cache()
        config = load_infrastructure_config(Path(tmpdir))

        assert config.container_naming_pattern == "{project}_{service}"
        assert len(config.services) == 1
        assert "dagster_webserver" in config.services


def test_load_infrastructure_config_invalid_yaml():
    """Test loading config with invalid YAML."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "phlo.yaml"
        config_path.write_text("invalid: yaml: content:")

        clear_config_cache()
        config = load_infrastructure_config(Path(tmpdir))

        assert len(config.services) == 9


def test_get_container_name_helper():
    """Test get_container_name helper function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "phlo.yaml"

        phlo_config = {
            "name": "test-project",
            "infrastructure": {
                "services": {
                    "dagster_webserver": {
                        "service_name": "dagster-webserver",
                        "internal_host": "dagster",
                    }
                }
            }
        }

        with open(config_path, "w") as f:
            yaml.dump(phlo_config, f)

        clear_config_cache()
        name = get_container_name("dagster_webserver", "myproject", Path(tmpdir))

        assert name == "myproject-dagster-webserver-1"

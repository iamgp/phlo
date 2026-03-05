"""Tests for infrastructure configuration."""

import tempfile
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from phlo.config_schema import InfrastructureConfig, ServiceConfig
from phlo.infrastructure import (
    clear_config_cache,
    get_container_name,
    get_project_name_from_config,
    get_service_config,
    load_infrastructure_config,
)


@pytest.fixture(autouse=True)
def _clear_infra_config_cache():
    """Ensure load_infrastructure_config cache does not leak between tests."""
    clear_config_cache()
    yield
    clear_config_cache()


def _write_phlo_yaml(config_path: Path, config: dict) -> None:
    """Write a phlo.yaml fixture payload."""
    with config_path.open("w") as f:
        yaml.safe_dump(config, f, sort_keys=False)


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
    service = ServiceConfig(service_name="dagster-webserver", container_name="my-custom-container")
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
        services={"dagster": ServiceConfig(service_name="dagster-webserver")}
    )

    service = config.get_service("dagster")
    assert service is not None
    assert service.service_name == "dagster-webserver"

    assert config.get_service("nonexistent") is None


def test_infrastructure_config_get_container_name():
    """Test get_container_name method."""
    config = InfrastructureConfig(
        container_naming_pattern="{project}-{service}-1",
        services={"dagster": ServiceConfig(service_name="dagster-webserver")},
    )

    name = config.get_container_name("dagster", "myproject")
    assert name == "myproject-dagster-webserver-1"

    assert config.get_container_name("nonexistent", "myproject") is None


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
                },
            },
        }

        with config_path.open("w") as f:
            yaml.dump(phlo_config, f)

        clear_config_cache()
        config = load_infrastructure_config(Path(tmpdir))

        assert config.container_naming_pattern == "{project}_{service}"
        assert len(config.services) == 1
        assert "dagster_webserver" in config.services


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
            },
        }

        with config_path.open("w") as f:
            yaml.dump(phlo_config, f)

        clear_config_cache()
        name = get_container_name("dagster_webserver", "myproject", Path(tmpdir))

        assert name == "myproject-dagster-webserver-1"


def test_load_infrastructure_config_missing_file_returns_defaults(tmp_path: Path):
    """Missing phlo.yaml should return default infrastructure config."""
    config = load_infrastructure_config(tmp_path)

    assert config.container_naming_pattern == "{project}-{service}-1"
    assert config.services == {}
    assert config.network.driver == "bridge"


def test_load_infrastructure_config_empty_file_returns_defaults(tmp_path: Path):
    """Empty phlo.yaml should return default infrastructure config."""
    config_path = tmp_path / "phlo.yaml"
    config_path.write_text("")

    config = load_infrastructure_config(tmp_path)

    assert config.container_naming_pattern == "{project}-{service}-1"
    assert config.services == {}
    assert config.network.driver == "bridge"


def test_load_infrastructure_config_missing_infrastructure_section_returns_defaults(tmp_path: Path):
    """Config without infrastructure section should return defaults."""
    config_path = tmp_path / "phlo.yaml"
    _write_phlo_yaml(config_path, {"name": "test-project"})

    config = load_infrastructure_config(tmp_path)

    assert config.container_naming_pattern == "{project}-{service}-1"
    assert config.services == {}
    assert config.network.driver == "bridge"


def test_load_infrastructure_config_invalid_yaml_raises(tmp_path: Path):
    """Invalid YAML should be surfaced to the caller."""
    config_path = tmp_path / "phlo.yaml"
    config_path.write_text("infrastructure:\n  services:\n    dagster: [")

    with pytest.raises(yaml.YAMLError):
        load_infrastructure_config(tmp_path)


def test_load_infrastructure_config_invalid_schema_raises(tmp_path: Path):
    """Invalid infrastructure schema should raise ValidationError."""
    config_path = tmp_path / "phlo.yaml"
    _write_phlo_yaml(
        config_path,
        {
            "infrastructure": {
                "container_naming_pattern": "invalid-pattern",
            }
        },
    )

    with pytest.raises(ValidationError):
        load_infrastructure_config(tmp_path)


def test_get_project_name_from_config_handles_missing_and_invalid_config(tmp_path: Path):
    """Project name helper should gracefully handle missing/invalid config."""
    assert get_project_name_from_config(tmp_path) is None

    config_path = tmp_path / "phlo.yaml"
    _write_phlo_yaml(config_path, {"name": "test-project"})
    assert get_project_name_from_config(tmp_path) == "test-project"

    config_path.write_text("name: [")
    assert get_project_name_from_config(tmp_path) is None


def test_service_config_and_container_name_helpers_use_service_override(tmp_path: Path):
    """Helper functions should honor configured service overrides."""
    config_path = tmp_path / "phlo.yaml"
    _write_phlo_yaml(
        config_path,
        {
            "infrastructure": {
                "services": {
                    "dagster": {
                        "service_name": "dagster-webserver",
                        "container_name": "custom-dagster-web",
                    }
                }
            }
        },
    )

    service = get_service_config("dagster", tmp_path)

    assert service is not None
    assert service.container_name == "custom-dagster-web"
    assert get_container_name("dagster", "test-project", tmp_path) == "custom-dagster-web"
    assert get_service_config("missing", tmp_path) is None
    assert get_container_name("missing", "test-project", tmp_path) is None


def test_clear_config_cache_refreshes_updated_file_contents(tmp_path: Path):
    """clear_config_cache should force a reload after file changes."""
    config_path = tmp_path / "phlo.yaml"

    _write_phlo_yaml(
        config_path,
        {
            "infrastructure": {
                "container_naming_pattern": "{project}-{service}-1",
                "services": {"dagster": {"service_name": "dagster-webserver"}},
            }
        },
    )
    first_config = load_infrastructure_config(tmp_path)
    assert first_config.container_naming_pattern == "{project}-{service}-1"

    _write_phlo_yaml(
        config_path,
        {
            "infrastructure": {
                "container_naming_pattern": "{project}_{service}",
                "services": {
                    "dagster": {
                        "service_name": "dagster-webserver",
                        "container_name": "updated-container",
                    }
                },
            }
        },
    )

    stale_config = load_infrastructure_config(tmp_path)
    assert stale_config is first_config
    assert stale_config.container_naming_pattern == "{project}-{service}-1"

    clear_config_cache()
    refreshed_config = load_infrastructure_config(tmp_path)

    assert refreshed_config is not first_config
    assert refreshed_config.container_naming_pattern == "{project}_{service}"
    assert get_container_name("dagster", "test-project", tmp_path) == "updated-container"

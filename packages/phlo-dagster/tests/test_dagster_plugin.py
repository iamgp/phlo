"""Tests for Dagster service plugin."""

from importlib import resources

from phlo_dagster.plugin import DagsterServicePlugin


def test_dagster_service_definition():
    """Verify the Dagster plugin exposes expected service metadata."""
    plugin = DagsterServicePlugin()
    service_definition = plugin.service_definition

    assert service_definition["name"] == "dagster"
    assert service_definition["category"] == "orchestration"
    assert "profile" not in service_definition


def test_dagster_service_uses_discoverable_dbt_project_and_mounts_project_metadata() -> None:
    service_yaml = resources.files("phlo_dagster").joinpath("service.yaml").read_text()
    dockerfile = resources.files("phlo_dagster").joinpath("Dockerfile").read_text()

    assert "PHLO_WORKFLOWS_PATH: /app/workflows" in service_yaml
    assert "DBT_PROJECT_DIR:" not in service_yaml
    assert "../:/app" in service_yaml
    assert "dagster-webserver" in dockerfile


def test_dagster_daemon_uses_same_project_discovery_contract() -> None:
    daemon_yaml = resources.files("phlo_dagster").joinpath("dagster-daemon.yaml").read_text()

    assert "PHLO_WORKFLOWS_PATH: /app/workflows" in daemon_yaml
    assert "DBT_PROJECT_DIR:" not in daemon_yaml
    assert "../:/app" in daemon_yaml

"""Integration tests for phlo-dagster."""

from types import SimpleNamespace
from typing import cast

import pytest
from dagster import AssetExecutionContext, Definitions, asset, materialize

pytestmark = pytest.mark.integration


def test_dagster_definitions_load():
    """Test that Dagster Definitions can be instantiated."""
    # Basic Definitions object creation
    defs = Definitions(assets=[], resources={})
    assert isinstance(defs, Definitions)


def test_dagster_asset_materialization():
    """Test that a simple asset can be materialized without external services."""

    @asset
    def test_asset():
        """Return a deterministic payload for materialization verification."""
        return {"value": 42}

    # Materialize the asset
    result = materialize([test_asset])

    assert result.success
    # Verify the asset output
    output = result.output_for_node("test_asset")
    assert output == {"value": 42}


def test_phlo_dagster_partitions():
    """Test that phlo_dagster partitions are properly configured."""
    from phlo_dagster.partitions import daily_partition

    assert daily_partition is not None
    assert daily_partition.timezone == "Europe/London"

    # Verify partitions are generated correctly
    partitions = list(daily_partition.get_partition_keys())
    assert len(partitions) > 0
    # First partition should be 2025-01-01
    assert partitions[0] == "2025-01-01"


def test_phlo_dagster_plugin_metadata():
    """Test that phlo-dagster plugin provides correct metadata."""
    from phlo_dagster.plugin import DagsterServicePlugin, DagsterDaemonServicePlugin

    # Test main plugin
    plugin = DagsterServicePlugin()
    assert plugin.metadata.name == "dagster"
    assert "orchestration" in plugin.metadata.tags

    # Test daemon plugin
    daemon_plugin = DagsterDaemonServicePlugin()
    assert daemon_plugin.metadata.name == "dagster-daemon"


def test_phlo_dagster_service_definition():
    """Test that service definitions can be loaded."""
    from phlo_dagster.plugin import DagsterServicePlugin

    plugin = DagsterServicePlugin()
    service_def = plugin.service_definition

    assert isinstance(service_def, dict)
    assert "services" in service_def or "service" in service_def or "name" in service_def


def test_dagster_with_phlo_iceberg_resource():
    """Test Dagster integration with IcebergResource."""
    try:
        from phlo_iceberg.resource import IcebergResource
    except ImportError:
        pytest.skip("phlo-iceberg not installed")

    # Just verify the resource can be instantiated
    # We don't actually connect to a catalog here
    iceberg = IcebergResource()
    assert iceberg is not None


def test_phlo_dagster_version():
    """Test that phlo-dagster has proper version."""
    import phlo_dagster

    assert hasattr(phlo_dagster, "__version__")
    assert phlo_dagster.__version__ == "0.1.1"


def test_dagster_runtime_reads_run_tags_when_context_has_no_tags():
    """DagsterRuntime should support contexts exposing run-level tags only."""
    from phlo_dagster.adapter import DagsterRuntime

    context = SimpleNamespace(
        run=SimpleNamespace(tags={"dbt_target": "ci"}),
        run_id="abc123",
        has_partition_key=False,
        log=SimpleNamespace(),
        resources=SimpleNamespace(),
    )

    runtime = DagsterRuntime(context=cast(AssetExecutionContext, context))
    assert runtime.tags == {"dbt_target": "ci"}


def test_materialize_result_failure_status_fails_step():
    """Failure statuses from capability assets must fail Dagster runs."""
    from phlo.capabilities import AssetSpec, MaterializeResult, RunSpec
    from phlo_dagster.adapter import DagsterOrchestratorAdapter

    def _run(_runtime):
        """Emit a failure materialize result for adapter failure-path testing."""
        return [MaterializeResult(status="failure", metadata={"reason": "boom"})]

    adapter = DagsterOrchestratorAdapter()
    asset_def = adapter._build_asset(
        AssetSpec(key="failure_asset", group=None, description=None, run=RunSpec(fn=_run))
    )
    result = materialize([asset_def], raise_on_error=False)

    assert not result.success

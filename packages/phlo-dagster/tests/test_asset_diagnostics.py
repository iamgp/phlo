"""Tests for duplicate Dagster asset diagnostics."""

from __future__ import annotations

from typing import Any

import dagster as dg
import pytest

from phlo.capabilities import AssetSpec, MaterializeResult, RunSpec
from phlo.exceptions import PhloDiscoveryError
from phlo_dagster.adapter import DagsterOrchestratorAdapter
from phlo_dagster.framework.asset_diagnostics import merge_definitions_with_duplicate_diagnostics


def _run(_context: Any) -> list[MaterializeResult]:
    return [MaterializeResult(metadata={}, status="success")]


def test_duplicate_asset_specs_include_key_and_metadata_origins() -> None:
    adapter = DagsterOrchestratorAdapter()
    assets = [
        AssetSpec(
            key="warehouse.orders",
            group=None,
            description=None,
            metadata={
                "provider": "dbt",
                "module": "workflows.transforms.orders",
                "file": "workflows/transforms/orders.py",
            },
            run=RunSpec(fn=_run),
        ),
        AssetSpec(
            key="warehouse.orders",
            group=None,
            description=None,
            metadata={
                "provider": "sling",
                "module": "workflows.ingestion.orders",
                "file": "workflows/ingestion/orders.py",
            },
            run=RunSpec(fn=_run),
        ),
    ]

    with pytest.raises(PhloDiscoveryError) as exc_info:
        adapter.build_definitions(assets=assets, checks=[], resources=[])

    message = str(exc_info.value)
    assert "Duplicate Dagster asset key discovered: warehouse.orders" in message
    assert "provider=dbt" in message
    assert "module=workflows.transforms.orders" in message
    assert "file=workflows/transforms/orders.py" in message
    assert "provider=sling" in message
    assert "module=workflows.ingestion.orders" in message
    assert "file=workflows/ingestion/orders.py" in message
    assert "auto-discovery" in message
    assert "explicit Dagster Definitions" in message
    assert "Rely on Phlo auto-discovery" in message


def test_duplicate_definition_assets_include_object_origins() -> None:
    @dg.asset(key=["warehouse", "orders"])
    def auto_discovered_orders() -> int:
        return 1

    @dg.asset(key=["warehouse", "orders"])
    def explicit_orders() -> int:
        return 1

    with pytest.raises(PhloDiscoveryError) as exc_info:
        merge_definitions_with_duplicate_diagnostics(
            dg.Definitions(assets=[auto_discovered_orders]),
            dg.Definitions(assets=[explicit_orders]),
        )

    message = str(exc_info.value)
    assert "Duplicate Dagster asset key discovered: warehouse.orders" in message
    assert "object=auto_discovered_orders" in message
    assert "object=explicit_orders" in message
    assert "test_asset_diagnostics.py" in message
    assert "auto-discovery" in message
    assert "explicit Dagster Definitions" in message


def test_asset_check_definition_does_not_break_asset_duplicate_diagnostics() -> None:
    @dg.asset(key=["warehouse", "orders"])
    def orders() -> int:
        return 1

    @dg.asset_check(asset=orders, blocking=True)
    def orders_ready() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    merged = merge_definitions_with_duplicate_diagnostics(
        dg.Definitions(assets=[orders]),
        # The module collector passes checks via ``assets``. Dagster then
        # exposes the AssetChecksDefinition in Definitions.assets as well.
        dg.Definitions(assets=[orders_ready]),
    )

    assert merged.resolve_asset_graph().get_all_asset_keys() == {
        dg.AssetKey(["warehouse", "orders"])
    }

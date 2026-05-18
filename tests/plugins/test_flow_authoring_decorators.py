"""Tests for terse flow authoring decorators."""

from __future__ import annotations

import importlib
import sys

import pytest

from phlo.contracts import SLA, Consumer

pytestmark = pytest.mark.core_regression


def test_transform_sql_registers_provider_neutral_asset() -> None:
    """SQL transforms should register asset specs with the returned SQL text."""
    import phlo

    transform = importlib.import_module("phlo.transform")
    transform.clear_transform_assets()

    @phlo.transform.sql(
        table="silver.orders",
        depends_on=["bronze.orders"],
        materialized="incremental",
        owner="data-platform",
        consumers=[Consumer(name="analytics")],
        sla=SLA(freshness_hours=4),
    )
    def orders_sql() -> str:
        return "select * from bronze.orders"

    assets = transform.get_transform_assets()

    assert orders_sql() == "select * from bronze.orders"
    assert len(assets) == 1
    assert assets[0].key == "transform_silver_orders"
    assert assets[0].deps == ["bronze.orders"]
    assert assets[0].kinds == {"sql", "transform"}
    assert assets[0].tags == {
        "asset_type": "transform",
        "provider": "core",
        "transform_type": "sql",
        "materialized": "incremental",
    }
    assert assets[0].metadata["table"] == "silver.orders"
    assert assets[0].metadata["sql"] == "select * from bronze.orders"
    assert assets[0].metadata["owner"] == "data-platform"
    assert assets[0].metadata["consumers"] == [
        {"name": "analytics", "contact": None, "usage": None}
    ]
    assert assets[0].metadata["sla"] == {
        "freshness_hours": 4,
        "quality_threshold": 1.0,
        "max_failures": None,
        "notify": None,
    }


def test_publish_registers_data_product_surface() -> None:
    """Publish should mark curated tables as data-product surfaces."""
    import phlo

    phlo.clear_publish_assets()

    @phlo.publish(
        table="gold.customer_health",
        audience=["cs", "sales"],
        owner="revops",
        freshness_hours=6,
        depends_on=["silver.customers"],
    )
    def customer_health() -> str:
        return "gold.customer_health"

    assets = phlo.get_publish_assets()

    assert customer_health() == "gold.customer_health"
    assert len(assets) == 1
    assert assets[0].key == "publish_gold_customer_health"
    assert assets[0].deps == ["silver.customers"]
    assert assets[0].kinds == {"publish", "data_product"}
    assert assets[0].tags["asset_type"] == "publish"
    assert assets[0].metadata["table"] == "gold.customer_health"
    assert assets[0].metadata["audience"] == ["cs", "sales"]
    assert assets[0].metadata["freshness_hours"] == 6
    assert assets[0].metadata["owner"] == "revops"


def test_observe_registers_operational_check_surface() -> None:
    """Observe should register operational health checks separately from quality rules."""
    import phlo

    phlo.clear_observe_assets()

    @phlo.observe(
        table="bronze.events",
        freshness_hours=2,
        row_count_change={"warn": 0.3, "fail": 0.6},
        depends_on=["bronze.events"],
    )
    def events_observability() -> None:
        return None

    assets = phlo.get_observe_assets()

    assert events_observability() is None
    assert len(assets) == 1
    assert assets[0].key == "observe_bronze_events"
    assert assets[0].deps == ["bronze.events"]
    assert assets[0].kinds == {"observe", "operational_check"}
    assert assets[0].tags["asset_type"] == "observe"
    assert assets[0].metadata["table"] == "bronze.events"
    assert assets[0].metadata["freshness_hours"] == 2
    assert assets[0].metadata["row_count_change"] == {"warn": 0.3, "fail": 0.6}
    assert [check.name for check in assets[0].checks] == [
        "freshness_hours",
        "row_count_change",
    ]


def test_backfill_registers_repeatable_backfill_job() -> None:
    """Backfill should capture partition window and write policy metadata."""
    import phlo

    phlo.clear_backfill_assets()

    @phlo.backfill(
        target="silver.orders",
        partitions={"start": "2026-01-01", "end": "2026-03-31"},
        mode="replace-partitions",
        depends_on=["bronze.orders"],
    )
    def orders_q1_backfill() -> str:
        return "orders_sql"

    assets = phlo.get_backfill_assets()

    assert orders_q1_backfill() == "orders_sql"
    assert len(assets) == 1
    assert assets[0].key == "backfill_silver_orders"
    assert assets[0].deps == ["bronze.orders"]
    assert assets[0].kinds == {"backfill"}
    assert assets[0].tags["asset_type"] == "backfill"
    assert assets[0].metadata["target"] == "silver.orders"
    assert assets[0].metadata["partitions"] == {
        "start": "2026-01-01",
        "end": "2026-03-31",
    }
    assert assets[0].metadata["mode"] == "replace-partitions"


def test_top_level_exports_lazy_load_new_authoring_surfaces() -> None:
    """Top-level phlo exports should expose the new decorators lazily."""
    import phlo

    for name in [
        "phlo.transform",
        "phlo.publish",
        "phlo.observe",
        "phlo.backfill",
    ]:
        sys.modules.pop(name, None)

    assert callable(phlo.publish)
    assert callable(phlo.observe)
    assert callable(phlo.backfill)
    assert callable(phlo.transform.sql)

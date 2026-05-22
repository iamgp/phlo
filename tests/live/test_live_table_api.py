import pytest

import phlo
from phlo.live import clear_live_tables, get_live_tables, plan_live_tables


@pytest.fixture(autouse=True)
def clean_live_tables() -> None:
    clear_live_tables()
    yield
    clear_live_tables()


def test_live_table_decorator_records_managed_table_spec() -> None:
    @phlo.live_table(
        name="silver.orders",
        query="select * from bronze.orders",
        sources=["bronze.orders"],
        target_lag="15 minutes",
        mode="incremental",
        quality=["not_null:order_id"],
    )
    def silver_orders() -> None:
        return None

    spec = get_live_tables()[0]

    assert spec.name == "silver.orders"
    assert spec.query == "select * from bronze.orders"
    assert spec.sources == ("bronze.orders",)
    assert spec.target_lag == "15 minutes"
    assert spec.mode == "incremental"
    assert spec.quality == ("not_null:order_id",)
    assert spec.fn is silver_orders


def test_live_table_rejects_invalid_mode() -> None:
    try:
        phlo.live_table(name="silver.orders", query="select 1", mode="streaming")
    except ValueError as exc:
        assert "Unsupported live table mode: streaming" in str(exc)
    else:
        raise AssertionError("Expected invalid mode to fail")


def test_plan_live_tables_orders_dependencies() -> None:
    clear_live_tables()

    @phlo.live_table(name="bronze.orders", query="select 1", mode="full")
    def bronze_orders() -> None:
        return None

    @phlo.live_table(
        name="silver.orders",
        query="select * from bronze.orders",
        sources=["bronze.orders"],
    )
    def silver_orders() -> None:
        return None

    plan = plan_live_tables()

    assert [item["name"] for item in plan] == ["bronze.orders", "silver.orders"]


def test_plan_live_tables_rejects_missing_source() -> None:
    clear_live_tables()

    @phlo.live_table(
        name="silver.orders",
        query="select * from bronze.orders",
        sources=["bronze.orders"],
    )
    def silver_orders() -> None:
        return None

    try:
        plan_live_tables()
    except ValueError as exc:
        assert "silver.orders depends on unknown live table source bronze.orders" in str(exc)
    else:
        raise AssertionError("Expected missing source to fail")


def test_plan_live_tables_rejects_duplicate_names() -> None:
    @phlo.live_table(name="silver.orders", query="select 1")
    def silver_orders_v1() -> None:
        return None

    @phlo.live_table(name="silver.orders", query="select 2")
    def silver_orders_v2() -> None:
        return None

    assert [spec.fn for spec in get_live_tables()] == [silver_orders_v1, silver_orders_v2]

    try:
        plan_live_tables()
    except ValueError as exc:
        assert "Duplicate live table declarations: silver.orders" in str(exc)
    else:
        raise AssertionError("Expected duplicate live table names to fail")

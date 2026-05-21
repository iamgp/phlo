import pytest

import phlo
from phlo.live import clear_live_tables, get_live_tables


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

"""Tests for hook bus behavior."""

import pytest

from phlo.hooks import QualityResultEvent
from phlo.plugins.hooks import FailurePolicy, HookFilter, HookRegistration
from phlo_testing.hooks import MockHookBus


def test_hook_bus_filters_and_ordering() -> None:
    bus = MockHookBus()
    calls: list[str] = []

    def handler_a(_event) -> None:
        calls.append("a")

    def handler_b(_event) -> None:
        calls.append("b")

    bus.register(
        HookRegistration(
            hook_name="handler_a",
            handler=handler_a,
            priority=10,
            filters=HookFilter(event_types={"quality.result"}, asset_keys={"asset"}),
        ),
        plugin_name="plugin_a",
    )
    bus.register(
        HookRegistration(
            hook_name="handler_b",
            handler=handler_b,
            priority=5,
            filters=HookFilter(event_types={"quality.result"}),
        ),
        plugin_name="plugin_b",
    )

    event = QualityResultEvent(
        event_type="quality.result",
        asset_key="asset",
        check_name="null_check",
        passed=True,
    )
    bus.emit(event)
    assert calls == ["b", "a"]


def test_hook_bus_failure_policy_raise() -> None:
    bus = MockHookBus()

    def handler(_event) -> None:
        raise RuntimeError("boom")

    bus.register(
        HookRegistration(
            hook_name="raise_hook",
            handler=handler,
            failure_policy=FailurePolicy.RAISE,
        ),
        plugin_name="plugin_raise",
    )

    event = QualityResultEvent(
        event_type="quality.result",
        asset_key="asset",
        check_name="null_check",
        passed=False,
    )

    with pytest.raises(RuntimeError, match="boom"):
        bus.emit(event)

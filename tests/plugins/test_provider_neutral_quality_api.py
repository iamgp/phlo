"""Tests for provider-neutral quality public API."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.core_regression


def test_quality_rule_factories_are_provider_neutral() -> None:
    """Top-level rule helpers should return QualityRule descriptors without provider imports."""
    import phlo
    from phlo.helpers.quality import QualityRule

    rules = [
        phlo.not_null("id", "email"),
        phlo.unique("id"),
        phlo.freshness("updated_at", hours=24),
        phlo.range_between("score", min_value=0, max_value=100),
        phlo.accepted_values("status", ["active", "paused"]),
    ]

    assert all(isinstance(rule, QualityRule) for rule in rules)
    assert rules[0].kind == "not_null"
    assert rules[0].columns == ["id", "email"]
    assert rules[1].kind == "unique"
    assert rules[2].parameters == {"max_age_hours": 24}
    assert rules[3].parameters == {"min_value": 0, "max_value": 100}
    assert rules[4].parameters == {"values": ["active", "paused"]}

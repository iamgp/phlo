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


def test_pandera_quality_provider_builds_checks_from_neutral_rules() -> None:
    """Pandera provider should translate supported neutral rules into Pandera checks."""
    from phlo_pandera.checks import FreshnessCheck, NullCheck, RangeCheck, UniqueCheck
    from phlo_pandera.plugin import PanderaQualityProvider

    from phlo.helpers.quality import QualityRule

    provider = PanderaQualityProvider()
    checks = provider.build_checks_from_rules(
        [
            QualityRule("not_null", ["id", "email"], {}),
            QualityRule("unique", ["id"], {}),
            QualityRule("freshness", ["updated_at"], {"max_age_hours": 24}),
            QualityRule("range", ["score"], {"min_value": 0, "max_value": 100}),
        ]
    )

    assert [type(check) for check in checks] == [
        NullCheck,
        UniqueCheck,
        FreshnessCheck,
        RangeCheck,
    ]


def test_pandera_quality_provider_rejects_unknown_neutral_rule() -> None:
    """Unknown neutral rules should fail during decoration, not at runtime."""
    from phlo_pandera.plugin import PanderaQualityProvider

    from phlo.helpers.quality import QualityRule

    provider = PanderaQualityProvider()

    with pytest.raises(ValueError) as exc_info:
        provider.build_checks_from_rules([QualityRule("mystery", ["id"], {})])

    assert "Unsupported neutral quality rule: mystery" in str(exc_info.value)

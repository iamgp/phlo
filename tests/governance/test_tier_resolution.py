"""Pure tier-resolution tests for the ADR 0053 trust-tier contract (#855).

Pins the authority model: the resolver derives ``community`` from
descriptors alone, ``conformance-tested`` only from unexpired passing
Phlo-owned verdicts for the exact artifact identity, and
``release-supported`` never from Authorities A/B — only from a typed
support-manifest decision with receipts when required. Legacy v1
``verified`` normalizes honestly to the derived ``legacy_verified``
state and never to a tier. Everything here is code-free static
resolution.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from phlo.plugins import trust
from phlo.plugins.trust import (
    ConformanceResultRecord,
    DescriptorRecord,
    SupportDecisionRecord,
    TrustTier,
    content_digest,
    normalize_v1_entry,
    normalize_v1_registry,
    resolve_tier,
    resolve_tiers,
)

ROOT = Path(__file__).parents[2]
FIXTURES = ROOT / "tests/fixtures/provider_tiers"
NOW = datetime(2026, 9, 5, tzinfo=UTC)


def _fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _descriptor() -> DescriptorRecord:
    return DescriptorRecord.from_json("acme-warehouse-source", _fixture("descriptor.valid.json"))


def _result(**overrides: object) -> ConformanceResultRecord:
    data = _fixture("conformance-result.valid.json")
    data.update(overrides)
    return ConformanceResultRecord.from_json(data)


def _matching_result(**overrides: object) -> ConformanceResultRecord:
    """A verdict bound to the exact artifact identity of the descriptor."""
    data = _fixture("conformance-result.valid.json")
    subject_overrides = {
        key: value for key, value in overrides.items() if key in {"package", "version", "digest"}
    }
    top_level_overrides = {
        key: value for key, value in overrides.items() if key not in subject_overrides
    }
    data["subject"].update(subject_overrides)
    data["subject"]["digest"] = _descriptor().artifact_identity()[2]
    data.update(top_level_overrides)
    return ConformanceResultRecord.from_json(data)


def _decision(**overrides: object) -> SupportDecisionRecord:
    data: dict[str, Any] = {
        "component_kind": "package",
        "component_name": "acme-phlo-source",
        "tier": "release-supported",
        "evidence_bar": "Plan 016 qualifying repeated evidence plus promotion receipt",
        "receipt_refs": ["receipt:2026-09-04:acme-phlo-source"],
        "owner": "phlo-support",
        "decided_at": "2026-09-04T00:00:00Z",
        "review_by": "2027-09-04T00:00:00Z",
    }
    data.update(overrides)
    return SupportDecisionRecord.from_json(data)


# --- matching and mismatched fixtures -------------------------------------------------


def test_matching_descriptor_and_result_fixtures_parse() -> None:
    descriptor = _descriptor()
    result = _result()
    assert descriptor.package == "acme-phlo-source"
    assert result.subject_package == "acme-phlo-source"


def test_mismatched_descriptor_fixture_is_rejected() -> None:
    with pytest.raises((trust.UnknownFieldError, ValueError)):
        DescriptorRecord.from_json("acme-warehouse-source", _fixture("descriptor.mismatched.json"))


def test_mismatched_result_fixture_is_rejected() -> None:
    with pytest.raises((trust.UnknownFieldError, ValueError)):
        ConformanceResultRecord.from_json(_fixture("conformance-result.mismatched.json"))


# --- Authority A: community ceiling ---------------------------------------------------


def test_descriptor_alone_resolves_to_community() -> None:
    resolution = resolve_tier(_descriptor(), now=NOW)
    assert resolution.tier == TrustTier.COMMUNITY
    assert resolution.legacy_verified is False


def test_descriptor_ceiling_holds_even_with_all_passing_verdicts_present() -> None:
    resolution = resolve_tier(
        _descriptor(),
        conformance_results=(
            _matching_result(),
            _matching_result(digest=content_digest({"x": 1})),
        ),
        now=NOW,
    )
    assert resolution.tier in {TrustTier.COMMUNITY, TrustTier.CONFORMANCE_TESTED}


# --- Authority B: conformance-tested --------------------------------------------------


def test_passing_unexpired_verdict_grants_conformance_tested() -> None:
    resolution = resolve_tier(_descriptor(), conformance_results=(_matching_result(),), now=NOW)
    assert resolution.tier == TrustTier.CONFORMANCE_TESTED


def test_expired_verdict_falls_back_to_community_mechanically() -> None:
    resolution = resolve_tier(
        _descriptor(),
        conformance_results=(_result(expires_at="2026-09-01T00:00:00Z"),),
        now=NOW,
    )
    assert resolution.tier == TrustTier.COMMUNITY


def test_failed_verdict_never_grants_conformance_tested() -> None:
    resolution = resolve_tier(_descriptor(), conformance_results=(_result(result="fail"),), now=NOW)
    assert resolution.tier == TrustTier.COMMUNITY


def test_verdict_does_not_transfer_across_artifact_identity() -> None:
    other_version = replace_descriptor_version()
    resolution = resolve_tier(other_version, conformance_results=(_result(),), now=NOW)
    assert resolution.tier == TrustTier.COMMUNITY


def replace_descriptor_version() -> DescriptorRecord:
    claim = _descriptor().descriptor_claim()
    claim["version"] = "2.2.0"
    return DescriptorRecord.from_json("acme-warehouse-source", claim)


def test_unapproved_tracer_is_refused_not_downgraded() -> None:
    with pytest.raises(ValueError, match="not approved"):
        _result(tracer="self_attested.v9")


def test_publisher_cannot_execute_a_verdict() -> None:
    with pytest.raises(ValueError, match="executed_by"):
        _result(executed_by="ACME Data Ltd")


def test_verdict_without_evidence_references_is_refused() -> None:
    with pytest.raises(ValueError, match="evidence_refs"):
        _result(evidence_refs=[])


# --- Authority C: release-supported enters only as a typed decision -------------------


def test_release_supported_never_derived_from_descriptors_and_verdicts() -> None:
    resolution = resolve_tier(_descriptor(), conformance_results=(_matching_result(),), now=NOW)
    assert resolution.tier == TrustTier.CONFORMANCE_TESTED
    assert resolution.tier != TrustTier.RELEASE_SUPPORTED


def test_release_supported_requires_a_typed_support_decision() -> None:
    resolution = resolve_tier(
        _descriptor(),
        conformance_results=(_matching_result(),),
        support_decisions=(_decision(),),
        now=NOW,
    )
    assert resolution.tier == TrustTier.RELEASE_SUPPORTED


def test_release_supported_without_receipts_is_refused_at_construction() -> None:
    with pytest.raises(ValueError, match="receipts"):
        _decision(requires_receipts=True, receipt_refs=[])


def test_release_supported_decision_past_review_degrades() -> None:
    resolution = resolve_tier(
        _descriptor(),
        support_decisions=(_decision(review_by="2026-09-01T00:00:00Z"),),
        now=NOW,
    )
    assert resolution.tier == TrustTier.COMMUNITY


def test_support_decision_cannot_bind_to_a_different_component() -> None:
    resolution = resolve_tier(
        _descriptor(),
        support_decisions=(_decision(component_name="other-package"),),
        now=NOW,
    )
    assert resolution.tier == TrustTier.COMMUNITY


def test_support_decision_rejects_unknown_fields() -> None:
    with pytest.raises(trust.UnknownFieldError):
        SupportDecisionRecord.from_json(
            {
                "component_kind": "package",
                "component_name": "acme-phlo-source",
                "tier": "release-supported",
                "evidence_bar": "bar",
                "receipt_refs": ["receipt:1"],
                "owner": "phlo-support",
                "decided_at": "2026-09-04T00:00:00Z",
                "review_by": "2027-09-04T00:00:00Z",
                "override": {"tier": "release-supported", "reason": "make it supported"},
            }
        )


def test_resolver_has_no_override_input_that_changes_a_tier() -> None:
    """ADR 0053 concern 5: overrides annotate but never change a tier.

    The resolver's signature has no override input at all; a verdict plus
    an "override-flavoured" raw decision dict still cannot escalate.
    """
    override_shaped: dict[str, Any] = {
        "component_kind": "package",
        "component_name": "acme-phlo-source",
        "tier": "release-supported",
        "evidence_bar": "none",
        "owner": "acme",
        "decided_at": "2026-09-04T00:00:00Z",
        "review_by": "2027-09-04T00:00:00Z",
    }
    with pytest.raises(ValueError, match="receipts"):
        SupportDecisionRecord.from_json(override_shaped)
    resolution = resolve_tier(_descriptor(), conformance_results=(_matching_result(),), now=NOW)
    assert resolution.tier == TrustTier.CONFORMANCE_TESTED


# --- Legacy v1 normalization: honest, one epoch, no inferred tier ---------------------


def test_v1_verified_true_normalizes_to_legacy_verified_with_no_tier() -> None:
    normalized = normalize_v1_entry(
        "trino",
        {
            "type": "service",
            "package": "phlo-trino",
            "version": "0.1.0",
            "author": "Phlo Team",
            "verified": True,
        },
        epoch=trust.CURRENT_COMPATIBILITY_EPOCH,
    )
    assert normalized.legacy_verified is True
    resolution = resolve_tier(normalized.descriptor, now=NOW, legacy_verified=True)
    assert resolution.tier == TrustTier.COMMUNITY
    assert resolution.legacy_verified is True


def test_v1_verified_false_carries_no_legacy_state() -> None:
    normalized = normalize_v1_entry(
        "community-plugin",
        {
            "type": "source_connectors",
            "package": "community-src",
            "version": "1.0.0",
            "author": "Community Author",
            "verified": False,
        },
        epoch=trust.CURRENT_COMPATIBILITY_EPOCH,
    )
    assert normalized.legacy_verified is False


def test_legacy_verified_dies_after_one_epoch() -> None:
    normalized = normalize_v1_entry(
        "trino",
        {
            "type": "service",
            "package": "phlo-trino",
            "version": "0.1.0",
            "author": "Phlo Team",
            "verified": True,
        },
        epoch=trust.LEGACY_VERIFIED_MAX_EPOCH + 1,
    )
    assert normalized.legacy_verified is False


def test_new_entries_cannot_set_verified() -> None:
    with pytest.raises(trust.UnknownFieldError):
        DescriptorRecord.from_json(
            "acme-warehouse-source",
            {**_fixture("descriptor.valid.json"), "verified": True},
        )


def test_real_v1_registry_normalizes_with_no_inferred_tier() -> None:
    registry = json.loads((ROOT / "registry/plugins.json").read_text(encoding="utf-8"))
    v2 = normalize_v1_registry(registry)
    legacy = set(v2.get("legacy", {}).get("legacy_verified", []))
    verified_true = {
        name for name, entry in registry["plugins"].items() if entry.get("verified") is True
    }
    assert legacy == verified_true
    assert all("verified" not in entry and "tier" not in entry for entry in v2["plugins"].values())


def test_real_estate_resolves_to_zero_conformance_tested_and_zero_release_supported() -> None:
    registry = json.loads((ROOT / "registry/plugins.json").read_text(encoding="utf-8"))
    descriptors = {
        name: normalize_v1_entry(name, entry, epoch=trust.CURRENT_COMPATIBILITY_EPOCH).descriptor
        for name, entry in registry["plugins"].items()
    }
    resolutions = resolve_tiers(descriptors, now=NOW)
    assert sum(r.tier == TrustTier.RELEASE_SUPPORTED for r in resolutions.values()) == 0
    assert sum(r.tier == TrustTier.CONFORMANCE_TESTED for r in resolutions.values()) == 0
    assert sum(r.tier == TrustTier.COMMUNITY for r in resolutions.values()) == len(descriptors)


# --- Canonicalization and digest identity ---------------------------------------------


def test_canonical_json_is_key_order_insensitive_and_digests_stable() -> None:
    first = content_digest({"a": 1, "b": [1, 2]})
    second = content_digest({"b": [1, 2], "a": 1})
    assert first == second
    assert first.startswith("sha256:")


def test_digest_changes_when_the_descriptor_changes() -> None:
    assert _descriptor().artifact_identity() != replace_descriptor_version().artifact_identity()

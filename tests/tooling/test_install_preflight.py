"""Pre-install preflight decision matrix (issue #857, ADR 0053).

Builds real candidate wheels and proves the one pure decision shared by
the CLI and Observatory mutation paths: the exact conformance-tested
artifact is accepted; a compatible community artifact requires an
explicit override and remains community; malformed, digest-mismatched,
core-incompatible, and capability-incompatible candidates are rejected
even with an override; ``legacy_verified`` authorizes nothing. The
preflight never imports or executes provider code.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from phlo.plugins.preflight import (
    CAPABILITY_INCOMPATIBLE,
    CORE_INCOMPATIBLE,
    DIGEST_MISMATCH,
    EVIDENCE,
    MALFORMED,
    POLICY,
    PreflightDecision,
    ProjectRequirementError,
    evaluate_install_preflight,
    read_project_requirements,
)
from phlo.plugins.trust import TrustTier

ROOT = Path(__file__).parents[2]
CORE_VERSION = "0.14.0"
NOW = datetime(2026, 9, 4, tzinfo=UTC)

PROJECT_CONFIG = {
    "capabilities": {"defaults": {"query_engine": "preflight-fixture"}},
}


def _core_pin() -> str:
    major, minor = CORE_VERSION.split(".")[:2]
    return f"phlo>={CORE_VERSION},<{major}.{int(minor) + 1}"


_PROVIDER_TEMPLATE = """\
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "phlo-preflight-fixture"
version = "0.1.0"
description = "Pre-install preflight fixture (not part of the Phlo estate)"
requires-python = ">=3.11"
dependencies = [{core_pin}]

{entry_points}
[tool.setuptools]
py-modules = ["preflight_fixture_module"]
"""

_ENTRY_POINTS = '[project.entry-points."phlo.plugins.resources"]\nfixture = "preflight_fixture_module:Provider"\n'

_MODULE = "VALUE = 1\n"


def _write_provider_project(directory: Path, *, core_pin: str | None, entry_points: bool) -> Path:
    project_dir = directory / "provider"
    src = project_dir / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "preflight_fixture_module.py").write_text(_MODULE, encoding="utf-8")
    (project_dir / "pyproject.toml").write_text(
        _PROVIDER_TEMPLATE.format(
            core_pin=f'"{core_pin}"' if core_pin else "",
            entry_points=_ENTRY_POINTS if entry_points else "",
        ),
        encoding="utf-8",
    )
    return project_dir


def _build_wheel(project_dir: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    commands = [
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--no-build-isolation",
            "-w",
            str(out_dir),
            str(project_dir),
        ],
        [
            "uv",
            "build",
            "--wheel",
            "--no-build-isolation",
            "--out-dir",
            str(out_dir),
            str(project_dir),
        ],
        [
            "python3",
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--no-build-isolation",
            "-w",
            str(out_dir),
            str(project_dir),
        ],
    ]
    errors: list[str] = []
    for command in commands:
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, check=False, timeout=300
            )
        except FileNotFoundError as exc:
            errors.append(f"{command[0]}: {exc}")
            continue
        if result.returncode == 0:
            wheels = list(out_dir.glob("*.whl"))
            assert len(wheels) == 1, f"expected one wheel, found {wheels}"
            return wheels[0]
        errors.append(result.stderr or result.stdout)
    pytest.skip(f"no wheel builder available (tried pip, uv, python3-pip): {errors}")


@pytest.fixture(scope="module")
def wheels(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Good, old-core, and no-entry-point candidate wheels, built offline."""
    out = tmp_path_factory.mktemp("preflight-wheels")
    built: dict[str, Path] = {}
    variants = {
        "good": {"core_pin": _core_pin(), "entry_points": True},
        "oldcore": {"core_pin": "phlo>=0.0.1,<0.2", "entry_points": True},
        "noentry": {"core_pin": _core_pin(), "entry_points": False},
    }
    for name, kwargs in variants.items():
        project_dir = _write_provider_project(out / name, **kwargs)
        built[name] = _build_wheel(project_dir, out / name)
    return built


def _descriptor() -> dict[str, Any]:
    return {
        "type": "resource",
        "package": "phlo-preflight-fixture",
        "version": "0.1.0",
        "description": "Preflight fixture provider",
        "author": "Preflight Fixture Author",
        "tags": ["fixture"],
    }


def _evidence(wheel: Path, *, result: str = "pass", expires: str = "2026-12-01T00:00:00Z") -> dict:
    digest = f"sha256:{hashlib.sha256(wheel.read_bytes()).hexdigest()}"
    return {
        "subject": {"package": "phlo-preflight-fixture", "version": "0.1.0", "digest": digest},
        "tracer": "query_engine.v1",
        "result": result,
        "evidence_refs": ["evidence:conformance:preflight-fixture-1"],
        "executed_by": "phlo-conformance",
        "run_at": "2026-09-01T00:00:00Z",
        "expires_at": expires,
    }


_MISSING = object()


def _decide(
    wheels: dict[str, Path],
    *,
    descriptor: dict[str, Any] | None | object = _MISSING,
    artifact: Path | None = None,
    evidence: tuple[dict, ...] = (),
    project_requirements: Any = None,
    override_reason: str | None = None,
    legacy_verified: bool = False,
    core_version: str | None = CORE_VERSION,
) -> PreflightDecision:
    from phlo.plugins.trust import ConformanceResultRecord

    records = tuple(ConformanceResultRecord.from_json(item) for item in evidence)
    return evaluate_install_preflight(
        descriptor_data=_descriptor() if descriptor is _MISSING else descriptor,
        plugin_name="preflight-fixture",
        artifact=artifact,
        conformance_results=records,
        project_requirements=project_requirements
        if project_requirements is not None
        else read_project_requirements(PROJECT_CONFIG),
        override_reason=override_reason,
        legacy_verified=legacy_verified,
        now=NOW,
        core_version=core_version,
    )


# --- Accept / override / reject matrix -------------------------------------------------


def test_exact_conformance_tested_artifact_is_accepted(wheels: dict[str, Path]) -> None:
    """The exact artifact named by unexpired passing Phlo-owned evidence passes."""
    decision = _decide(wheels, artifact=wheels["good"], evidence=(_evidence(wheels["good"]),))
    assert decision.accepted
    assert decision.tier is TrustTier.CONFORMANCE_TESTED
    assert decision.failures == ()
    assert decision.artifact_digest is not None
    assert decision.matched_family == "query_engine"


def test_community_artifact_requires_explicit_override_and_stays_community(
    wheels: dict[str, Path],
) -> None:
    """A compatible community candidate needs the explicit override and never
    rises above community (ADR 0053 concern 5)."""
    without_override = _decide(wheels, artifact=wheels["good"])
    assert not without_override.accepted
    assert [failure.code for failure in without_override.failures] == [POLICY]
    assert without_override.failures[0].overridable
    assert without_override.required_tier is TrustTier.CONFORMANCE_TESTED

    with_override = _decide(wheels, artifact=wheels["good"], override_reason="team decision")
    assert with_override.accepted
    assert with_override.tier is TrustTier.COMMUNITY
    assert with_override.override_rule == "min_tier:query_engine"
    assert with_override.override_reason == "team decision"


def test_spec_candidate_below_bar_requires_override_and_spec_community_is_accepted(
    wheels: dict[str, Path],
) -> None:
    """Without an artifact the tier resolves honestly from the descriptor alone."""
    decision = _decide(wheels, artifact=None)
    assert not decision.accepted
    assert decision.tier is TrustTier.COMMUNITY
    assert decision.artifact_digest is None

    accepted = _decide(wheels, artifact=None, override_reason="explicit")
    assert accepted.accepted
    assert accepted.tier is TrustTier.COMMUNITY


def test_malformed_candidates_rejected_even_with_override(wheels: dict[str, Path]) -> None:
    """Unknown, invalid, and identity-mismatched candidates never pass."""
    unknown = _decide(wheels, descriptor=None, override_reason="no")
    assert not unknown.accepted
    assert [failure.code for failure in unknown.failures] == [MALFORMED]

    invalid = _decide(
        wheels,
        descriptor={**_descriptor(), "verified": True},
        artifact=wheels["good"],
        override_reason="no",
    )
    assert not invalid.accepted
    assert [failure.code for failure in invalid.failures] == [MALFORMED]

    mismatched_identity = _decide(
        wheels,
        descriptor={**_descriptor(), "version": "9.9.9"},
        artifact=wheels["good"],
        override_reason="no",
    )
    assert not mismatched_identity.accepted
    assert MALFORMED in [failure.code for failure in mismatched_identity.failures]


def test_digest_mismatched_variant_rejected_even_with_override(wheels: dict[str, Path]) -> None:
    """A rebuild of a conformance-tested version is a digest-mismatched variant."""
    other_build = {
        **_evidence(wheels["good"]),
        "subject": {
            "package": "phlo-preflight-fixture",
            "version": "0.1.0",
            "digest": "sha256:" + "ab" * 32,
        },
    }
    decision = _decide(
        wheels,
        artifact=wheels["good"],
        evidence=(other_build,),
        override_reason="no",
    )
    assert not decision.accepted
    assert DIGEST_MISMATCH in [failure.code for failure in decision.failures]
    assert all(not failure.overridable for failure in decision.failures)


def test_core_incompatible_rejected_even_with_override(wheels: dict[str, Path]) -> None:
    decision = _decide(wheels, artifact=wheels["oldcore"], override_reason="no")
    assert not decision.accepted
    assert CORE_INCOMPATIBLE in [failure.code for failure in decision.failures]
    assert all(not failure.overridable for failure in decision.failures)


def test_wheel_without_declared_core_posture_is_core_incompatible(
    wheels: dict[str, Path],
) -> None:
    """An undeclared core epoch is unknown, and unknown candidates never pass."""
    project_dir = wheels["noentry"].parent
    naked = _build_wheel(
        _write_provider_project(project_dir, core_pin=None, entry_points=True),
        project_dir / "out",
    )
    decision = _decide(wheels, artifact=naked, override_reason="no")
    assert not decision.accepted
    assert CORE_INCOMPATIBLE in [failure.code for failure in decision.failures]


def test_capability_incompatible_rejected_even_with_override(wheels: dict[str, Path]) -> None:
    """A candidate without the tracer's entry-point group cannot serve the family."""
    decision = _decide(wheels, artifact=wheels["noentry"], override_reason="no")
    assert not decision.accepted
    assert CAPABILITY_INCOMPATIBLE in [failure.code for failure in decision.failures]
    assert all(not failure.overridable for failure in decision.failures)


def test_failing_verdict_condemns_the_exact_artifact(wheels: dict[str, Path]) -> None:
    """A superseding failed verdict revokes the tier for the exact build (ADR 0053
    concern 6) and rejects the install even with an override."""
    decision = _decide(
        wheels,
        artifact=wheels["good"],
        evidence=(_evidence(wheels["good"], result="fail"),),
        override_reason="no",
    )
    assert not decision.accepted
    assert EVIDENCE in [failure.code for failure in decision.failures]
    assert all(not failure.overridable for failure in decision.failures)


def test_expired_verdict_decays_to_community_mechanically(wheels: dict[str, Path]) -> None:
    """Expiry is mechanical (ADR 0053 concern 6): the tier degrades to community
    and the install faces only the overridable policy bar."""
    decision = _decide(
        wheels,
        artifact=wheels["good"],
        evidence=(_evidence(wheels["good"], expires="2026-09-02T00:00:00Z"),),
    )
    assert not decision.accepted
    assert decision.tier is TrustTier.COMMUNITY
    assert [failure.code for failure in decision.failures] == [POLICY]


def test_legacy_verified_authorizes_nothing(wheels: dict[str, Path]) -> None:
    """``legacy_verified`` carries no trust claim beyond community (ADR 0053
    concern 5): it satisfies no evidence bar and needs the same override."""
    decision = _decide(wheels, artifact=wheels["good"], legacy_verified=True)
    assert not decision.accepted
    assert decision.tier is TrustTier.COMMUNITY
    assert decision.legacy_verified

    accepted = _decide(
        wheels, artifact=wheels["good"], legacy_verified=True, override_reason="explicit"
    )
    assert accepted.accepted
    assert accepted.tier is TrustTier.COMMUNITY


def test_safe_absent_default_is_community(wheels: dict[str, Path]) -> None:
    """Absent project requirements the bar is an honest community resolution."""
    from phlo.plugins.preflight import ProjectRequirements

    decision = _decide(
        wheels,
        artifact=wheels["good"],
        project_requirements=ProjectRequirements.empty(),
    )
    assert decision.accepted
    assert decision.required_tier is TrustTier.COMMUNITY
    assert decision.matched_family is None


def test_release_supported_only_via_typed_support_decision(wheels: dict[str, Path]) -> None:
    """``release-supported`` enters only as a typed Authority-C decision with
    receipts (ADR 0053 concerns 1 and 3) — never from the candidate itself."""
    from phlo.plugins.trust import SupportDecisionRecord

    demanding_config = {
        "capabilities": {"defaults": {"query_engine": "preflight-fixture"}},
        "plugins": {"trust": {"min_tier": {"query_engine": "release-supported"}}},
    }
    bare = _decide(
        wheels,
        artifact=wheels["good"],
        evidence=(_evidence(wheels["good"]),),
        project_requirements=read_project_requirements(demanding_config),
    )
    assert bare.required_tier is TrustTier.RELEASE_SUPPORTED
    assert not bare.accepted  # conformance-tested alone cannot satisfy the bar

    decision_payload = {
        "component_kind": "package",
        "component_name": "phlo-preflight-fixture",
        "tier": "release-supported",
        "evidence_bar": "plan-016 receipts",
        "receipt_refs": ["receipt:plan-016:1"],
        "owner": "phlo-support",
        "decided_at": "2026-09-01T00:00:00Z",
        "review_by": "2027-09-01T00:00:00Z",
        "requires_receipts": True,
    }
    with_decision = evaluate_install_preflight(
        descriptor_data=_descriptor(),
        plugin_name="preflight-fixture",
        artifact=wheels["good"],
        conformance_results=(),
        support_decisions=(SupportDecisionRecord.from_json(decision_payload),),
        project_requirements=read_project_requirements(demanding_config),
        now=NOW,
        core_version=CORE_VERSION,
    )
    assert with_decision.accepted
    assert with_decision.tier is TrustTier.RELEASE_SUPPORTED


# --- Strict project requirement reader -------------------------------------------------


def test_reader_accepts_the_documented_shape() -> None:
    requirements = read_project_requirements(
        {
            "capabilities": {"defaults": {"query_engine": "trino"}},
            "plugins": {"trust": {"min_tier": {"query_engine": "release-supported"}}},
        }
    )
    assert requirements.required_providers == {"query_engine": "trino"}
    assert requirements.required_tier("query_engine") is TrustTier.RELEASE_SUPPORTED
    assert requirements.required_tier("source") is TrustTier.COMMUNITY
    assert requirements.required_tier(None) is TrustTier.COMMUNITY


def test_reader_rejects_unknown_fields_and_malformed_values() -> None:
    with pytest.raises(ProjectRequirementError):
        read_project_requirements({"plugins": {"trust": {"tiers": {}}}})
    with pytest.raises(ProjectRequirementError):
        read_project_requirements({"plugins": {"tier": {}}})
    with pytest.raises(ProjectRequirementError):
        read_project_requirements({"capabilities": {"defaults": {"query_engine": 7}}})
    with pytest.raises(ProjectRequirementError):
        read_project_requirements({"capabilities": "nope"})


def test_reader_rejects_tier_synonyms_and_bar_lowering() -> None:
    with pytest.raises(ProjectRequirementError):
        read_project_requirements(
            {"plugins": {"trust": {"min_tier": {"query_engine": "verified"}}}}
        )
    with pytest.raises(ProjectRequirementError):
        read_project_requirements(
            {"plugins": {"trust": {"min_tier": {"query_engine": "community"}}}}
        )


def test_reader_refuses_conformance_tested_demand_without_an_approved_tracer() -> None:
    """The tracer enum is closed (ADR 0053 concern 7): demanding its verdict
    for a deferred family is unsatisfiable by construction and refused."""
    with pytest.raises(ProjectRequirementError):
        read_project_requirements(
            {"plugins": {"trust": {"min_tier": {"source": "conformance-tested"}}}}
        )


# --- Static boundary: no provider import or discovery ----------------------------------


def test_preflight_imports_no_provider_code(wheels: dict[str, Path], monkeypatch) -> None:
    """The decision is code-free (ADR 0053 concern 4): a guard module placed
    on the import path proves the candidate is never imported or discovered."""

    class _Guard:
        def find_module(self, fullname, path=None):  # noqa: D401 (legacy hook signature)
            return self if fullname.startswith("preflight_fixture") else None

        def find_spec(self, fullname, path=None, target=None):
            return self if fullname.startswith("preflight_fixture") else None

        def load_module(self, fullname):
            raise AssertionError(f"preflight imported provider code: {fullname}")

        def create_module(self, spec):  # pragma: no cover - never reached
            raise AssertionError(f"preflight imported provider code: {spec.name}")

        def exec_module(self, module):  # pragma: no cover - never reached
            raise AssertionError(f"preflight executed provider code: {module.__name__}")

    monkeypatch.syspath_prepend(str(wheels["good"].parent))
    monkeypatch.setattr(sys, "meta_path", [_Guard(), *sys.meta_path])

    decision = _decide(wheels, artifact=wheels["good"], evidence=(_evidence(wheels["good"]),))
    assert decision.accepted

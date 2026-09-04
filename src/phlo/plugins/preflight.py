"""Pure pre-install provider compatibility decision (ADR 0053, issue #857).

One evidence-backed decision shared by every install surface (CLI pip
mutation and the Observatory package-install mutation) and enforced
before either mutates the Python environment: candidate identity, digest
binding, core/capability compatibility, project policy, and trust tier.

The decision is pure and static: it reads the candidate wheel's
dist-info metadata and the registry descriptor without importing or
executing any provider code (ADR 0053 concern 4 -- install-time
observation is never evidence, and no uninstalled provider is ever
discovered or imported here).

Authority inputs (ADR 0053 concern 1):

- descriptor (publisher claim, ceiling ``community``),
- conformance verdicts (Phlo-owned evidence, ``phlo-conformance``),
- support decisions (manifest authority + Plan 016 receipts).

Trust tiers are resolved exclusively through
:func:`phlo.plugins.trust.resolve_tier`; this module can never mint a
tier. The only overridable failure is the project's minimum-tier bar,
and an override never changes the resolved tier (ADR 0053 concern 5):
a community artifact installed under override installs as community.
Malformed, digest-mismatched, core-incompatible, capability-incompatible,
and known-failing (evidence) candidates are rejected even with an
override. ``legacy_verified`` authorizes nothing.
"""

from __future__ import annotations

import configparser
import hashlib
import importlib.metadata
import json
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from packaging.requirements import Requirement

from phlo.conformance.suites import SuiteDefinition, get_suite, suite_ids
from phlo.plugins.trust import (
    ConformanceResultRecord,
    DescriptorRecord,
    SupportDecisionRecord,
    TrustTier,
    resolve_tier,
)

#: Non-overridable failure codes (issue #857: rejected even with override).
MALFORMED = "malformed"
DIGEST_MISMATCH = "digest-mismatch"
CORE_INCOMPATIBLE = "core-incompatible"
CAPABILITY_INCOMPATIBLE = "capability-incompatible"
EVIDENCE = "evidence"

#: The only overridable failure: the project's minimum-tier bar.
POLICY = "policy"

_TIER_ORDER = {
    TrustTier.COMMUNITY: 0,
    TrustTier.CONFORMANCE_TESTED: 1,
    TrustTier.RELEASE_SUPPORTED: 2,
}


class ProjectRequirementError(ValueError):
    """Raised when phlo.yaml carries a malformed plugin requirement block.

    The reader is strict (issue #857 step 1): unknown fields, malformed
    values, tier synonyms, and policies that lower a default bar are
    rejected rather than silently dropped.
    """


def _normalise(name: str) -> str:
    return name.lower().replace("_", "-")


def _suite_for_family(family: str) -> SuiteDefinition | None:
    """Return the approved conformance suite for a capability family.

    The suite registry is closed (ADR 0053 concern 7); families without
    an approved suite have no executable path above ``community``.
    """
    for suite_id in suite_ids():
        suite = get_suite(suite_id)
        if suite.capability_type == family:
            return suite
    return None


@dataclass(frozen=True)
class ProjectRequirements:
    """What the project demands of an installed provider.

    ``required_providers`` maps capability family to the provider name
    the project requires (from ``capabilities.defaults`` in phlo.yaml).
    ``min_tier`` maps capability family to an explicit minimum tier that
    may only raise the default bar (from ``plugins.trust.min_tier``).
    """

    required_providers: dict[str, str] = field(default_factory=dict)
    min_tier: dict[str, str] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> ProjectRequirements:
        """The safe absent default: no requirements, no raised bars."""
        return cls()

    def matched_family(self, plugin_name: str) -> str | None:
        """Return the required family this plugin name satisfies, if any."""
        normalised = _normalise(plugin_name)
        for family, provider in self.required_providers.items():
            if _normalise(provider) == normalised:
                return family
        return None

    def default_bar(self, family: str | None) -> TrustTier:
        """The default minimum tier for a candidate of this family.

        A family with an approved tracer demands the tracer's verdict
        (``conformance-tested``); every other candidate demands nothing
        beyond an honest ``community`` resolution.
        """
        if family is not None and _suite_for_family(family) is not None:
            return TrustTier.CONFORMANCE_TESTED
        return TrustTier.COMMUNITY

    def required_tier(self, family: str | None) -> TrustTier:
        """The effective minimum tier for a candidate of this family."""
        bar = self.default_bar(family)
        if family is None:
            return bar
        explicit = self.min_tier.get(family)
        if explicit is None:
            return bar
        explicit_tier = TrustTier(explicit)
        return explicit_tier if _TIER_ORDER[explicit_tier] > _TIER_ORDER[bar] else bar


def read_project_requirements(project_config: dict[str, Any]) -> ProjectRequirements:
    """Strictly read the project requirement/trust-policy block.

    Expected shape (both blocks optional; absence is the safe default)::

        capabilities:
          defaults:
            query_engine: trino
        plugins:
          trust:
            min_tier:
              query_engine: release-supported

    Closed field sets throughout. ``min_tier`` accepts only tier values
    from the frozen vocabulary (no synonyms), may only demand
    ``conformance-tested`` for a family with an approved tracer (the
    tracer enum is closed -- demanding its verdict elsewhere can never be
    satisfied by construction), and may only raise a family's default
    bar, never lower it.
    """
    requirements = ProjectRequirements.empty()

    capabilities = project_config.get("capabilities")
    if capabilities is not None:
        if not isinstance(capabilities, dict):
            raise ProjectRequirementError("phlo.yaml capabilities must be a mapping")
        defaults = capabilities.get("defaults")
        if defaults is not None:
            if not isinstance(defaults, dict):
                raise ProjectRequirementError("phlo.yaml capabilities.defaults must be a mapping")
            for family, provider in defaults.items():
                if not isinstance(family, str) or not family.strip():
                    raise ProjectRequirementError(
                        f"capabilities.defaults key {family!r} must be a non-empty string"
                    )
                if not isinstance(provider, str) or not provider.strip():
                    raise ProjectRequirementError(
                        f"capabilities.defaults[{family!r}] must name a non-empty provider"
                    )
                requirements.required_providers[family] = provider

    plugins = project_config.get("plugins")
    if plugins is not None:
        if not isinstance(plugins, dict):
            raise ProjectRequirementError("phlo.yaml plugins must be a mapping")
        unknown = sorted(set(plugins) - {"trust"})
        if unknown:
            raise ProjectRequirementError(
                f"phlo.yaml plugins: unknown field(s) {unknown}; supported: ['trust']"
            )
        trust = plugins.get("trust")
        if trust is not None:
            if not isinstance(trust, dict):
                raise ProjectRequirementError("phlo.yaml plugins.trust must be a mapping")
            unknown_trust = sorted(set(trust) - {"min_tier"})
            if unknown_trust:
                raise ProjectRequirementError(
                    f"phlo.yaml plugins.trust: unknown field(s) {unknown_trust}; "
                    "supported: ['min_tier']"
                )
            min_tier = trust.get("min_tier")
            if min_tier is not None:
                if not isinstance(min_tier, dict):
                    raise ProjectRequirementError(
                        "phlo.yaml plugins.trust.min_tier must be a mapping"
                    )
                for family, tier in min_tier.items():
                    if not isinstance(family, str) or not family.strip():
                        raise ProjectRequirementError(
                            f"plugins.trust.min_tier key {family!r} must be a non-empty string"
                        )
                    if not isinstance(tier, str):
                        raise ProjectRequirementError(
                            f"plugins.trust.min_tier[{family!r}] must be a tier name"
                        )
                    if tier not in {member.value for member in TrustTier}:
                        raise ProjectRequirementError(
                            f"plugins.trust.min_tier[{family!r}]: {tier!r} is not a trust "
                            "tier (community, conformance-tested, release-supported)"
                        )
                    if tier == TrustTier.CONFORMANCE_TESTED.value and (
                        _suite_for_family(family) is None
                    ):
                        raise ProjectRequirementError(
                            f"plugins.trust.min_tier[{family!r}]: conformance-tested demands "
                            "an approved tracer, and no suite is approved for this family "
                            "(the tracer enum is closed; extending it is a decision, "
                            "not a code change)"
                        )
                    if tier == TrustTier.COMMUNITY.value:
                        raise ProjectRequirementError(
                            f"plugins.trust.min_tier[{family!r}]: community is the safe "
                            "absent default and cannot be configured; policies may only "
                            "raise a bar"
                        )
                    requirements.min_tier[family] = tier

    for family, tier in requirements.min_tier.items():
        default = requirements.default_bar(family)
        if _TIER_ORDER[TrustTier(tier)] < _TIER_ORDER[default]:
            raise ProjectRequirementError(
                f"plugins.trust.min_tier[{family!r}]: {tier!r} would lower the default "
                f"bar {default.value!r}; policies may only raise a bar"
            )

    return requirements


@dataclass(frozen=True)
class PreflightFailure:
    """One reason a candidate failed the preflight."""

    code: str
    message: str
    overridable: bool
    rule: str | None = None


@dataclass(frozen=True)
class PreflightDecision:
    """The full, honest pre-install decision for one candidate.

    ``tier`` is the resolved trust tier and is never changed by an
    override: a community artifact accepted under override installs as
    community (ADR 0053 concern 5).
    """

    accepted: bool
    tier: TrustTier
    plugin_name: str
    package: str
    version: str
    artifact_digest: str | None
    required_tier: TrustTier
    matched_family: str | None
    failures: tuple[PreflightFailure, ...] = ()
    override_rule: str | None = None
    override_reason: str | None = None
    legacy_verified: bool = False

    def rejection_messages(self) -> list[str]:
        """Human-readable rejection reasons (empty when accepted)."""
        if self.accepted:
            return []
        return [f"{failure.code}: {failure.message}" for failure in self.failures]


def _read_dist_info(wheel: Path, filename: str, *, required: bool = True) -> str | None:
    """Return the text of one dist-info file (or None when absent and optional)."""
    with zipfile.ZipFile(wheel) as archive:
        matches = [name for name in archive.namelist() if name.endswith(filename)]
        if not matches and not required:
            return None
        if len(matches) != 1:
            raise ValueError(
                f"wheel {wheel.name!r} must contain exactly one {filename}; found {len(matches)}"
            )
        return archive.read(matches[0]).decode("utf-8", errors="replace")


def _read_required_dist_info(wheel: Path, filename: str) -> str:
    """Return the text of one dist-info file that must exist."""
    text = _read_dist_info(wheel, filename)
    assert text is not None  # required=True always yields a string or raises
    return text


def _wheel_sha256(wheel: Path) -> str:
    digest = hashlib.sha256()
    with wheel.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _wheel_identity(wheel: Path) -> tuple[str, str]:
    """Return (name, version) read statically from the wheel METADATA."""
    name: str | None = None
    version: str | None = None
    for line in _read_required_dist_info(wheel, ".dist-info/METADATA").splitlines():
        if name is None and line.startswith("Name:"):
            name = line.split(":", 1)[1].strip()
        elif version is None and line.startswith("Version:"):
            version = line.split(":", 1)[1].strip()
        if name is not None and version is not None:
            break
    if not name or not version:
        raise ValueError(f"wheel {wheel.name!r} METADATA lacks Name/Version")
    return name, version


def _wheel_entry_point_groups(wheel: Path) -> set[str]:
    """Return the entry-point groups the wheel declares (static read)."""
    text = _read_dist_info(wheel, ".dist-info/entry_points.txt", required=False)
    if text is None:
        return set()
    parser = configparser.ConfigParser()
    parser.read_string(text)
    return set(parser.sections())


def _wheel_phlo_requirements(wheel: Path) -> list[Requirement]:
    """Return the wheel's declared ``phlo`` core requirements (static read)."""
    requirements: list[Requirement] = []
    for line in _read_required_dist_info(wheel, ".dist-info/METADATA").splitlines():
        if not line.startswith("Requires-Dist:"):
            continue
        requirement = Requirement(line.split(":", 1)[1].strip())
        if requirement.name.lower() == "phlo":
            requirements.append(requirement)
    return requirements


def _core_compatibility_failures(wheel: Path, core_version: str) -> list[PreflightFailure]:
    """Static core-epoch check.

    The wheel must declare a ``phlo`` requirement whose range covers the
    running core (the workspace compatibility-epoch rule); an undeclared
    core posture is unknown, and unknown candidates never reach an
    installer.
    """
    try:
        requirements = _wheel_phlo_requirements(wheel)
    except (zipfile.BadZipFile, ValueError) as exc:
        return [
            PreflightFailure(
                code=MALFORMED,
                message=f"candidate wheel is unreadable: {exc}",
                overridable=False,
            )
        ]
    if not requirements:
        return [
            PreflightFailure(
                code=CORE_INCOMPATIBLE,
                message=(
                    "candidate wheel declares no phlo core requirement; the core "
                    "compatibility epoch is unknown (unknown candidates never reach "
                    "an installer)"
                ),
                overridable=False,
            )
        ]
    for requirement in requirements:
        if requirement.marker is not None and not requirement.marker.evaluate():
            continue
        if core_version not in requirement.specifier:
            return [
                PreflightFailure(
                    code=CORE_INCOMPATIBLE,
                    message=(
                        f"candidate core requirement {str(requirement)!r} does not cover "
                        f"the running phlo {core_version}"
                    ),
                    overridable=False,
                )
            ]
    return []


def _running_core_version() -> str:
    return importlib.metadata.version("phlo")


def load_conformance_evidence(
    paths: list[Path] | tuple[Path, ...],
) -> tuple[ConformanceResultRecord, ...]:
    """Load artifact-bound conformance evidence documents (strict).

    Each path is one schema-shaped conformance-result document as emitted
    by the Phlo-owned runner (#856). Anything outside the frozen shape is
    refused rather than downgraded.
    """
    records: list[ConformanceResultRecord] = []
    for path in paths:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(document, list):
            records.extend(ConformanceResultRecord.from_json(item) for item in document)
        else:
            records.append(ConformanceResultRecord.from_json(document))
    return tuple(records)


def evaluate_install_preflight(
    *,
    descriptor_data: dict[str, Any] | None,
    plugin_name: str | None = None,
    artifact: Path | None = None,
    conformance_results: tuple[ConformanceResultRecord, ...] = (),
    support_decisions: tuple[SupportDecisionRecord, ...] = (),
    project_requirements: ProjectRequirements | None = None,
    override_reason: str | None = None,
    legacy_verified: bool = False,
    now: datetime | None = None,
    core_version: str | None = None,
) -> PreflightDecision:
    """Return the one pure pre-install decision for one candidate.

    Static and code-free: the candidate wheel is read through its
    dist-info only; no provider code is imported, discovered, or
    executed. ``override_reason`` (when non-blank) applies only to the
    overridable minimum-tier policy failure and never changes the
    resolved tier. ``release-supported`` can only come from a typed
    ``SupportDecisionRecord`` (Authority C) -- never from the
    descriptor, the registry, or the candidate itself.
    """
    now = now or datetime.now(UTC)
    requirements = project_requirements or ProjectRequirements.empty()

    # --- Descriptor (Authority A): malformed/unknown candidates never pass.
    if descriptor_data is None:
        return PreflightDecision(
            accepted=False,
            tier=TrustTier.COMMUNITY,
            plugin_name=plugin_name or "",
            package="",
            version="",
            artifact_digest=None,
            required_tier=TrustTier.COMMUNITY,
            matched_family=None,
            failures=(
                PreflightFailure(
                    code=MALFORMED,
                    message=(
                        "no registry descriptor for the candidate; the candidate "
                        "identity is unknown (unknown candidates never reach an "
                        "installer)"
                    ),
                    overridable=False,
                ),
            ),
        )

    name_hint = plugin_name or str(descriptor_data.get("package", ""))
    try:
        descriptor = DescriptorRecord.from_json(name_hint, descriptor_data)
    except (KeyError, TypeError, ValueError) as exc:
        return PreflightDecision(
            accepted=False,
            tier=TrustTier.COMMUNITY,
            plugin_name=name_hint,
            package=str(descriptor_data.get("package", "")),
            version=str(descriptor_data.get("version", "")),
            artifact_digest=None,
            required_tier=TrustTier.COMMUNITY,
            matched_family=None,
            failures=(
                PreflightFailure(
                    code=MALFORMED,
                    message=f"invalid descriptor for {name_hint!r}: {exc}",
                    overridable=False,
                ),
            ),
        )

    matched_family = requirements.matched_family(descriptor.plugin_name)
    required_tier = requirements.required_tier(matched_family)
    failures: list[PreflightFailure] = []

    # --- Artifact binding: identity, digest, core, and capability checks.
    artifact_digest: str | None = None
    if artifact is not None:
        try:
            wheel_name, wheel_version = _wheel_identity(artifact)
        except (zipfile.BadZipFile, ValueError) as exc:
            failures.append(
                PreflightFailure(
                    code=MALFORMED,
                    message=f"candidate wheel is unreadable: {exc}",
                    overridable=False,
                )
            )
        else:
            if _normalise(wheel_name) != _normalise(descriptor.package) or (
                wheel_version != descriptor.version
            ):
                failures.append(
                    PreflightFailure(
                        code=MALFORMED,
                        message=(
                            f"descriptor binds {descriptor.package}=={descriptor.version} "
                            f"but the wheel is {wheel_name}=={wheel_version}; the candidate "
                            "identity does not match its own descriptor"
                        ),
                        overridable=False,
                    )
                )
            artifact_digest = _wheel_sha256(artifact)

            core_version = core_version or _running_core_version()
            failures.extend(_core_compatibility_failures(artifact, core_version))

            if matched_family is not None:
                suite = _suite_for_family(matched_family)
                if suite is not None:
                    try:
                        groups = _wheel_entry_point_groups(artifact)
                    except (configparser.Error, zipfile.BadZipFile, ValueError) as exc:
                        failures.append(
                            PreflightFailure(
                                code=MALFORMED,
                                message=(f"candidate wheel entry points are unreadable: {exc}"),
                                overridable=False,
                            )
                        )
                    else:
                        if suite.entry_point_group not in groups:
                            failures.append(
                                PreflightFailure(
                                    code=CAPABILITY_INCOMPATIBLE,
                                    message=(
                                        f"candidate declares no entry point in "
                                        f"{suite.entry_point_group!r}, required by the "
                                        f"{matched_family!r} capability the project requires"
                                    ),
                                    overridable=False,
                                )
                            )

    # --- Evidence failures (non-overridable): a verdict that condemns the
    # exact artifact, and digest-mismatched variants of a tested build.
    if artifact_digest is not None:
        identity = (descriptor.package, descriptor.version, artifact_digest)
        condemned = any(
            record.result == "fail"
            and (record.subject_package, record.subject_version, record.subject_digest) == identity
            for record in conformance_results
        )
        if condemned:
            failures.append(
                PreflightFailure(
                    code=EVIDENCE,
                    message=(
                        f"a Phlo-owned conformance verdict failed for this exact artifact "
                        f"({descriptor.package}=={descriptor.version} at {artifact_digest})"
                    ),
                    overridable=False,
                )
            )

    if (
        artifact_digest is not None
        and matched_family is not None
        and _suite_for_family(matched_family) is not None
    ):
        same_version = [
            record
            for record in conformance_results
            if _normalise(record.subject_package) == _normalise(descriptor.package)
            and record.subject_version == descriptor.version
        ]
        exact_pass = any(
            record.result == "pass"
            and (record.subject_package, record.subject_version, record.subject_digest)
            == (descriptor.package, descriptor.version, artifact_digest)
            for record in same_version
        )
        if (
            same_version
            and not exact_pass
            and any(record.result == "pass" for record in same_version)
        ):
            failures.append(
                PreflightFailure(
                    code=DIGEST_MISMATCH,
                    message=(
                        f"passing evidence exists for {descriptor.package}=="
                        f"{descriptor.version} but binds a different artifact digest; "
                        f"the candidate at {artifact_digest} is a digest-mismatched variant"
                    ),
                    overridable=False,
                )
            )

    # --- Trust tier: resolved exclusively through the frozen resolver.
    resolution = resolve_tier(
        descriptor,
        conformance_results=conformance_results,
        support_decisions=support_decisions,
        now=now,
        legacy_verified=legacy_verified,
        artifact_digest=artifact_digest,
    )

    # --- Project policy: the only overridable failure.
    override_rule: str | None = None
    override_applied_reason: str | None = None
    if _TIER_ORDER[resolution.tier] < _TIER_ORDER[required_tier]:
        rule = f"min_tier:{matched_family}" if matched_family is not None else "min_tier"
        if override_reason is not None and override_reason.strip():
            override_rule = rule
            override_applied_reason = override_reason.strip()
        else:
            failures.append(
                PreflightFailure(
                    code=POLICY,
                    message=(
                        f"candidate tier {resolution.tier.value!r} is below the "
                        f"project's required {required_tier.value!r}"
                        + (f" for the {matched_family!r} capability" if matched_family else "")
                    ),
                    overridable=True,
                    rule=rule,
                )
            )

    non_overridable = [failure for failure in failures if not failure.overridable]
    overridable = [failure for failure in failures if failure.overridable]
    accepted = not non_overridable and not (overridable and override_rule is None)

    return PreflightDecision(
        accepted=accepted,
        tier=resolution.tier,
        plugin_name=descriptor.plugin_name,
        package=descriptor.package,
        version=descriptor.version,
        artifact_digest=artifact_digest,
        required_tier=required_tier,
        matched_family=matched_family,
        failures=tuple(failures),
        override_rule=override_rule,
        override_reason=override_applied_reason,
        legacy_verified=resolution.legacy_verified,
    )


__all__ = [
    "CAPABILITY_INCOMPATIBLE",
    "CORE_INCOMPATIBLE",
    "DIGEST_MISMATCH",
    "EVIDENCE",
    "MALFORMED",
    "POLICY",
    "PreflightDecision",
    "PreflightFailure",
    "ProjectRequirementError",
    "ProjectRequirements",
    "evaluate_install_preflight",
    "load_conformance_evidence",
    "read_project_requirements",
]

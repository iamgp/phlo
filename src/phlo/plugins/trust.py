"""Pure provider trust-tier vocabulary (ADR 0053).

Neutral models, canonicalization, artifact digests, legacy-v1
normalization, and the pure tier resolver for the frozen provider
trust-tier contract. The module is deliberately stdlib-only and imports
nothing from the plugin system: every function is static and total, so
validation can run untrusted registry data without executing any
provider code.

Authority model (ADR 0053 concern 1):

- Descriptor (publisher): static self-describing claims; ceiling
  ``community``.
- Conformance (Phlo-owned evidence): verdicts authored only by the
  ``phlo-conformance`` runner, with an approved tracer and durable
  evidence references; supports ``conformance-tested`` for the exact
  artifact identity.
- Support (manifest authority + Plan 016 receipts): typed
  ``SupportDecision`` records originating only from the support
  manifest; the only path to ``release-supported``.

The resolver can never derive ``release-supported`` from descriptors or
conformance results alone, and ``legacy_verified`` is a derived,
non-assertable compatibility state that grants nothing beyond
``community``.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

#: Registry-contract compatibility epoch counted by the v2 registry schema
#: (``registry/schema/registry.v2.json``, ``compatibility_epoch``) and named
#: by ``scripts/validate_support_manifest.py``'s epoch check. Bumping the
#: epoch retires ``legacy_verified`` (ADR 0053 concern 5).
CURRENT_COMPATIBILITY_EPOCH = 1

#: Last epoch in which the derived ``legacy_verified`` state may exist.
LEGACY_VERIFIED_MAX_EPOCH = 1

#: Closed approved-tracer set (ADR 0053 concern 7). Extending it is a
#: decision, not a code change.
APPROVED_TRACERS = frozenset({"query_engine.v1"})

#: Identity every conformance record must name as its executor.
CONFORMANCE_RUNNER_IDENTITY = "phlo-conformance"

#: Asserter identities, one per authority (ADR 0053 concern 2).
ASSERTER_DESCRIPTOR = "publisher"
ASSERTER_CONFORMANCE = "phlo-conformance"
ASSERTER_SUPPORT = "phlo-support"

#: SHA-256 digest prefix used for artifact identity (ADR 0050 identity model).
_DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


class TrustTier(Enum):
    """The three trust tiers (ADR 0053 concern 3). ``legacy_verified`` is
    deliberately absent: it is a compatibility state, not a tier."""

    COMMUNITY = "community"
    CONFORMANCE_TESTED = "conformance-tested"
    RELEASE_SUPPORTED = "release-supported"


class UnknownFieldError(ValueError):
    """Raised when untrusted data carries fields outside a frozen shape."""


def canonical_json_bytes(value: Any) -> bytes:
    """Return the canonical JSON encoding: sorted keys, no whitespace."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def content_digest(value: Any) -> str:
    """Return the SHA-256 content digest of a canonicalized JSON value."""
    return f"sha256:{hashlib.sha256(canonical_json_bytes(value)).hexdigest()}"


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp {value!r} must carry a UTC offset")
    return parsed.astimezone(UTC)


def _no_unknown_fields(data: dict[str, Any], allowed: frozenset[str], label: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise UnknownFieldError(f"{label}: unknown field(s) {unknown}")


@dataclass(frozen=True)
class DescriptorRecord:
    """Authority A fact: a static publisher claim. Supports only
    ``community``; carries no tier field by construction."""

    plugin_name: str
    type: str
    package: str
    version: str
    description: str
    author: str
    homepage: str | None = None
    tags: list[str] = field(default_factory=list)
    core: bool = False

    @classmethod
    def from_json(cls, plugin_name: str, data: dict[str, Any]) -> DescriptorRecord:
        _no_unknown_fields(
            data,
            frozenset(
                {"type", "package", "version", "description", "author", "homepage", "tags", "core"}
            ),
            f"descriptor {plugin_name!r}",
        )
        record = cls(
            plugin_name=plugin_name,
            type=str(data["type"]),
            package=str(data["package"]),
            version=str(data["version"]),
            description=str(data.get("description", "")),
            author=str(data["author"]),
            homepage=data.get("homepage"),
            tags=[str(tag) for tag in data.get("tags", [])],
            core=bool(data.get("core", False)),
        )
        if not record.plugin_name or not record.package or not record.author:
            raise ValueError(
                f"descriptor {plugin_name!r}: plugin_name, package, and author must be non-empty"
            )
        return record

    def artifact_identity(self) -> tuple[str, str, str]:
        """Return the (package, version, digest) identity of the subject."""
        return (self.package, self.version, content_digest(self.descriptor_claim()))

    def descriptor_claim(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "package": self.package,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "homepage": self.homepage,
            "tags": list(self.tags),
            "core": self.core,
        }


@dataclass(frozen=True)
class ConformanceResultRecord:
    """Authority B fact: a Phlo-owned conformance verdict. Authors other
    than ``phlo-conformance``, unapproved tracers, and verdicts without
    evidence references are refused rather than downgraded."""

    subject_package: str
    subject_version: str
    subject_digest: str
    tracer: str
    result: str
    evidence_refs: tuple[str, ...]
    executed_by: str
    run_at: datetime
    expires_at: datetime

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> ConformanceResultRecord:
        _no_unknown_fields(
            data,
            frozenset(
                {
                    "subject",
                    "tracer",
                    "result",
                    "evidence_refs",
                    "executed_by",
                    "run_at",
                    "expires_at",
                }
            ),
            "conformance result",
        )
        subject = data["subject"]
        if not isinstance(subject, dict):
            raise ValueError("conformance result: subject must be an object")
        _no_unknown_fields(subject, frozenset({"package", "version", "digest"}), "subject")
        try:
            record = cls(
                subject_package=str(subject["package"]),
                subject_version=str(subject["version"]),
                subject_digest=str(subject["digest"]),
                tracer=str(data["tracer"]),
                result=str(data["result"]),
                evidence_refs=tuple(str(ref) for ref in data["evidence_refs"]),
                executed_by=str(data["executed_by"]),
                run_at=_utc(str(data["run_at"])),
                expires_at=_utc(str(data["expires_at"])),
            )
        except KeyError as exc:
            raise ValueError(f"conformance result: missing required field {exc}") from exc
        if not _DIGEST_PATTERN.match(record.subject_digest):
            raise ValueError(
                f"conformance result: digest {record.subject_digest!r} is not a sha256 digest"
            )
        if record.result not in {"pass", "fail"}:
            raise ValueError(f"conformance result: unknown result {record.result!r}")
        if record.tracer not in APPROVED_TRACERS:
            raise ValueError(f"conformance result: tracer {record.tracer!r} is not approved")
        if record.executed_by != CONFORMANCE_RUNNER_IDENTITY:
            raise ValueError(
                f"conformance result: executed_by {record.executed_by!r} is not "
                f"{CONFORMANCE_RUNNER_IDENTITY!r}"
            )
        if not record.evidence_refs or any(not ref for ref in record.evidence_refs):
            raise ValueError("conformance result: evidence_refs must be non-empty and resolvable")
        return record

    def qualifies(self, *, now: datetime, identity: tuple[str, str, str]) -> bool:
        """True when this record can support ``conformance-tested`` for
        ``identity``: passing, approved, Phlo-executed, with evidence, and
        unexpired. Any miss is a silent no (expiry is mechanical, ADR 0053
        concern 6)."""
        return (
            self.result == "pass"
            and self.tracer in APPROVED_TRACERS
            and self.executed_by == CONFORMANCE_RUNNER_IDENTITY
            and bool(self.evidence_refs)
            and (self.subject_package, self.subject_version, self.subject_digest) == identity
            and self.run_at <= now < self.expires_at
        )


@dataclass(frozen=True)
class SupportDecisionRecord:
    """Authority C fact: a typed support-manifest decision. This is the
    only shape in which ``release-supported`` may enter the resolver; it
    can never be derived from Authority A or B inputs."""

    component_kind: str
    component_name: str
    tier: TrustTier
    evidence_bar: str
    receipt_refs: tuple[str, ...]
    owner: str
    decided_at: datetime
    review_by: datetime
    requires_receipts: bool = False

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> SupportDecisionRecord:
        _no_unknown_fields(
            data,
            frozenset(
                {
                    "component_kind",
                    "component_name",
                    "tier",
                    "evidence_bar",
                    "receipt_refs",
                    "owner",
                    "decided_at",
                    "review_by",
                    "requires_receipts",
                }
            ),
            "support decision",
        )
        tier = TrustTier(str(data["tier"]))
        record = cls(
            component_kind=str(data["component_kind"]),
            component_name=str(data["component_name"]),
            tier=tier,
            evidence_bar=str(data["evidence_bar"]),
            receipt_refs=tuple(str(ref) for ref in data.get("receipt_refs", ())),
            owner=str(data["owner"]),
            decided_at=_utc(str(data["decided_at"])),
            review_by=_utc(str(data["review_by"])),
            requires_receipts=bool(
                data.get("requires_receipts", tier == TrustTier.RELEASE_SUPPORTED)
            ),
        )
        if not record.evidence_bar or not record.owner:
            raise ValueError("support decision: evidence_bar and owner must be non-empty")
        if record.requires_receipts and not record.receipt_refs:
            raise ValueError(
                "support decision: tier requires matching Plan 016 receipts but none are referenced"
            )
        return record

    def qualifies(self, *, now: datetime, component_identity: tuple[str, str]) -> bool:
        """True when this decision currently supports the component named
        by ``component_identity`` (a ``(kind, name)`` pair, e.g.
        ``("package", "phlo-trino")``): tier already release-supported,
        receipts present when required, and not past review. Overrides
        cannot enter here — there is no override input that changes a
        tier (ADR 0053 concern 5). Artifact-level proof for a specific
        version binds through ``receipt_refs`` (Plan 016 receipts), not
        through this record's component name."""
        return (
            self.tier == TrustTier.RELEASE_SUPPORTED
            and (self.component_kind, self.component_name) == component_identity
            and (bool(self.receipt_refs) or not self.requires_receipts)
            and now <= self.review_by
        )


@dataclass(frozen=True)
class NormalizedEntry:
    """A v1 registry entry normalized honestly: ``verified: true`` becomes
    the derived ``legacy_verified`` state — never an inferred tier."""

    descriptor: DescriptorRecord
    legacy_verified: bool


def normalize_v1_entry(plugin_name: str, entry: dict[str, Any], *, epoch: int) -> NormalizedEntry:
    """Normalize one legacy v1 registry entry.

    ``verified`` is retired (ADR 0053 concern 5): a ``true`` value maps to
    the derived ``legacy_verified`` state, valid only while
    ``epoch <= LEGACY_VERIFIED_MAX_EPOCH``; it is dropped from the
    descriptor and never infers a tier. No tier is produced here.
    """
    verified = entry.get("verified", False)
    if not isinstance(verified, bool):
        raise ValueError(f"registry entry {plugin_name!r}: verified must be a boolean")
    legacy_verified = verified and epoch <= LEGACY_VERIFIED_MAX_EPOCH
    descriptor_data = {key: value for key, value in entry.items() if key != "verified"}
    return NormalizedEntry(
        descriptor=DescriptorRecord.from_json(plugin_name, descriptor_data),
        legacy_verified=legacy_verified,
    )


def normalize_v1_registry(
    data: dict[str, Any], *, epoch: int = CURRENT_COMPATIBILITY_EPOCH
) -> dict[str, Any]:
    """Normalize a legacy v1 registry document into the strict v2 shape:
    closed descriptor field sets, ``verified`` retired into the
    container-level derived ``legacy`` block, no tier anywhere."""
    plugins = data.get("plugins", {})
    normalized = {
        name: normalize_v1_entry(name, entry, epoch=epoch).descriptor.descriptor_claim()
        for name, entry in plugins.items()
    }
    legacy_verified = [
        name
        for name, entry in plugins.items()
        if normalize_v1_entry(name, entry, epoch=epoch).legacy_verified
    ]
    document: dict[str, Any] = {
        "$schema": "https://registry.phlohouse.com/schema/registry.v2.json",
        "schema_version": "2",
        "compatibility_epoch": epoch,
        "updated_at": data.get("updated_at", "1970-01-01T00:00:00Z"),
        "plugins": normalized,
    }
    if legacy_verified:
        document["legacy"] = {"legacy_verified": sorted(legacy_verified)}
    return document


@dataclass(frozen=True)
class TierResolution:
    """The honest resolution result: at most one tier plus, when the entry
    was migrated from ``verified: true``, the (non-assertable) derived
    ``legacy_verified`` state."""

    tier: TrustTier
    legacy_verified: bool = False


def resolve_tier(
    descriptor: DescriptorRecord,
    *,
    conformance_results: tuple[ConformanceResultRecord, ...] = (),
    support_decisions: tuple[SupportDecisionRecord, ...] = (),
    now: datetime | None = None,
    epoch: int = CURRENT_COMPATIBILITY_EPOCH,
    legacy_verified: bool = False,
) -> TierResolution:
    """Resolve the tier of one provider entry from typed authority inputs.

    Pure and static: nothing here executes provider code. The ceiling for
    descriptor-only inputs is ``community``; ``conformance-tested``
    requires an unexpired passing verdict from an approved Phlo-owned
    tracer for the exact artifact identity; ``release-supported``
    requires a typed support-manifest decision (with receipts when
    required) — it is never derived from the other authorities. Expired
    or failing evidence degrades the tier mechanically.
    """
    now = now or datetime.now(UTC)
    identity = descriptor.artifact_identity()
    tier = TrustTier.COMMUNITY

    if any(result.qualifies(now=now, identity=identity) for result in conformance_results):
        tier = TrustTier.CONFORMANCE_TESTED

    if epoch > LEGACY_VERIFIED_MAX_EPOCH:
        legacy_verified = False

    package_identity = ("package", descriptor.package)
    if any(
        decision.qualifies(now=now, component_identity=package_identity)
        for decision in support_decisions
    ):
        tier = TrustTier.RELEASE_SUPPORTED

    return TierResolution(tier=tier, legacy_verified=legacy_verified)


def resolve_tiers(
    descriptors: dict[str, DescriptorRecord],
    *,
    conformance_results: tuple[ConformanceResultRecord, ...] = (),
    support_decisions: tuple[SupportDecisionRecord, ...] = (),
    legacy_verified_names: frozenset[str] = frozenset(),
    now: datetime | None = None,
    epoch: int = CURRENT_COMPATIBILITY_EPOCH,
) -> dict[str, TierResolution]:
    """Resolve tiers for every descriptor. ``release-supported`` decisions
    bind to (package, version) component identities, so at most the
    matching entries may carry the tier — and only through Authority C."""
    return {
        name: resolve_tier(
            descriptor,
            conformance_results=conformance_results,
            support_decisions=support_decisions,
            now=now,
            epoch=epoch,
            legacy_verified=name in legacy_verified_names,
        )
        for name, descriptor in descriptors.items()
    }


__all__ = [
    "APPROVED_TRACERS",
    "ASSERTER_CONFORMANCE",
    "ASSERTER_DESCRIPTOR",
    "ASSERTER_SUPPORT",
    "CONFORMANCE_RUNNER_IDENTITY",
    "CURRENT_COMPATIBILITY_EPOCH",
    "LEGACY_VERIFIED_MAX_EPOCH",
    "ConformanceResultRecord",
    "DescriptorRecord",
    "NormalizedEntry",
    "SupportDecisionRecord",
    "TrustTier",
    "TierResolution",
    "UnknownFieldError",
    "canonical_json_bytes",
    "content_digest",
    "normalize_v1_entry",
    "normalize_v1_registry",
    "resolve_tier",
    "resolve_tiers",
]

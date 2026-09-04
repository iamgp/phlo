# ADR 0053: Freeze the Provider Trust-Tier Contract

## Status

Accepted (2026-09-04). Supersedes the single-binary `verified` flag in
`registry/schema/v1.json` as a trust signal: the flag survives only as the
one-epoch `legacy_verified` compatibility input defined in concern 5.
Companion decisions: ADR 0047 (production trust and readiness contract),
ADR 0048 (run-evidence semantics), ADR 0050 (release promotion contract —
evidence bundles, promotion receipts, and the separation of support-manifest
classification from promotion). This ADR is a decision only: it changes no
schema, runner, registry code, or gate (implementation is #855–#857).

## Context

The plugin system knows more than the registry exposes. Today a provider's
entire trust story is one boolean: `verified` in `registry/plugins.json`
(constrained by `registry/schema/v1.json`). Around it:

- `src/phlo/plugins/base/plugin.py` carries capability and support
  declarations (`requires_capabilities`, `optional_capabilities`,
  `CapabilitySupport`) that the registry never surfaces as trust facts.
- `src/phlo/plugins/discovery/_registry_validation.py` performs shape-only
  interface validation, and unknown plugin types pass unvalidated rather
  than being rejected.
- `src/phlo/cli/commands/plugin/install.py` reports post-install capability
  gaps as warnings, after the trust decision has already been made.

Binary trust cannot scale to third-party operators. A registry author can
today write `"verified": true` about their own package, and nothing in the
write path distinguishes that claim from a Phlo-audited one. Three
independent authorities already exist or are being built — the publisher's
descriptor, Phlo-owned conformance evidence, and the support manifest plus
Plan 016 receipts (ADR 0050) — but nothing has frozen who may assert which
fact, or what the tiers mean.

This ADR freezes that contract so #855–#857 (schema, runner, registry
consumer) implement one answer instead of inventing three.

## Reconciled prerequisites

- **Plan 016 evidence relationship.** Plan 016 (`plans/016-gate-promotion-
  on-repeated-artifact-evidence.md`, issue #835) governs promotion on
  repeated qualifying artifact evidence and emits a promotion receipt
  reconciled to public identities; ADR 0047 explicitly defers
  repeated-artifact evidence and freshness policy to Plan 016; ADR 0050
  freezes the evidence bundle those receipts reference and requires
  `registry/support/v1.json` to remain a read-only input to acceptance,
  never a promotion output. The relationship is consistent: Plan 016
  receipts are *evidence inputs* to the support authority, never authority
  themselves, and no ADR or plan makes support classification a promotion
  product. No conflict.
- **Support-manifest authority.** `registry/support/v1.json` (validated by
  `scripts/validate_support_manifest.py`, schema in
  `registry/support/schema/v1.json`) is the single manifest authority for
  release-support classification. Its authoring rule is frozen by the
  Plan 014 / ADR 0050 work: classification changes are normal reviewed code
  changes on `main`, neither a promotion gate nor a promotion output. The
  validator already binds named claims to committed evidence paths and
  checks compatibility epochs. No conflict.
- **#837 tier-authority input.** #837 (explicit support decisions) decides
  per-surface verdicts with owner, evidence bar, and expiry/review date,
  and defines the status-truth and version-drift rules. This ADR freezes
  the *tier vocabulary and authority model* those verdicts will use;
  #837's per-surface verdicts are consumers of this contract, not
  competitors with it. Where #837 later assigns tiers to specific surfaces,
  it must do so within the authority rules frozen here.

## Decision

The following contract is frozen. Every concern is decided; there are no
open alternatives.

### 1. Three independent authorities

Every trust-relevant fact has exactly one authority, and the three
authorities are independent: no authority can manufacture another
authority's facts.

**Authority A — Descriptor (the publisher).** The publisher of a package
asserts static, self-describing facts about their own artifact:

```text
DescriptorClaim := {
  plugin_name:    string            # registry key, unique
  type:           enum (registry plugin types, v1 list)
  package:        string            # distribution name, non-empty
  version:        string
  description:    string
  author:         string            # MUST be a real identity; see concern 2
  homepage:       string (uri, optional)
  tags:           string[]
  core:           boolean           # blessed in-repo provenance only
}
```

Who may assert: only the publisher of record — the maintainer of the
package the descriptor points at (for in-repo plugins, the Phlo
maintainers via a reviewed change to `registry/plugins.json`; for
third-party submissions, the upstream author via the registry
contribution path). What it may support: the `community` tier and nothing
above it. A descriptor claim is *static*: it is checkable without
executing any provider code.

**Authority B — Conformance (Phlo-owned evidence).** Conformance verdicts
come only from conformance runs that Phlo owns: Phlo-authored tracers,
executed on Phlo-controlled infrastructure, recorded to the durable
evidence store per ADR 0048, with the artifact digests they exercised.

```text
ConformanceVerdict := {
  subject:        (package, version-digest)   # what was exercised
  tracer:         enum { query_engine.v1 }    # approved tracers, concern 7
  result:         enum { pass, fail }
  evidence_refs:  durable evidence record ids (ADR 0048 store)
  executed_by:    "phlo-conformance"          # Phlo-owned runner identity
  run_at:         UTC timestamp
  expires_at:     UTC timestamp               # concern 6
}
```

Who may assert: Phlo, and only Phlo. A publisher cannot author, sign, or
submit a conformance verdict; submissions of "test results" by providers
are descriptors (claims), never verdicts (facts). What it may support: the
`conformance-tested` tier for the exercised artifact identity.

**Authority C — Support (manifest authority + Plan 016 receipts).**
Release-support classification lives only in `registry/support/v1.json`,
authored as normal reviewed code on `main` by the Phlo maintainers, and —
where the classification depends on artifact-level proof — bound to a
Plan 016 promotion receipt (evidence bundle + promotion authorization,
per ADR 0050 concerns 4–6).

```text
SupportDecision := {
  component:      (kind, name)                # package | service | capability
  tier:           enum { community, conformance-tested,
                         release-supported }  # concern 3
  evidence_bar:   string                      # what proof the tier required
  receipt_refs:   Plan-016 receipt ids        # required for release-supported
  owner:          maintainer of record
  decided_at:     UTC timestamp
  review_by:      UTC timestamp               # concern 6
}
```

Who may assert: the support-manifest authority alone. What it may support:
`conformance-tested` (mirroring an unexpired Authority-B verdict) and
`release-supported` (manifest decision + matching receipts). The
publisher cannot write into the manifest, and the manifest cannot create
conformance evidence — it can only reference it.

**Independence guarantee.** Each authority reads the others' outputs but
cannot produce them: the registry write path can never emit a
`SupportDecision`; the conformance runner can never edit the manifest;
the manifest can never mint evidence. Enforcement is mechanical (#855–
#857: separate write paths, separate validators) and this ADR is the
normative statement those implementations must satisfy.

### 2. Identity and provenance rules

Every tier-relevant fact must carry provenance, and provenance is part of
the fact, not metadata about it:

- **Identity of the subject.** Facts bind to an artifact identity: for
  Python distributions, the package name plus the version and its
  SHA-256 content digest (ADR 0050 identity model); for container images,
  the immutable digest; for registry entries, the registry key plus
  package/version. A fact that cannot name its subject identity is not
  recordable.
- **Identity of the asserter.** Every fact records who asserted it:
  `publisher` (Authority A), `phlo-conformance` (Authority B), or
  `phlo-support` (Authority C). Anonymous or self-asserting provenance is
  invalid; the `author` field of a descriptor must name an accountable
  publisher identity (for third-party plugins, the upstream maintainer or
  organization, never a placeholder).
- **Identity of the evidence.** Verdicts and support decisions reference
  durable evidence by id (ADR 0048 evidence records; ADR 0050 evidence
  bundles and receipts). A verdict without resolvable evidence references
  is invalid and treated as absent.
- **Immutability.** Recorded facts are append-only; corrections are new
  facts superseding old ones by subject and kind, with the supersession
  recorded. History is never rewritten.
- **No inference across identities.** A verdict for (package, v1.2.3,
  digest D) says nothing about v1.2.4, a rebuild of v1.2.3 with a
  different digest, or any other package by the same publisher. Tiers do
  not inherit across identity boundaries — including preview-provider
  inheritance of blessed-profile support, which is forbidden (Horizon A
  non-goal, consistent with #837).

### 3. Tier truth table

There are exactly three tiers and one legacy compatibility state.

| Tier | Meaning | Assertable by | Requires |
| --- | --- | --- | --- |
| `community` | Exists, is published, and the publisher stands behind the descriptor | Publisher (via registry descriptor) | Descriptor only |
| `conformance-tested` | Phlo-owned conformance runs passed for this exact artifact identity | Phlo only, via Authority B + mirrored by Authority C | Unexpired passing `ConformanceVerdict` from an approved tracer |
| `release-supported` | Phlo support commitments (fix/upgrade posture) apply to this component | Phlo only, via Authority C | Support-manifest entry **and**, where artifact-level proof is required, matching Plan 016 receipts |
| `legacy_verified` (one epoch) | Was `verified: true` under the old binary flag; carries no trust claim beyond `community` | Nobody new — derived, concern 5 | Pre-migration `verified: true` in the registry |

Truth table — who can assert what:

| Assertion | Publisher | Registry write path | Conformance runner | Support manifest |
| --- | --- | --- | --- | --- |
| `community` | ✅ | ✅ (static check only) | ❌ | ❌ |
| `conformance-tested` | ❌ | ❌ (mirror only) | ✅ (verdict) | ✅ (classification referencing a verdict) |
| `release-supported` | ❌ | ❌ | ❌ | ✅ (manifest decision + receipts) |
| `legacy_verified` | ❌ | ❌ (derived at migration) | ❌ | ❌ |

**Registry-authored release support is impossible by construction.** The
registry write path (the JSON Schema in `registry/schema/v1.json` and the
code that consumes it) has no field that maps to any tier above
`community`. Under the v1 schema, `verified` is the only trust-shaped
field, and this ADR strips it of tier meaning (concern 5). #855–#857 must
keep it that way: no registry-schema extension — `support`, `tier`,
`release_supported`, or any synonym — may be introduced, because any such
field would let a registry author assert Authority-B or Authority-C facts
about their own artifact, which is the failure this contract exists to
prevent.

### 4. Static-vs-executable boundary

- **Static validation is code-free.** Everything checkable about a
  registry entry — schema conformance of the descriptor, uniqueness,
  digest well-formedness, provenance fields present, epoch tags — is
  validated without executing any provider code. Static validation may
  *reject* entries but may never *promote* them: the ceiling of static
  validation is `community`. Shape-only validation with unknown types
  passing (`_registry_validation.py` today) is acceptable for discovery
  robustness but confers zero trust; unknown types are recorded as
  `community` with unknown-executable semantics.
- **Executable conformance is the only path up.** `conformance-tested`
  and above require tracer execution (Authority B) on Phlo-owned
  infrastructure. Install-time or run-time capability reporting (as in
  `install.py` post-install warnings) is observation, never evidence:
  it may inform diagnostics but cannot create or restore a tier.
- **No self-test equivalence.** Provider-supplied test suites, CI badges,
  or submitted run logs are descriptors of process, not verdicts. They
  may be referenced by a descriptor but never satisfy an evidence bar.

### 5. Compatibility: one-epoch `legacy_verified` and overrides

- **One-epoch `legacy_verified`.** Every existing `verified: true` entry
  maps, at migration, to the derived state `legacy_verified` for exactly
  one compatibility epoch (one minor-epoch of the registry contract; the
  epoch is counted by #855's schema version and named in
  `scripts/validate_support_manifest.py`'s epoch check). `legacy_verified`
  displays as before but grants nothing beyond `community`: it is not
  `conformance-tested`, does not satisfy any evidence bar, and does not
  inherit blessed-profile support. After one epoch the state is removed;
  surviving trust must be re-earned through Authorities B and C. The
  `verified` boolean itself is retired from the v1 schema by #855; it
  survives only as this one-epoch input.
- **Narrow explicit override.** The only override mechanism is an
  explicit, reviewed `overrides` entry in the support manifest naming the
  component, the rule being overridden, the reason, the decider, and an
  expiry. Overrides are annotations on a component's classification —
  they can relax a *display or gate detail* (for example, waiving a
  documentation requirement for an in-repo component) — and **can never
  change a tier**: no override may set, raise, or substitute for
  `conformance-tested` or `release-supported`, and no override may
  substitute for a missing receipt or verdict. An override request that
  would change a tier is refused by design, not escalated.
- **No grandfathering.** There is no path from `legacy_verified` (or from
  tenure, popularity, or in-repo location) to a higher tier except the
  ordinary evidence routes of concerns 1 and 3.

### 6. Expiry and revocation

- **Expiry.** Every `ConformanceVerdict` carries `expires_at` and every
  `SupportDecision` a `review_by` date (the evidence bar and cadence are
  set by #837's per-surface decisions). An expired verdict stops
  supporting `conformance-tested` immediately; the tier falls back to
  `community` until a fresh verdict exists. Expiry is mechanical, never
  discretionary, and never extends an existing decision — renewal is a
  new fact.
- **Revocation.** A revocation event — evidence-bundle reconciliation
  mismatch (ADR 0050 concern 8), withdrawal or invalidation of referenced
  evidence, a security incident, or a superseding failed verdict —
  downgrades the affected tier immediately and is recorded append-only.
  Revocation is retroactive in effect (the tier was never valid during
  the failure window) but never destructive of history: the record and
  its correction both remain.
- **Asymmetry.** Tiers degrade automatically and instantly; they never
  escalate automatically. Any escalation requires the full authority path
  of concern 1, executed again, for the new artifact identity.

### 7. First tracer: `query_engine.v1`; the estate deferred

The first approved tracer is `query_engine.v1`, exercising query-engine
providers (`QueryEngineSpec` registrations under the `query_engine`
capability type) against the frozen conformance scenarios #856 will
implement. It is the only approved tracer value in
`ConformanceVerdict.tracer` at acceptance of this ADR.

The remainder of the estate — source connectors, quality providers and
checks, transformation providers, service plugins, catalogs, orchestrator
adapters, hooks, asset and resource providers — is **explicitly deferred**:
no conformance verdict may be recorded for them, so none of them can hold
`conformance-tested` or above until a tracer for their capability type is
approved by a future decision. Deferral is a property of the contract, not
a backlog statement: the `tracer` enum is closed, and extending it is a
decision, not a code change.

### 8. Worked examples

**Example 1 — a registry entry cannot make itself release-supported.**
A third-party publisher submits a registry change:

```json
{
  "acme-warehouse-source": {
    "type": "source_connectors", "package": "acme-phlo-source",
    "version": "2.1.0", "author": "ACME Data Ltd",
    "verified": true, "release_supported": true
  }
}
```

Both trust-shaped fields fail: `verified` is retired (it maps to the
derived `legacy_verified` state at most, and only for pre-migration
entries — new entries cannot set it), and `release_supported` is not a
registry field at all; the v1 schema's closed field set rejects it
(#855). Even if the schema accepted arbitrary fields, the resolver
(#857) reads `release-supported` only from Authority C's
`SupportDecision` records, which the registry write path cannot emit,
and only with resolvable Plan 016 receipts, which no publisher can
mint. The entry lands as `community`, by `ACME Data Ltd`, and nothing
the publisher writes next to it changes that. Requiring zero code to
demonstrate: the *schema* (a static, code-free check) rejects the
unknown field, and the *resolver's read path* (manifest + receipts
only) ignores anything the registry claims.

**Example 2 — zero release-supported providers is the honest current
result.** At HEAD, `registry/support/v1.json` classifies every component
against the v1 target (`target_status`), while the gate block records the
present: `gates.status` is `security: blocked`, and `run_evidence`,
`maintenance`, `upgrade_restore`, `golden_path` are `planned`; every
entry in `gates.components` — all 13 packages, all 10 services, all 11
capabilities — is `blocked`, and `production.status` is `blocked`. No
component holds an unexpired conformance verdict (no tracer exists yet),
so nothing can hold `conformance-tested` either. The 31 entries with
`"verified": true` in `registry/plugins.json` map to `legacy_verified`
only. Therefore: at HEAD, the count of `release-supported` providers is
**zero**, the count of `conformance-tested` providers is **zero**, and
the tiers say so honestly. This is the correct output of the contract,
not a gap in it: the support manifest's `target_status` fields express
v1 *intent*, and this contract refuses to let intent masquerade as
current support.

**Example 3 — override refused.** A maintainer proposes an `overrides`
entry for an in-repo component: `{"component": "capability:dlt_ingestion",
"tier": "release-supported", "reason": "core path"}`. The override is
invalid by construction: overrides annotate classification details but
cannot change a tier, and `release-supported` for a capability requires
the manifest's ordinary decision path with its evidence bar and receipts.
The correct action is a normal manifest classification change with the
required evidence — which is exactly the path this ADR intends to be
narrow.

## Consequences

- **Positive.** One unambiguous answer for who may assert each trust
  fact; binary-trust escalation by registry authorship becomes
  structurally impossible rather than policy-discouraged; the existing
  registry estate maps losslessly into `community` + one-epoch
  `legacy_verified` with no data loss; support review (#837), schema
  work (#855), runner work (#856), and registry consumption (#857) have
  one frozen vocabulary.
- **Negative.** Every currently `verified` plugin drops to
  `community`/`legacy_verified` — including first-party ones — until
  Phlo-owned tracers and manifest decisions re-earn their standing; the
  pilot covers only query-engine providers, so the wider estate is
  honestly ungraded for now; two new write paths (conformance runner,
  manifest mirroring) must be built and kept independent (#855–#857).
- **Neutral.** No gate flips, no schema edits, and no registry data
  changes are authorised by this ADR; `registry/support/v1.json`,
  `scripts/validate_support_manifest.py`, and `registry/schema/v1.json`
  are unchanged until #855–#857.

## Decision table

| # | Concern | Decision |
| --- | --- | --- |
| 1 | Authorities | Three independent authorities: descriptor (publisher), conformance (Phlo-owned evidence), support (manifest + Plan 016 receipts); none can manufacture another's facts |
| 2 | Identity/provenance | Facts bind to artifact identity, named asserter, and resolvable evidence ids; append-only; no inheritance across identities |
| 3 | Tiers | `community`, `conformance-tested`, `release-supported`, plus derived one-epoch `legacy_verified`; registry write path ceiling is `community` |
| 4 | Static vs executable | Static validation is code-free and can only reject; executable tracers are the only path above `community` |
| 5 | Compatibility | One-epoch `legacy_verified` grants nothing beyond `community`; narrow explicit overrides never change a tier |
| 6 | Expiry/revocation | Mechanical expiry with `expires_at`/`review_by`; immediate append-only revocation; tiers decay, never auto-escalate |
| 7 | Scope | First tracer `query_engine.v1` only; the wider estate explicitly deferred behind closed `tracer` enum |
| 8 | Current truth | Zero `release-supported` and zero `conformance-tested` at HEAD — the honest result |

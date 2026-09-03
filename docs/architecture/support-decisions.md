# Support Decisions (v1)

Decision record for the externally consumable Phlo surfaces identified by the
[external-consumer and support census](external-support-census.md)
([phlohouse/phlo#836](https://github.com/phlohouse/phlo/issues/836)). It is the
deliverable of the explicit support-decision pass
([phlohouse/phlo#837](https://github.com/phlohouse/phlo/issues/837)) and is the
authority that the narrowing pass (#859) and the deprecation pass (#860) must
implement. Related closed context: #628 (reconcile v1 support claims).

- **Record version:** 1 (2026-09-03)
- **Censused commit:** `1fe9d7584ef774890c3e6f57d398138e1cd6f44d`
- **Record status:** decided, pending maintainer acceptance (see
  [Acceptance ledger](#acceptance-ledger)). No gate, manifest, or registry file
  is changed by this record; the proposed deltas are recorded in
  [`registry/support/v1-delta-proposal.json`](../../registry/support/v1-delta-proposal.json)
  and remain **unapplied** until #859/#860.

## Decision vocabulary

Every censused surface receives exactly one verdict:

| Verdict | Meaning | Census tier mapping |
|---------|---------|---------------------|
| `supported` | Contractual surface. Documented, tested, evidence-backed; breaking changes require a deprecation cycle. | T1 / T2 |
| `community` | Working and kept importable, but not invested in and not guaranteed. Support is best-effort; honesty about it is mandatory (`legacy_verified` in the registry). | T3 |
| `deprecated-with-migration` | Will be removed or narrowed; a migration path is published before removal. | T4 |
| `removed-with-version` | Slated for removal in a named release after a deprecation cycle; no long-term future. | T5 (or end state of T4) |

A "correct" verdict (rows 11 and 14) repairs a false support claim without
changing the surface's tier; it is a truthfulness decision, not a support tier.

## Tier authority, evidence bar, and expiry

These rules are decided here as input to #854 (repeated-evidence promotion) and
the provider trust-tier work (T7-01+).

**Tier authority.** Only a maintainer-accepted decision record (this document
or a successor) may create, change, or retire a support verdict. The support
manifest (`registry/support/v1.json`), the plugin registry
(`registry/plugins.json` + `src/phlo/plugins/registry_data.json`), user docs,
and `phlo status` are *projections* of this record and must not diverge from
it. A pull request that changes a tier must change this record in the same
commit.

**Evidence bar** (tied to the #835 / T3-03 repetition rule: promotion claims
must be backed by evidence that is repeatable, not asserted once):

- `supported`: evidence must be reproducible from committed code and re-runnable
  on demand through the release gates (focused tests plus, where applicable,
  the golden-path/repeated-evidence machinery). A claim that cannot be
  re-evidenced on demand may not be called `supported`.
- `community`: evidence of working-at-HEAD plus published-artifact
  installability. External `none-found` code search is "no evidence found",
  never proof of absence, and may not justify a `supported` claim.
- `deprecated-with-migration` / `removed-with-version`: census evidence of no
  functioning consumer (internal `rg` sweep + external `none-found`) plus a
  published migration path. Removal executes only in #860/#861, one pass per
  approved surface.
- `correct` verdicts: byte-level or call-graph evidence captured in the census
  (e.g. identical registry copies, zero callers of `get_schedules()`).

**Expiry / review.** Every verdict is re-reviewed (a) before each v1 release
cut, (b) no later than **2027-03-01**, and (c) whenever the surface's consumer
evidence materially changes. A verdict whose evidence bar can no longer be met
downgrades automatically to `community` until re-decided — silence never
preserves a tier.

**Profile-inheritance rule (Horizon A non-goal, restated as binding).** A
surface in a `preview` or `outside_v1` profile must not inherit or cite the
support of a blessed-core sibling. Concretely: `phlo-rustfs` (preview) cannot
claim the `supported` status of `phlo-minio` (blessed_core); preview evidence
bars apply to preview surfaces in full.

## Verdicts per censused surface

Summary; per-row detail (owner, evidence bar, expiry, migration) follows.

| Census row | Surface | Verdict | Acceptance |
|---|---------|---------|------------|
| 1 | Flow authoring decorators (`@phlo.publish`, `@phlo.observe`, `@phlo.contract`, `@phlo.access`) | deprecated-with-migration (execution implication); `supported` for the governance-metadata path | pending |
| 2 | `@phlo.backfill` | deprecated-with-migration → removed-with-version | pending |
| 3 | `@phlo.schedule` | deprecated-with-migration → removed-with-version | pending |
| 4 | `@phlo.transform.sql` | deprecated-with-migration → removed-with-version | pending |
| 5 | `phlo.helpers` package | `supported` (six consumer-backed families) + `community` (~24 legacy families) | pending |
| 6 | `phlo.ingestion` compatibility alias (B-37) | deprecated-with-migration | pending |
| 7 | Legacy plugin SDK families (S-01) | `community` (`legacy_verified`); `transformation` family deprecated-with-migration | pending |
| 8 | Compliance plane (S-02) | `supported` (internal contract; CLI docs published) | pending |
| 9 | Operations base contracts (`BaseIngester`/`BaseTransformer` + async) | `supported` (T2 internal contract) | pending |
| 10 | Operations adapter quartet (S-10) | deprecated-with-migration → removed-with-version | pending |
| 11 | Version/metadata duplication (S-08) | correct — single-sourcing rule (below) | pending |
| 12 | `phlo-observatory-example` (S-09) | `community` (documented reference); auto-install removed from dev group | pending |
| 13 | Root Makefile Compose targets (S-04) | removed-with-version (broken); dev-tooling targets `supported` | pending |
| 14 | Plugin registry `verified` flags (S-03 follow-on) | correct — mechanical rename to `legacy_verified` | pending |
| 15 | CLI mutation authorization tables (F5) | `supported` (T2 internal contract) | pending |
| 16 | RBAC plan/verify algorithm (F9) | `supported` (T2 internal contract) | pending |
| 17 | Observatory transport layer (F25) | `supported` (T2 internal contract) | pending |
| 18 | Observatory browser-fallback / stale snapshot (F26) | `supported` (T2 internal contract) | pending |
| 19 | `phlo-testing` packaging (S-06) | `supported` as internal test contract (T2) + packaging fix | pending |

### Row detail

**Row 1 — Flow authoring decorators.** Owner: maintainers/core. Evidence bar:
`supported` requires wired execution reachable from a release gate; today only
the governance-metadata drain (`src/phlo/governance/surface.py:14-20`) is
wired. Verdict: the metadata plane stays `supported`; the *execution
implication* the docs currently teach is deprecated-with-migration. Migration:
docs correction (metadata-only semantics) in #859; users needing orchestration
use explicit asset/provider definitions; a codemod is optional because the
decorators remain valid metadata input. Expiry: 2027-03-01. Rejected
alternative: wiring specs into orchestration now (deferred — it is roadmap
work, not a support verdict; see DECISION-01 context and Horizon A scope).

**Row 2 — `@phlo.backfill`.** Owner: maintainers/core. Evidence bar: T5/T4
standard (zero callers, `none-found`). Verdict: deprecated-with-migration →
removed-with-version; docs correction (non-executing) is required regardless
and happens in #859. Migration: none needed — nothing that registers ever
runs; release-notes deprecation in #860, removal in a following minor.
Expiry: removal re-review at each release cut.

**Row 3 — `@phlo.schedule`.** Owner: maintainers/core. Same evidence bar and
verdict as row 2 (`get_schedules()` has zero callers).

**Row 4 — `@phlo.transform.sql`.** Owner: maintainers/core. Same evidence bar
and verdict as row 2; the eager-SQL capture semantics make rewiring
unattractive, reinforcing removal over wiring.

**Row 5 — `phlo.helpers`.** Owner: maintainers/core + maintainers/docs.
Evidence bar: `supported` requires a first-party consumer in-tree (per the
census only `quality`, `tables`, `partitions`, `governance`, `sql`, `testing`
plus `_common` qualify); `community` requires working-at-HEAD plus published
installability. Verdict: the six consumer-backed families are `supported`
(T1-keep); the ~24 internally-dead families are `community` (T3) and may be
narrowed further only through the #860 deprecation pass. The surface stays
documented as public API; removal without a deprecation cycle is forbidden.
B-33 guide drift is a docs fix in #859, not a removal. Expiry: 2027-03-01.
(See DECISION-05.)

**Row 6 — `phlo.ingestion` alias (B-37).** Owner: maintainers/core. Evidence
bar: T4 standard; the repo's own codemod
(`src/phlo/codemods/decorators_2026_05.py`) already rewrites the call form.
Verdict: deprecated-with-migration. Migration: add the missing
`DeprecationWarning` in #860, keep the codemod through one minor cycle, then
remove the alias and the `sys.modules` class mutation. Expiry: each release
cut.

**Row 7 — Legacy plugin SDK families (S-01).** Owner: maintainers/core.
Evidence bar: `community` requires the census facts (documented, scaffolded,
tested, bundled source implementation, discoverable in `TYPE_CONFIG`); a
removal claim would require zero-consumer evidence, which the census
contradicts. Verdict: `community` (`legacy_verified`) for
`SourceConnectorPlugin` and the quality-check family — kept discoverable, no
roadmap investment; the `transformation` family, which has **no bundled
implementation**, is deprecated-with-migration and is the strongest removal
candidate, still requiring the #860 pass. (See DECISION-01.)

**Row 8 — Compliance plane (S-02).** Owner: maintainers/security. Evidence
bar: `supported` requires the wired, integration-tested evidence-pack path to
stay gated (it is: `tests/integration/compliance/*`, HMAC keys via production
preflight). Verdict: `supported` as an internal contract; the
`phlo compliance` CLI is published in `docs/reference/cli-reference.md` in
#859 (SP9-DRIFT-05). The fail-closed hazards are Phase 1 containment work,
independent of this verdict. (See DECISION-02.)

**Row 9 — Operations base contracts.** Owner: maintainers/core. Evidence bar:
T2 — first-party published packages (`phlo-dlt`, `phlo-sling`, `phlo-dbt`)
consume the contracts in production. Verdict: `supported` as a T2 internal
contract. Explicitly **not** folded into any adapter removal; breaking these
requires a first-party-provider migration plan, not just a deprecation cycle.

**Row 10 — Operations adapter quartet.** Owner: maintainers/core. Evidence
bar: T4 standard (zero production callers; exported but undocumented on a
published wheel). Verdict: deprecated-with-migration → removed-with-version.
Migration: a release-notes deprecation naming the four classes is mandatory
before removal precisely because they are importable from the published wheel;
no shim is provided. Expiry: removal in #860/#861.

**Row 11 — Version/metadata duplication (S-08).** Owner: maintainers/release.
Verdict: correct — the S-08 single-sourcing rule below. Not a tier.

**Row 12 — `phlo-observatory-example`.** Owner: maintainers/observatory.
Evidence bar: `community` requires working-at-HEAD plus published
installability (PyPI ~15–30 downloads/day, provenance unknowable); a PyPI
removal would need a deprecation cycle. Verdict: `community` as a documented
reference extension. The repo-only change — stop auto-installing it in the
root dev dependency group, move to an examples extra — is decided here and
executes in #859; it affects only this repository. Expiry: 2027-03-01.

**Row 13 — Root Makefile Compose targets (S-04).** Owner: maintainers/core.
Evidence bar: removal requires demonstrated brokenness (no root
`compose.yaml`; targets run Compose against nothing — confirmed in the
census). Verdict: removed-with-version for the Compose targets
(`up`, `down`, `stop`, `restart`, `build`, `rebuild`, `pull`, `ps`, `logs`,
`exec`, `clean`, and profile targets); the live dev-tooling targets (`check`,
`lint`, `test`, `docs-build`) stay `supported`. Migration: README/CONTRIBUTING
correction pointing project lifecycle at the `phlo` CLI. Executes in
#859/#861.

**Row 14 — Plugin registry `verified` flags.** Owner: maintainers/core.
Verdict: correct — mechanical rename `verified` → `legacy_verified` in both
byte-identical copies (`registry/plugins.json` and
`src/phlo/plugins/registry_data.json`), changed together; deriving one copy
from the other is the preferred follow-up to end dual-file drift. No behavior
change; the honest support record remains `registry/support/v1.json`. Executes
in #859.

**Rows 15–18 — CLI authorization tables, RBAC algorithm, Observatory
transport, browser fallback.** Owner: maintainers/core / maintainers/observatory.
Evidence bar: T2 — load-bearing for first-party published packages or the
product's own UI data plane. Verdict: `supported` as T2 internal contracts.
Consolidation (F5/F9/F25/F26) is behavior-preserving cleanup permitted by this
record, but none of it is a support change and none of it may drift the
documented `phlo authz` or Observatory behavior.

**Row 19 — `phlo-testing`.** Owner: maintainers/core. Evidence bar: T2 —
25 test files including 13 package authorization suites consume it; a PyPI
removal is off the table while installs are observed. Verdict: `supported` as
an internal test contract (T2), with two corrections decided here: (a) fix or
re-scope the repo-only `scripts/run_golden_path.py` load
(`profile_harness.py:144-147`) so the installed package is honest about what
works; (b) correct the support claim in `docs/packages/phlo-testing.md` in
#859.

## SP9-DECISION-01 — Legacy connector/check/transformation SDK support

**Decision:** keep the legacy plugin SDK families as `community`
(`legacy_verified`): discoverable, scaffoldable, and importable, with no
roadmap investment and no new capability work. The `transformation` family is
additionally deprecated-with-migration (no bundled implementation exists).
New integrations are steered to asset-provider plugins.

**Trade-offs.** Keeping preserves the documented, tested, published surface
and avoids breaking scaffolded plugins; the cost is a permanent second plugin
state machine that competes for attention with the canonical one. Honest
labeling (`legacy_verified`) converts that cost into visible truth instead of
silent drift.

**Rejected alternatives.** (a) *Immediate removal* — rejected: the census
contradicts the "dormant/removable" claim; the families are documented,
scaffolded, tested, and shipped on published wheels, and external
`none-found` is not proof of absence. (b) *Full support investment (T1)* —
rejected: the families are a parallel dormant state machine; investing would
legitimize a second authoring path while the orchestration bridge does not
exist.

## SP9-DECISION-02 — Compliance plane wire or retire

**Decision:** wire (keep). The compliance plane is `supported` as an internal
contract: the evidence-pack export/verify CLI path stays, is published in the
CLI reference in #859, and keeps its integration tests as the safety net. The
SP9-CUT-04 no-op hook may be removed in #859 without affecting this verdict.

**Trade-offs.** Keeping keeps a working, audited, tamper-evident evidence
feature alive at the cost of maintaining signatures/manifest code that few
users reach. Retiring would delete tested security-adjacent functionality
that Phase 1 containment just hardened.

**Rejected alternative.** *Retire the plane* — rejected: the census
contradicts the dormancy premise; the surface is wired, integration-tested,
and reachable, and the fail-closed hazards are already contained in Phase 1,
so the retire rationale no longer holds.

## SP9-DECISION-03 — MinIO/RustFS default selection

**Decision:** MinIO is the default object store. When both MinIO and RustFS
are installed, selection must be explicit; absence of an explicit choice
resolves deterministically to MinIO (never silently ambiguous, never
RustFS-by-accident). RustFS stays `preview` and may not inherit MinIO's
blessed-core support (Horizon A non-goal, see profile-inheritance rule).

**Trade-offs.** MinIO as default matches the current `blessed_core` manifest
entries and the tested service definitions; the cost is deferring any
licensing/distribution benefits of RustFS until it earns promotion on its own
evidence.

**Rejected alternatives.** (a) *RustFS as default* — rejected: it is
`outside_v1`/preview with no blessed-core evidence; flipping would be a gate
flip on unproven surface. (b) *Keep conditional ambiguity, decide at
init-time by install order* — rejected: install-order-dependent behavior is
exactly the non-determinism the finding confirmed.

## SP9-DECISION-04 — Core quality forwarders vs optional Pandera dependency

**Decision:** Pandera remains the blessed quality engine
(`pandera_quality` is a `supported` blessed-core capability). The core quality
forwarders stay `supported` as a T2 internal contract for the first-party
pandera plugin and tests. The `phlo_quality` third name for the decorator is
deprecated-with-migration via the existing codemod in #860. Making Pandera
optional or replacing the forwarders is not decided here and requires a new
decision record.

**Trade-offs.** Keeping the forwarders preserves the internal contract the
pandera plugin and 13 authorization test suites rely on; the cost is a thin
forwarding layer that a future simplification may fold.

**Rejected alternatives.** (a) *Drop the forwarders and depend on
`phlo_pandera` directly everywhere* — rejected now: it is a cross-package
contract change touching published packages, not a support verdict; it belongs
to a simplification slice with its own evidence. (b) *Demote Pandera to
optional/community* — rejected: `pandera_quality` is a blessed-core capability
with focused-test evidence; demotion would be a gate flip on unit-tests-only
grounds, which the programme forbids.

## SP9-DECISION-05 — Helper API support tier

**Decision:** split tier. `supported` (T1): `partitions`, `sql`, `tables`,
`quality`, `governance`, `testing` (plus the private `_common`) — the families
with first-party consumers and documentation. `community` (T3,
`legacy_verified`): the remaining ~24 internally-dead families — kept
importable and documented as-is, no investment, honest labeling, narrowing
only through #860. B-33 docs drift is fixed as docs in #859.

**Trade-offs.** Splitting keeps the documented public-API promise for the
surface users actually touch while telling the truth about the rest; the cost
is that "which helpers are supported" is no longer a single yes. The
hand-maintained `docs/reference/helper-api.md` must carry the tier split
per family.

**Rejected alternatives.** (a) *Whole-surface T1* — rejected: it would claim
support for ~24 modules nothing consumes. (b) *Whole-surface removal/T4* —
rejected: the surface is documented public API on a PyPI-published package
with observed installs; wholesale removal without a deprecation cycle is
unacceptable.

## B-25 rule — what `phlo status` may claim without evidence

**Decision (status-truth rule).** `phlo status` may derive `never_run`,
`stale`, or `healthy` **only** from a wired evidence source (run-evidence
store, health/readiness checks, durable state). Any component whose evidence
source is not wired must be displayed as unknown (e.g. `—` or `unknown`), and
must never be silently derived from a stub, a default, or an empty snapshot.
Where the underlying data is a heuristic or partial, the output must say so.
Implementing this rule (replacing the unwired stub behind B-25) is P3-03E /
T7-06 work; this record fixes the contract it must implement.

**Rejected alternative.** *Keep deriving states from the stub and label the
command "advisory"* — rejected: an advisory command that fabricates states is
the exact operator-truth failure the programme exists to close.

## S-08 rule — version single-sourcing

**Decision (version-drift rule).** There is exactly one version authority per
distribution: the dynamic `importlib.metadata.version("phlo")` resolution in
`src/phlo/__init__.py`. Concretely: (1) the hard-coded
`__version__ = "0.14.0"` literals in `src/phlo/plugins/__init__.py` and
`src/phlo/cli/__init__.py` are removed and replaced by imports or the same
dynamic resolution (SP9-CUT-03 executes here); (2) the `31 × "0.1.0"` package
version column in the plugin registries is either derived from package
metadata or dropped — it may not remain a second hand-maintained version
owner; (3) the stale `registry/plugins.json` `updated_at` must be maintained
by whatever process writes the registry. A check that fails on version drift
between package metadata, the plugin registries, and docs is added in #859.

**Rejected alternative.** *Keep the literals and add a test that they stay in
sync* — rejected: syncing four owners by test preserves the drift machinery
instead of removing it.

## Proposed (unapplied) support-delta

`registry/support/v1-delta-proposal.json` records the deltas this decision
authorizes for #859/#860 to apply. It is **not** applied: the applied manifest
`registry/support/v1.json`, the schema, and
`scripts/validate_support_manifest.py` behavior are unchanged by this record,
and the validator remains green. Non-delta note: module-level surfaces
(census rows 1–6, 10) have no manifest entity; their verdicts live in this
record, and #860/#861 must not invent manifest entries for them.

## Acceptance ledger

Each verdict above carries an explicit maintainer-acceptance slot. Until a
slot is filled, the verdict is **decided and proposed, not accepted**; #859
and #860 must not execute a removal or narrowing that depends on an
unaccepted verdict. A maintainer rejection must record the rejected
alternative here and stops that row (controller handles re-planning).

| Verdict set | Acceptance status | Accepted by | Date |
|---|---|---|---|
| Rows 1–4 (flow/schedule/backfill/transform verdicts) | pending maintainer acceptance | — | — |
| Row 5 + DECISION-05 (helpers tier split) | pending maintainer acceptance | — | — |
| Row 6 (ingestion alias) | pending maintainer acceptance | — | — |
| Row 7 + DECISION-01 (legacy SDK) | pending maintainer acceptance | — | — |
| Row 8 + DECISION-02 (compliance) | pending maintainer acceptance | — | — |
| Rows 9–10 (operations contracts/adapters) | pending maintainer acceptance | — | — |
| Rows 11, 14 (correct verdicts; S-08, registry rename) | pending maintainer acceptance | — | — |
| Row 12 (observatory-example) | pending maintainer acceptance | — | — |
| Row 13 (Makefile Compose targets) | pending maintainer acceptance | — | — |
| Rows 15–18 (T2 internal contracts) | pending maintainer acceptance | — | — |
| Row 19 (phlo-testing) | pending maintainer acceptance | — | — |
| DECISION-03 (MinIO/RustFS default) | pending maintainer acceptance | — | — |
| DECISION-04 (quality forwarders/Pandera) | pending maintainer acceptance | — | — |
| B-25 status-truth rule | pending maintainer acceptance | — | — |
| Tier authority / evidence bar / expiry | pending maintainer acceptance | — | — |

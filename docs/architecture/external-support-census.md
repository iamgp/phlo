# External-Consumer and Support Census

Evidence-backed inventory of every externally consumable Phlo surface and its
actual consumers, produced for the Phase 3 support decisions
([phlohouse/phlo#836](https://github.com/phlohouse/phlo/issues/836)). It feeds
the explicit support-decision pass (#837); the narrowing pass (#859) and the
deprecation pass (#860) depend on those decisions, not on this document.

**Censused commit: `1fe9d7584ef774890c3e6f57d398138e1cd6f44d`** (2026-09-03).
Every claim below was verified against this exact commit, not against the
programme audit scratchpads, whose claims were treated as hypotheses to
re-check. Where the current code disagrees with a prior finding, the
contradiction is recorded explicitly.

This document is an inventory only. No code, gate, contract, or deprecation is
changed by it.

## Method and evidence quality

- **Declaration** is read from the code, entry points, or docs at the censused
  commit.
- **Repo-internal consumers** were established with `rg` over `src/`, `packages/`,
  `tests/`, `scripts/`, and `.github/` (commands in the appendix).
- **External-consumer evidence** was collected on 2026-09-03 from GitHub
  (repo stats, code search, issues) and PyPI (published artifacts, download
  statistics via pepy.tech). Evidence keys:
  - `none-found` — GitHub code search found no consumer outside
    `phlohouse/phlo`. GitHub code search only indexes public, indexed code, so
    this is "no evidence found", not "proof of absence".
  - `installs-observed` — the distribution is published on PyPI and receives
    measurable downloads. Download provenance is unknowable (it includes the
    project's own CI and mirrors); it demonstrates reachable installs, not
    identified consumers.
- **Support claim** is what a user would reasonably believe is supported today,
  given docs, packaging, and tests.
- **Recommended tier** is the input to #837. Tiers used here:

  | Tier | Meaning |
  |------|---------|
  | T1 Supported public API | Documented, tested, kept as a contract |
  | T2 Internal contract | Consumed by first-party packages; supported for them, not advertised to end users |
  | T3 Legacy/verified-only | Works and is documented, but no roadmap investment; support is a product decision (registry `verified=true` becomes `legacy_verified` under this tier) |
  | T4 Deprecate candidate | Documented or exported, but no working consumer; deprecation + codemod before removal |
  | T5 Remove candidate | No consumer evidence and no documentation promise; correction or removal without a long deprecation cycle |

  Tier assignment here is a recommendation with evidence, not a decision;
  #837 decides.

## Census

| # | Surface | Declared API | Repo-internal consumers | External evidence | Current support claim | Recommended tier |
|---|---------|--------------|-------------------------|-------------------|----------------------|------------------|
| 1 | Flow authoring: `@phlo.publish`, `@phlo.observe`, `@phlo.contract`, `@phlo.access` (B-30, S-05) | `src/phlo/flow.py`; exported via `phlo.__init__` lazy `_FLOW_EXPORTS`; documented as public authoring API in `docs/guides/developer-guide.md:853-948` | `src/phlo/governance/surface.py:14-20` drains publish/observe/contract/access specs into the governance surface (metadata plane only). The specs are **not** bridged to any orchestrator: assets reach the Dagster adapter only through `AssetProviderPlugin.get_assets()` (`packages/phlo-dlt/src/phlo_dlt/plugin.py:173`), and no provider feeds flow specs. Flow-decorated functions never execute in orchestration — **B-30 confirmed at HEAD** | `none-found` for `phlo.publish`/`phlo.observe` outside the repo | Docs present these as the way to mark published datasets and declare governance metadata. Metadata (governance) works; execution does not | Product call for #837 between: (a) wire specs into orchestration, or (b) T4 — deprecate the execution implication, keep the governance-metadata path, codemod users to explicit DAG definitions. Metadata plane alone is real, working surface |
| 2 | `@phlo.backfill` (B-30) | `src/phlo/flow.py` `backfill()`; documented `docs/guides/developer-guide.md:878` | Zero consumers: `get_backfill_assets()` has no caller outside definition and `tests/plugins/test_flow_authoring_decorators.py`; nothing registers backfill specs with an orchestrator | `none-found` | Documented as a "repeatable backfill job"; nothing can run what it registers | T5 correction or T4 deprecation; no functioning behavior is lost either way. Non-execution is silent — a docs correction is required regardless |
| 3 | `@phlo.schedule` (B-31) | `src/phlo/flow.py` `schedule()`; documented `docs/guides/developer-guide.md:952-958` | Zero consumers: `get_schedules()` has no caller anywhere; no schedule object is ever created — **B-31 confirmed at HEAD** | `none-found` | Documented as declaring "when static targets should run"; no schedule is ever created | T5 correction or T4 deprecation. Silent non-execution; docs correction required regardless |
| 4 | `@phlo.transform.sql` (B-34) | `src/phlo/transform.py` `sql()`; exported as `phlo.transform` submodule; documented `docs/guides/developer-guide.md:837` | Zero consumers: `get_transform_assets()` has no caller outside tests; no provider bridges transform specs to the Dagster adapter — **B-34 confirmed at HEAD** | `none-found` | Documented as registering a SQL transform; the registered asset is unreachable at runtime | T5 correction or T4 deprecation. Note the eager-SQL capture semantics would also need rework if wired |
| 5 | `phlo.helpers` package (S-07, B-33) | `src/phlo/helpers/` — 30 modules re-exported through `phlo/helpers/__init__.py`; documented as public API in `docs/reference/helper-api.md` and `docs/guides/lakehouse-helpers.md` | Internal consumers exist for only ~6 of 30 modules: `quality` (quality_rules.py, pandera plugin), `tables` (iceberg/delta/clickhouse packages), `partitions`, `governance`, `sql`, `testing`, plus `_common`. ~24 modules have **zero** internal callers | `none-found` for `from phlo.helpers` in external code; `installs-observed` for the `phlo` distribution (PyPI, 20,438 total downloads) — installs exist, no identified consumer of helpers | Documented public API ("meant for the day-to-day code users write"); `docs/reference/helper-api.md` is a hand-maintained map of the full surface. B-33 (guide imports of nonexistent/unexported helpers) must be re-checked doc-by-doc at fix time | T1 for the documented surface — removal without a deprecation cycle is not safe: it is advertised public API on a PyPI-published package. #837 may narrow *which* module families stay T1 (e.g. keep partitions/sql/tables/quality/governance; mark the ~24 internally-dead families T3) but every cut needs the #860 deprecation pass first. B-33 docs drift is a docs fix, not a removal |
| 6 | `phlo.ingestion` compatibility alias (B-37) | `src/phlo/ingestion.py` — callable-module class mutation (`sys.modules[__name__].__class__ = _CallableIngestionModule`), forwards to `phlo.ingest` | Exported via `phlo.__init__` `_SUBMODULE_EXPORTS`; no first-party caller uses the alias form (examples all use `@phlo.ingest.dlt`); retirement is encoded in the repo's own codemod `src/phlo/codemods/decorators_2026_05.py` | `none-found` for `phlo.ingestion(` outside the repo | Docstring calls it "backward-compatible"; **no `DeprecationWarning` is emitted anywhere in the module** — B-37 confirmed at HEAD | T4: add the warning (currently missing) during #860, then remove. The codemod already rewrites the call form |
| 7 | Legacy plugin SDK families: `SourceConnectorPlugin`, `TransformationPlugin`, quality-check family (S-01) | `src/phlo/plugins/base/source.py`, `base/transform.py`, `base/quality.py`; exported from `phlo.plugins`; present in discovery `TYPE_CONFIG` (`src/phlo/plugins/discovery/_registry_constants.py`); scaffoldable via `src/phlo/cli/commands/plugin/scaffold.py` (`source`, `transformation`) | Documented in `docs/reference/plugin-api.md` and `docs/guides/plugin-development.md`; tested (`tests/plugins/test_plugin_system.py`, `test_plugin_loading.py`, `test_plugin_discovery_lifecycle.py`); one bundled implementation exists (`packages/phlo-core-plugins/src/phlo_core/sources/rest_api.py`, registered in `registry/plugins.json` as type `source`; quality has 4 bundled entries). **No bundled `transformation` implementation exists** — the prior audit's "removal claim contradicted" holds: the families are discoverable, scaffolded, tested, published | `none-found`; `SourceConnectorPlugin` GitHub code-search hits are unrelated same-named classes in other projects | Documented plugin SDK; `registry/plugins.json` marks bundled entries `verified: true` (see row 14) | T3 `legacy_verified` at most: keep discoverable, stop investing; SP9-DECISION-01 decides. The `transformation` family, having no bundled implementation, is the weakest — strongest removal candidate within the family, still needing the #860 pass |
| 8 | Compliance plane: `phlo.compliance` + `phlo compliance` CLI (S-02) | `src/phlo/compliance/` (audit, evidence, governance, manifest, signatures, features) + `src/phlo/cli/commands/compliance.py` (`export-evidence`, `verify-evidence`), registered in `src/phlo/cli/main.py:59,112` | Wired and tested: `tests/integration/compliance/test_evidence_export.py`, `test_tamper_evident_pipeline.py`, `test_signature_enforcement.py`; referenced by `src/phlo/security/production_preflight.py:127` (HMAC keys). The empty `_ensure_compliance_capabilities()` hook (`compliance.py:22`) is a confirmed no-op (SP9-CUT-04). "Largely dormant" is **contradicted**; the fail-closed hazards around approval signature/step-up placeholders remain confirmed | `none-found`; CLI not advertised in `docs/reference/cli-reference.md` (section omitted) | Working, audited evidence-pack feature reachable only by knowing the CLI exists; not in the published CLI reference | Wire-or-retire product call (SP9-DECISION-02). If kept: T2/T3 + publish the CLI docs. If retired: the integration tests are the safety net to remove first. Hazards are containment work (Phase 1), independent of this decision |
| 9 | Operations base contracts: `BaseIngester`/`AsyncIngester`, `BaseTransformer`/`AsyncTransformer` (S-10 context) | `src/phlo/operations/ingestion.py`, `transformation.py`; re-exported from `phlo.operations` | Production consumers: `DltIngester` (`packages/phlo-dlt/src/phlo_dlt/executor.py:171`), `SlingIngester` (`packages/phlo-sling/src/phlo_sling/executor.py:31`), `DbtTransformer` (`packages/phlo-dbt/src/phlo_dbt/transformer.py:249`) | These ship inside the published `phlo-dlt`, `phlo-sling`, `phlo-dbt` distributions (`installs-observed`); `none-found` for external implementers | De-facto provider contract; not user-documented but load-bearing for first-party published packages | T2 internal contract. Do **not** fold into an adapters removal |
| 10 | Operations adapter quartet: `SyncToAsyncIngesterAdapter`, `AsyncToSyncIngesterAdapter`, `SyncToAsyncTransformerAdapter`, `AsyncToSyncTransformerAdapter` (S-10) | `src/phlo/operations/adapters.py` (110 lines, 4 classes); exported from `phlo.operations/__init__.py` | Zero production callers — only `tests/runtime/test_operations_async.py`. **Confirmed at HEAD.** Correction to the audit wording: the adapters are *exported* but not *documented* — no `docs/` page mentions `phlo.operations` adapters | `none-found` | Exported public names on a PyPI-published package; module docstring documents them, user docs do not | T4 (deprecate, then remove): exported-but-undocumented + zero callers. Removal is safe only after a release notes deprecation because the names are importable from the published wheel |
| 11 | Version/metadata duplication (S-08) | Hard-coded `__version__ = "0.14.0"` in `src/phlo/plugins/__init__.py:280` and `src/phlo/cli/__init__.py:19` vs. dynamic `version("phlo")` in `src/phlo/__init__.py:85`; `registry/plugins.json` and `src/phlo/plugins/registry_data.json` (identical files) carry 31 × `"0.1.0"` package versions; `registry/plugins.json` `updated_at: 2025-12-22` predates the 0.14.0 release | Both registries are consumed by plugin discovery and the CLI plugin commands; the two copies must be kept byte-identical (verified identical at HEAD) | `installs-observed` (0.14.0 on PyPI); version drift is user-visible through `phlo` CLI vs plugin metadata | Users see three different version stories depending on which surface they query | Hygiene, not removal: single-owner version (one dynamic source); registry version column either derived or dropped. Input to #837 as a "correct" decision, not a tier |
| 12 | `phlo-observatory-example` (S-09) | `packages/phlo-observatory-example/` — `ExampleObservatoryExtension` via `phlo.observatory.extensions` entry point (`example` group); documented `docs/packages/phlo-observatory-example.md` | Installed into **every dev stack** by root `pyproject.toml` dev dependency group (`pyproject.toml:30`); built by CI (`ci.yml:369`); auto-discovered at Observatory startup once installed | `installs-observed`: published on PyPI, 3,190 total downloads, steady ~15-30/day. Provenance unknowable | An example ships enabled-by-install in dev environments and is documented as a reference implementation | #837 product call: keep T3 as a documented reference extension but **stop auto-installing it** in the default dev group (move to an examples extra). The steady download traffic means a PyPI removal would need a deprecation cycle; removing it from the dev group affects only this repo |
| 13 | Root Makefile Compose targets (S-04) | Root `Makefile:45-77`: `up`, `down`, `stop`, `restart`, `build`, `rebuild`, `pull`, `ps`, `logs`, `exec`, `clean`, profile targets — all invoke `$(COMPOSE)` (`docker compose`) | **Broken at repo root — confirmed:** no `compose.yaml`/`docker-compose.yml` exists at the repository root; `phlo init` generates project-local `.phlo/docker-compose.yml` (`docs/getting-started/quickstart.md:112`), so the root targets run Compose against nothing | Repo-internal maintainer surface only; no external evidence relevant (`none-found`) | `README.md`/`CONTRIBUTING.md` advertise `make check`/`make test` (which work); the Compose targets silently promise a workflow that cannot work from the root | T5 for the Compose targets: correct or delete (maintainer-interface decision, S-04). The dev-tooling targets (`check`, `lint`, `test`, `docs-build`) are live and should stay |
| 14 | Plugin registry `verified` flags (S-03 follow-on) | `registry/plugins.json` + identical `src/phlo/plugins/registry_data.json`: 31 plugins, all `"verified": true` (21 service, 1 source, 4 quality, 1 resource, 3 hooks, 1 ingestion provider) | Consumed by plugin discovery and `phlo plugins` commands | `none-found` for external registries mirroring the file | The flag reads as a support claim; per the programme rule it must not: the honest support record is `registry/support/v1.json` (which already distinguishes `supported`/`tested`/`unverified` and records production-readiness blockers) | Mechanical rename `verified` → `legacy_verified` in #837/#859 (no behavior change, pure honesty). Both copies must change together; consider deriving one from the other to end the dual-file drift |
| 15 | CLI mutation authorization tables (F5) | `src/phlo/cli/authorization.py:48-143` — `MUTATION_COMMANDS`, `COMMAND_RESOURCE_MAP`, `COMMAND_ACTION_MAP` (3 parallel tables, ~21 commands each) | `cli_surface_adapter_class` (`authorization.py:379`) is reused by **8 first-party provider packages** (`phlo-dlt`, `phlo-postgres`, `phlo-pandera`, `phlo-clickhouse`, `phlo-lineage`, `phlo-nessie`, and siblings) — each published separately on PyPI | Provider packages are `installs-observed`; external packages *could* subclass the adapter (`none-found` observed) | An informal but load-bearing cross-package contract | T2: consolidation of the three tables into one spec is safe for #859 *only if* the derived names/shapes (`CliSurfaceAdapter` API) stay stable for the 8 first-party consumers; tests assert set identities |
| 16 | RBAC plan/verify algorithm (F9) | `src/phlo/rbac/` — `plan`/`verify` implemented in `sync.py:53,173`, `compiler.py:105,165,412,522` (4 copies) | Consumed by `phlo authz` CLI and provider sync paths | `none-found` (internal algorithm; the RBAC *behavior* is user-facing via `phlo authz`, documented in `docs/reference/canonical-rbac.md`) | The algorithm is duplicated, but the *surface* (`phlo authz sync/plan/verify`) is documented and tested | T2: consolidation is behavior-preserving cleanup; no support decision needed. External reach is through the documented CLI behavior, which must not drift |
| 17 | Observatory transport layer (F25) | `packages/phlo-observatory/src/phlo_observatory/src/observatory/api/` — 13 modules, 4,142 lines of per-endpoint fetch plumbing (`resources.ts`, `dagster.ts`, `quality.ts`, …) plus `src/server/phlo-api.ts` | Consumed by every Observatory route; the Observatory UI is a user-facing product surface (`installs-observed` via `phlo-observatory` on PyPI) | `none-found` for external UI consumers of the transport internals (it is an application, not a library) | Not a public contract; drift risk is internal (already-drifted copies) | T2: F25 consolidation is safe cleanup; no support tier decision needed. Do not treat as removable — it is the product's UI data plane |
| 18 | Observatory browser-fallback / stale snapshot (F26) | `localStorage`/fallback logic across `src/observatory/routes/liveResource.ts`, `OverviewRoute.tsx`, `shell/localActivity.ts`, `shell/ObservatoryShell.tsx`, `api/settings.ts`, `api/resources.ts` | Same as row 17 | Same as row 17 | Internal UX behavior; three divergent fallback dialects | T2: fold into the F25 consolidation; no support tier decision |
| 19 | `phlo-testing` packaging (S-06) | `packages/phlo-testing/` — 15 modules, 5,174 lines (harness, profile harness, mocks, authorization surface, fixtures); published on PyPI; documented `docs/packages/phlo-testing.md` | **"Unconsumed" claim contradicted — confirmed at HEAD:** 25 test files import it, including 13 package `test_authorization.py` suites (dlt, clickhouse, trino, nessie, alerting, dbt, postgres, openmetadata, …) plus core tests (`tests/observability/test_hook_bus.py`). Packaging defect confirmed: `profile_harness.py:144-147` loads `scripts/run_golden_path.py` from `Path(__file__).resolve().parents[4]` — works only inside a repo checkout, broken for a pip-installed package | `installs-observed`: 4,006 total PyPI downloads, steady ~10-35/day, provenance unknowable | Documented package whose installed form cannot load its own golden-path harness; repo tests exercise it from a checkout where the relative path happens to resolve | T2 internal contract + fix or re-scope: either move the golden-path module into the package or document the harness as repo-only. A PyPI removal is off the table while installs are observed; a support-claim correction in `docs/packages/phlo-testing.md` is cheap and safe |

## B-30 / B-31 / B-34 / B-37 disposition

- **B-30** (publish/observe/backfill never execute): **confirmed at HEAD.**
  Census rows 1-2. Governance-metadata consumers are real; orchestration
  execution does not exist. Handed to #837.
- **B-31** (`@phlo.schedule` never creates schedules): **confirmed at HEAD.**
  Row 3. `get_schedules()` has zero callers. Handed to #837.
- **B-34** (`@phlo.transform.sql` never reaches the pipeline): **confirmed at
  HEAD.** Row 4. `get_transform_assets()` has zero callers. Handed to #837.
- **B-37** (`phlo.ingestion` alias emits no warning): **confirmed at HEAD.**
  Row 6. The alias works silently; the codemod for its retirement already
  exists. Handed to #837/#860.

## Contradictions with prior audit claims, re-verified at HEAD

- **S-01 "dormant/removable"**: contradicted — families are documented,
  scaffoldable, tested, and shipped (row 7). The `transformation` family has no
  bundled implementation.
- **S-02 "dormant compliance plane"**: contradicted — the CLI evidence-pack
  path is wired and integration-tested (row 8); hazards remain real.
- **S-06 "unconsumed phlo-testing"**: contradicted — 25 test files use it,
  including 13 package `test_authorization.py` suites plus core tests (row
  19); the
  packaging defect (repo-only `scripts/run_golden_path.py` load at
  `packages/phlo-testing/src/phlo_testing/profile_harness.py:144-147`) is
  confirmed.
- **S-07 "helpers runtime-dead, removability unverified"**: partially
  confirmed — ~24 of 30 modules lack internal callers, but the surface is
  documented public API on a PyPI package, so removability is now answered:
  only via a deprecation cycle (row 5).
- **S-10 "no production callers"**: confirmed for the four adapter classes
  only; the sibling base contracts are production load-bearing (rows 9-10).

## External evidence snapshot (2026-09-03)

- GitHub `phlohouse/phlo`: 0 stars, 0 forks, 0 watchers, created 2025-10-07;
  31 issues, none authored outside the maintainer account.
- GitHub code search: no public code outside `phlohouse/phlo` imports
  `phlo.helpers`, `phlo.ingestion`, or uses `phlo.publish`/`phlo.observe`/
  `phlo.transform.sql`. (`SourceConnectorPlugin` hits are unrelated projects.)
- PyPI `phlo`: latest 0.14.0 (uploaded 2026-08-21); 30 released versions;
  20,438 total downloads (pepy); steady single-to-low-double-digit daily
  downloads of 0.14.0 after release-week traffic.
- PyPI `phlo-testing`: 4,006 total downloads, ~10-35/day recent.
- PyPI `phlo-observatory-example`: 3,190 total downloads, ~15-30/day recent.
- PyPI `phlo-core-plugins`: 3,854 total downloads, ~15-70/day recent.
- Download provenance is unknowable; treated as reachable installs, not
  identified consumers. No STOP condition triggered: no identified live
  external dependency on a removal candidate was found.

## Appendix: reproducible commands

Run from the repository root at commit
`1fe9d7584ef774890c3e6f57d398138e1cd6f44d`.

```sh
# --- flow authoring surfaces (rows 1-4) ---
rg -n "def (publish|observe|backfill|schedule|contract|access)\(" src/phlo/flow.py
rg -n "get_publish_assets|get_observe_assets|get_backfill_assets|get_schedules|get_transform_assets|get_contract_specs|get_access_policies" \
  --type py -g '!.venv'          # consumers: governance/surface.py only; backfill/schedules/transform: definition + tests
rg -n "AssetProviderPlugin|get_assets\(\)" packages/phlo-dlt/src/phlo_dlt/plugin.py
rg -n "phlo\.(publish|observe|backfill|schedule|transform|contract|access)\b" docs/ examples/

# --- helpers (row 5) ---
ls src/phlo/helpers | wc -l
for m in artifacts backfills bitemporal connections crosswalks effective errors events evidence governance incremental ingestion io lineage maintenance observability partitions publishing quality reconciliation references schema sql states storage supersession tables testing wap; do
  echo "$m: $(rg -l "from phlo.helpers.$m|from phlo.helpers import.*$m|helpers\.$m" src/ packages/ tests/ scripts/ -g '*.py' | grep -v '^src/phlo/helpers/' | wc -l)"
done
rg -n "phlo.helpers" docs/reference/helper-api.md | head -1

# --- ingestion alias (row 6) ---
rg -n "DeprecationWarning|warnings.warn" src/phlo/ingestion.py        # no matches: B-37 confirmed
rg -n "sys.modules\[__name__\].__class__" src/phlo/ingestion.py
rg -n "ingestion" src/phlo/codemods/decorators_2026_05.py | head

# --- legacy plugin families (row 7) ---
rg -n "TYPE_CONFIG" src/phlo/plugins/discovery/_registry_constants.py
rg -n "source|transformation" src/phlo/cli/commands/plugin/scaffold.py
rg -n "SourceConnectorPlugin|TransformationPlugin" docs/reference/plugin-api.md docs/guides/plugin-development.md
ls packages/phlo-core-plugins/src/phlo_core/sources/

# --- compliance plane (row 8) ---
rg -n "compliance_group" src/phlo/cli/main.py
rg -ln "compliance" tests/integration/compliance/
rg -n "_ensure_compliance_capabilities" src/phlo/cli/commands/compliance.py   # empty no-op body
rg -n "compliance" docs/reference/cli-reference.md                            # no matches: unpublished surface

# --- operations contracts vs adapters (rows 9-10) ---
rg -n "BaseIngester|BaseTransformer" packages/phlo-{dlt,sling,dbt}/src -g '*.py'   # production consumers
rg -n "SyncToAsync|AsyncToSync" src/ packages/ tests/ -g '*.py' | grep -v "phlo/operations"  # tests only
rg -n "adapters" docs/reference/ docs/guides/                                       # no user docs

# --- version/metadata (row 11) ---
rg -n "__version__" src/phlo/__init__.py src/phlo/plugins/__init__.py src/phlo/cli/__init__.py
diff <(jq -S . registry/plugins.json) <(jq -S . src/phlo/plugins/registry_data.json) && echo SAME
rg -c '"0\.1\.0"' registry/plugins.json

# --- observatory-example (row 12) ---
rg -n "observatory-example" pyproject.toml .github/workflows/ci.yml
rg -n "entry-points" -A3 packages/phlo-observatory-example/pyproject.toml

# --- Makefile (row 13) ---
ls compose.yaml docker-compose.yml 2>/dev/null   # absent at root
rg -n "COMPOSE" Makefile | head -3
rg -n "docker-compose" docs/getting-started/quickstart.md

# --- registry (row 14) ---
jq '[.plugins[] | .type] | group_by(.) | map({(.[0]): length}) | add' registry/plugins.json
jq '[.plugins | to_entries[] | select(.value.verified == true)] | length' registry/plugins.json
rg -n "unverified" registry/support/schema/v1.json | head -2

# --- F5 (row 15) ---
rg -n "cli_surface_adapter_class" src/phlo/cli/authorization.py packages/*/src -g '*.py'

# --- F9 (row 16) ---
rg -n "def (plan|verify)" src/phlo/rbac/

# --- F25/F26 (rows 17-18) ---
wc -l packages/phlo-observatory/src/phlo_observatory/src/observatory/api/*.ts | tail -1
rg -ln "localStorage" packages/phlo-observatory/src/phlo_observatory/src/observatory

# --- phlo-testing (row 19) ---
ls packages/phlo-testing/src/phlo_testing | wc -l
wc -l packages/phlo-testing/src/phlo_testing/*.py | tail -1
rg -n "run_golden_path|_repo_root" packages/phlo-testing/src/phlo_testing/profile_harness.py
rg -ln "phlo_testing|phlo-testing" packages/*/tests tests/ -g '*.py' | wc -l
rg -ln "phlo_testing" packages/*/tests/test_authorization.py | wc -l

# --- external evidence snapshot date check ---
gh repo view phlohouse/phlo --json stargazerCount,forkCount,watchers,createdAt
```

External-evidence commands (re-run to refresh; results quoted above are from
2026-09-03):

```sh
gh repo view phlohouse/phlo --json stargazerCount,forkCount,watchers,createdAt
gh search code "from phlo.helpers" --json repository | jq -r '.[].repository.nameWithOwner' | sort -u
gh search code "phlo_ingestion" --json repository | jq -r '.[].repository.nameWithOwner' | sort -u
gh search code '"phlo.transform.sql"' --json repository | jq -r '.[].repository.nameWithOwner' | sort -u
curl -s https://pypi.org/pypi/phlo/json | jq -r '.info.version, .info.summary'
curl -s https://pepy.tech/api/v2/projects/phlo | jq '.total_downloads'
curl -s https://pepy.tech/api/v2/projects/phlo-testing | jq '.total_downloads'
curl -s https://pepy.tech/api/v2/projects/phlo-observatory-example | jq '.total_downloads'
```

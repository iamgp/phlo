# ADR 0052: Freeze the Retail Files Blueprint Distribution Contract

- **Status:** Accepted
- **Approval:** _Maintainer sign-off recorded here by the programme controller on acceptance._
- **Date:** 2026-09-04
- **Task:** Phlo-V1 roadmap decision task; GitHub issue #850
- **Supersedes:** nothing. Companion decisions: ADR 0050 (release promotion contract) supplies
  the artifact-harness mechanics this contract reuses; ADR 0051 (dataset authority) is
  unaffected — a blueprint is a project template, not a Dataset product. Earlier programme
  ADRs in the accepted series are 0047–0051.

## Context

The build-an-example opportunity is delivered: 13 scenarios are tracked complete, and
`examples/lakehouses/retail-files/` is production-shaped, network-independent, blessed-Iceberg,
and sequential-WAP, with an intentional failure mode that leaves published data unchanged
(`examples/lakehouses/retail-files/README.md`, `docs/retail-files-e2e.md`). The gap is
distribution: a user cannot reach it through `phlo init` without cloning the monorepo.

The seams already exist and are reused, not invented:

- **Template discovery.** `src/phlo/cli/templates/registry.py` merges built-in templates with
  provider templates loaded from the `phlo.project_templates` entry-point group
  (`entry_points_for_group("phlo.project_templates")`, lines 28-34); duplicate template names
  raise `TemplateDiscoveryError` at discovery time; `missing_required_packages` already checks
  importability of declared `required_packages`. `phlo init --template <name>` consumes this
  registry (`docs/getting-started/quickstart.md:51`).
- **Distribution vehicle.** The example is already packaged as a standalone consumer project
  (`examples/lakehouses/retail-files/pyproject.toml`: distribution `phlo-retail-files-example`,
  setuptools backend, `phlo[defaults]==0.14.0` plus bounded third-party ranges).
- **What must not happen.** The root `phlo` distribution's extras
  (`pyproject.toml:96-118`) define the v1 support promise: `defaults` and `core-services`.
  Folding a retail analytics blueprint into either would widen that promise to every `phlo`
  user. Provider trust tiers (#854 / ADR-track 0053) wait on this contract; SaaS Product
  Analytics waits as the second candidate until it is stable.

Two prerequisite contracts were reconciled while writing this ADR:

- **ADR 0050 (release promotion).** Its BOM covers "every workspace package published by the
  release (root `phlo` and every `packages/*` distribution)". `phlo-retail-files` is
  composition-owned and lives outside `packages/*`, so it is not in a phlo-release BOM.
  No conflict: this contract **reuses** the Plan 015 artifact-harness mechanics (BOM, digest
  identity, staged-once, no-rebuild promotion, evidence bundles) for a separate, blueprint-scoped
  BOM instead of duplicating or extending the phlo release BOM. Concern 6 below freezes that
  boundary.
- **ADR 0051 (dataset authority).** A blueprint scaffolds project files; it never derives or
  decides Dataset facts. Generated projects consume core's authority unchanged. No conflict.

One conflict with current example state is deliberate and resolved by this ADR, not papered
over: `examples/lakehouses/retail-files/pyproject.toml` today depends on
`phlo-dagster @ git+https://github.com/phlohouse/phlo.git@main#subdirectory=packages/phlo-dagster`
(and likewise `phlo-dbt`, `phlo-pandera` in the dev group) — floating VCS dependencies that the
frozen contract prohibits. Replacing them with exact released pins is implementation work for
#851; this ADR freezes the rule the implementation must satisfy.

## Decision

The following contract is frozen. Every concern is decided as an invariant or an explicit
rejection; the table at the end summarises.

### 1. What a blueprint is (normative schema in prose)

A **blueprint** is a PyPI-distributable Python package that:

1. declares exactly one entry point in the `phlo.project_templates` group, whose value resolves
   to a callable returning a non-empty tuple of `phlo.cli.templates.models.ProjectTemplate`
   instances;
2. carries, per template, `metadata` with a unique `name` (the `phlo init --template` value),
   a human-readable description, and a `required_packages` list of PyPI distribution names;
3. emits, on `phlo init`, **project-owned workflow files** — the generated tree is written into
   the consumer's project and owned by them from that point (the existing template rule:
   "The template creates the files you own", `docs/getting-started/quickstart.md`);
4. never requires Docker images, remote services, or network access beyond the local compose
   stack the generated project itself starts; and
5. is **composition-owned**: it lives beside its example (`examples/lakehouses/retail-files/`),
   is versioned and released by the composition's maintainers, and is not a `packages/*`
   workspace member.

For this decision the blueprint is `phlo-retail-files`, distributing the template named
`retail-files`. **Rejected:** any other distribution name, any second template from the same
distribution without an ADR amendment, and any "generic scenario framework" — blueprints are
per-example packages, not a plugin platform.

### 2. Packaging and dependency rules (normative)

The blueprint's `pyproject.toml` is a normal PEP 621 project with a setuptools (or equivalent
PEP 517) backend. Its dependency set is frozen by allowlist and by pin policy:

- **Phlo-family dependencies are exact-released pins.** Every dependency whose distribution
  name starts with `phlo` (including the `phlo` meta-distribution itself) is pinned to one
  exact released version, e.g. `phlo[defaults]==0.14.0`.
- **Third-party dependencies come only from the allowlist** (machine-checkable; names, as they
  must appear in `pyproject.toml`):
  - runtime and dev groups combined: `pandas`, `pyarrow`, `duckdb`, `dbt-duckdb`
  - nothing else. A dependency outside this list requires an ADR amendment.
- **Rejected dependency shapes** — none may appear in the published blueprint:
  - VCS/URL dependencies (`name @ git+https://…`, `name @ https://…`);
  - path or editable installs (`name @ file://…`, `-e .`);
  - floating pins on phlo-family packages (`phlo-dagster>=x`, `phlo-dagster @ main`);
  - any dependency on the monorepo checkout (the published wheel must be installable from PyPI
    artifacts alone).

**Worked example** (the exact shape #851 must produce; phlo pins move together):

```toml
[project]
name = "phlo-retail-files"
dependencies = [
    "phlo[defaults]==0.14.0",
    "phlo-dagster==0.3.2",
    "phlo-dbt==0.1.0",
    "pandas>=2.3,<3.1",
    "pyarrow>=21,<26",
]

[project.entry-points."phlo.project_templates"]
retail_files = "phlo_retail_files.provider:templates"
```

The current example's `phlo-dagster @ git+…@main` lines violate the frozen shape above and are
replaced by exact released pins during #851.

### 3. Install and discovery routes (frozen; exhaustive)

A consumer reaches the blueprint through exactly two routes:

1. **Direct install:** `uv pip install phlo-retail-files` (or `pip install phlo-retail-files`),
   then `phlo init my-project --template retail-files`.
2. **Bundled extra:** `uv pip install "phlo[blueprints]"` — the root `phlo` distribution gains
   an optional-dependency extra named `blueprints` whose sole member is
   `phlo-retail-files==<exact released version>`. The extra is additive; installing it is
   optional and changes nothing for existing users.

**Explicitly rejected:**

- adding `phlo-retail-files` (or any future blueprint) to the `defaults` or `core-services`
  extras of the root `pyproject.toml` — those extras are the v1 support promise and stay
  blueprint-free;
- a new CLI subcommand, plugin, or core service for blueprint installation — `pip install` plus
  the existing entry-point discovery is the whole mechanism (no Retail-specific core contract);
- automatic or implicit installation of blueprints by `phlo` at any time.

**Discovery seam (invariant):** the only discovery route is the `phlo.project_templates`
entry-point group consumed by `src/phlo/cli/templates/registry.py`. The template name
`retail-files` must not collide with a built-in name; if the core later ships a built-in of the
same name, `TemplateDiscoveryError` fails loudly at discovery time — that is the desired
behavior, and the collision is resolved by renaming the built-in, never the blueprint.

### 4. Versioning, release, and the Plan 015 artifact-harness boundary

- **Version scheme:** the blueprint package uses calendar-independent semantic versioning
  (`MAJOR.MINOR.PATCH`), independent of phlo core releases. A MAJOR bump is required when a
  release changes the generated project's contract in a way that breaks projects scaffolded by
  the previous MAJOR (including a required move to a newer exact phlo pin).
- **Every blueprint release pins exact released phlo-family versions** (concern 2). A blueprint
  release never floats ahead of a published phlo release; if a needed fix exists only on
  `main`, the fix is released as a phlo version first, then pinned.
- **Artifact harness reuse (Plan 015 / ADR 0050), no duplication.** Blueprint releases flow
  through the same staged-candidate mechanics the release-promotion contract defines —
  built once, identified by SHA-256 content digests, staged immutably, promoted without
  rebuild, gated by evidence — but with a **blueprint-scoped BOM**, containing:
  1. the `phlo-retail-files` sdist and wheel;
  2. the exact phlo-family distributions pinned by concern 2 (by digest, as consumed at
     qualification time);
  3. the blueprint commit SHA.
  The blueprint BOM is separate from (and never merged into) a phlo-release BOM; nothing in
  this contract authorises publishing or promoting phlo core artifacts.
- **Support classification is separate**, per ADR 0050 concern 7: `registry/support/v1.json`
  records the blueprint's support classification through normal reviewed changes on `main`,
  and is neither a promotion gate nor a promotion output for blueprint releases.

### 5. Bounded starter and evidence contract (normative)

The distributed template ships the **bounded starter**: the deterministic default-scale fixture
set and the workflow tree as they exist in `examples/lakehouses/retail-files/` at the release
commit (25 stores × 500 products × 30 days × 80 sales lines per store/day → 60,000 sales lines
in 750 CSV files and 375,000 NDJSON inventory snapshots).

The starter is qualified against a frozen evidence contract; a blueprint release that cannot
reproduce this evidence is not promotable:

- **Runtime bound:** from a clean host, `scripts/generate_fixtures.py --scale default`, the
  test suite, and the first daily-partition materialization complete without network access
  beyond the local compose stack (`services init/start`, Nessie, MinIO, Trino, Dagster).
- **Failure bound:** the intentional-failure demonstrations hold — removing one expected store
  CSV fails ingestion before staging; the duplicate/unknown-product/bad-arithmetic fixture
  sets fail their checks; a terminal failed Dagster run updates the durable WAP report to
  `failed` and **leaves published data unchanged** (`docs/retail-files-e2e.md`).
- **Evidence bound (exact released-pin qualification):** the published catalog contains
  exactly **12 tables** with the verified row counts — `retail_products` 500, `retail_stores`
  25, `retail_promotions` 2, `retail_inventory` 12,560, `retail_sales_lines` 4,000,
  `product_dimension` 500, `store_dimension` 25, `sales_facts` 4,000, `inventory_balances`
  12,500, `daily_store_mart` 50, `product_category_performance` 120, `stockout_reorder`
  12,500 — and the S001/2025-01-01 daily mart returns 80 lines, 40 transactions, gross
  6,100.80, discount 62.84, tax 483.03, net 6,520.99. These counts are the pass/fail oracle
  for blueprint-release qualification and are re-verified per release.

**Rejected:** shipping `--scale test` fixtures as the starter, unbounded or randomized fixture
generation, network-fetched sample data, and any relaxation of the 12-table oracle without an
ADR amendment.

### 6. Resource ownership and cleanup

Ownership of everything the blueprint touches is fixed as follows:

- **Generated files:** owned by the consumer's project the moment `phlo init` writes them. The
  blueprint never rewrites, migrates, or deletes generated files on upgrade; a new release
  affects only projects scaffolded *after* it is installed.
- **WAP staging branches and staged Iceberg data:** owned by the **composition** — the
  generated project's own workflows and the WAP machinery configured in its `phlo.yaml`
  (`wap.enabled: true`, job `retail_wap_job`) perform branch creation and the normal
  audit-retention cleanup; core owns the WAP mechanics, never the blueprint's branches.
- **Local services:** owned by the generated project's compose stack, started and stopped with
  `phlo services start` / `phlo services stop` like any other phlo project.
- **Uninstall:** `pip uninstall phlo-retail-files` removes only the installed package bytes and
  its entry point. It deletes nothing from any project, catalog, or volume — blueprint
  cleanup of deployed resources is out of scope by construction.

**Rejected:** core-side cleanup jobs for blueprint resources, an uninstall hook that removes
generated files, and shared/global services implicitly created outside the generated project's
compose stack.

### Decision table

| # | Concern | Decision |
| --- | --- | --- |
| 1 | Blueprint definition | One `phlo.project_templates` entry point per distribution; one template (`retail-files`); project-owned generated files; composition-owned package |
| 2 | Dependencies | Exact released pins for all phlo-family deps; third-party allowlist = `pandas`, `pyarrow`, `duckdb`, `dbt-duckdb`; no VCS/path/editable/floating |
| 3a | Install routes | Direct install and `phlo[blueprints]` only — exactly two routes, both opt-in |
| 3b | Support-promise boundary | `phlo-retail-files` never enters `defaults` or `core-services`; no new CLI/core surface |
| 3c | Discovery seam | `phlo.project_templates` entry-point group via `src/phlo/cli/templates/registry.py`; name collisions fail loudly |
| 4a | Versioning | Semver, independent of phlo core; MAJOR bump on generated-project contract breaks |
| 4b | Release promotion | Plan 015 artifact-harness reuse: blueprint-scoped BOM, digest identity, staged once, no rebuild, evidence-gated |
| 4c | Support manifest | `registry/support/v1.json` classification separate from promotion (ADR 0050 concern 7) |
| 5 | Starter + evidence | Bounded deterministic starter; network-free runtime bound; failure leaves published data unchanged; 12-table/row-count oracle per release |
| 6 | Ownership + cleanup | Generated files consumer-owned; WAP branches composition-owned; services project-owned; uninstall removes package bytes only |

## Alternatives considered

1. **Add the blueprint to `phlo[defaults]`.** Rejected: it widens the v1 support promise to
   every phlo user and couples core release cadence to a retail analytics example.
2. **Ship it as a `packages/*` workspace package.** Rejected: it would enter the phlo release
   BOM under ADR 0050, making core releases gate on example qualification and vice versa; the
   composition owns this example, not core.
3. **Monorepo-clone instructions in the docs.** Rejected: this is today's gap — `phlo init`
   must reach the blueprint from PyPI artifacts alone.
4. **A generic scenario/framework package parameterised per example.** Rejected for v1: the
   second candidate (SaaS Product Analytics) stays blocked until this per-example contract is
   proven; generalising now would freeze the wrong abstraction.
5. **Floating phlo dependencies with a compatibility matrix.** Rejected: floating pins
   contradict the exact-artifact identity ADR 0050 builds promotion on, and make the evidence
   oracle (concern 5) unreproducible.

## Consequences

**Positive.** `phlo init --template retail-files` works from a PyPI install with no monorepo
clone. The v1 support promise (`defaults` / `core-services`) is untouched. The 12-table
evidence oracle gives every blueprint release a machine-checkable pass/fail gate. #851–#853
can be implemented from this contract without inventing policy, and #854 (provider trust
tiers) is unblocked.

**Costs and follow-through.** #851 must replace the example's VCS dependencies with exact
released pins, add the `blueprints` extra to the root `pyproject.toml`, and stand up the
blueprint-scoped BOM on the Plan 015 harness; until then the example remains clone-only. The
root `pyproject.toml` gains one extra (additive, opt-in). Each blueprint release re-runs the
full starter qualification against its pinned phlo versions.

**Neutral.** No runtime code, no schema change, and no example modification is authorised by
this ADR. `registry/support/v1.json` and `scripts/validate_support_manifest.py` are unchanged;
`src/phlo/cli/templates/registry.py` needs no change — it already implements the discovery
seam this contract freezes.

## Successor seams

- **#851 (package implementation):** create `phlo-retail-files` from
  `examples/lakehouses/retail-files/` per concerns 1–2; add the `blueprints` extra (concern
  3a); wire the blueprint-scoped BOM onto the Plan 015 harness (concern 4b).
- **#852/#853:** release mechanics and the `phlo[blueprints]` extra publication per concerns
  3–4.
- **Second candidate (SaaS Product Analytics):** may reuse this contract verbatim — new
  distribution, same entry-point group, same pin/allowlist discipline, its own evidence
  oracle — after this contract has proven stable through one real release.

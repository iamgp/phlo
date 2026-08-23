---
title: "Lakehouse examples tracker"
type: plan
status: in-progress
date: 2026-08-21
origin: thread/T-01a0263f-ffde-7638-9367-c2eb640c7149
---

# Lakehouse examples tracker

## Purpose

Build a set of independent, runnable Phlo lakehouses that exercise realistic
source systems, workflow layouts, transformations, quality controls, storage
profiles, and operational failure modes. These are usage examples and an
ergonomics/compatibility suite: an example that exposes a product limitation is
valuable even when its first end-to-end result is not green.

Live external sources must have deterministic local fixtures or a replay mode so
CI does not depend on credentials, public API availability, or rate limits.

## Status legend

- **Planned**: scope agreed; implementation has not started.
- **In progress**: at least one delivery checkpoint is underway.
- **Blocked**: implementation found a Phlo capability gap that prevents the
  intended outcome; link the issue or follow-up plan in Notes.
- **Complete**: all delivery checkpoints pass, including the documented
  end-to-end scenario.
- Checkpoints: **Scaffold**, **Data**, **Pipeline**, **Quality**, **E2E**, and
  **Docs**. Change `⬜` to `✅` only when that checkpoint is reviewable and
  verified; use `🚧` while actively working on it.

## Example tracker

| # | Lakehouse | Status | Workflow organization | Sources and ingestion | Transformations | Quality and operational stress | Profile | Anticipated outcome | Scaffold | Data | Pipeline | Quality | E2E | Docs | Notes |
|---:|---|---|---|---|---|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| 1 | Retail Files | Complete | Technical/domain: `ingestion/retail`, shared `schemas`, `quality`, `schedules`, and central dbt | DLT; per-store/day CSV sales, JSON product/store/promotion references, NDJSON inventory, Parquet archive | Sales facts, product/store dimensions, append-ledger inventory deduplication, daily store marts, category performance, stockout/reorder | Malformed files, duplicates, missing store files, referential integrity, revenue reconciliation, native dbt check evidence, sequential WAP replay | Blessed Iceberg stack | A network-free golden path; replay is idempotent and bad partitions do not promote | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Live E2E produced 12 Iceberg tables from 25 stores, 500 products, 60,000 generated sales rows, and 375,000 inventory snapshots. Five schedules and differentiated asset contracts verified. A two-partition WAP backfill promoted sequentially; native dbt checks passed and a missing partition failed without changing published data. See the [case study](../../examples/lakehouses/retail-files/docs/retail-files-e2e.md). |
| 2 | SaaS Product Analytics | Complete | Domain-first: `product_analytics/{ingestion,schemas,quality,transforms,tests}` with one dbt runtime | DLT; paginated nested REST API, replay server, account-plan CSV | Flatten events, sessionization, activation, retention, feature adoption, release impact | Pagination completeness, rate limits/retries, schema evolution, accepted event types, session ordering, freshness | Blessed Iceberg stack | Incremental retries add only new events and optional API fields evolve safely | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | [Case study](../../examples/lakehouses/saas-product-analytics/docs/saas-product-analytics-e2e.md) |
| 3 | E-commerce Replication | Complete | Source plus domain: `sources/commerce_postgres`, `domains/{customers,orders}`, central dbt | Sling; PostgreSQL customers, orders, lines, products, payments, config; full refresh, incremental, and snapshot modes | Order lifecycle facts, customer dimensions, revenue marts | Watermarks, composite keys, source updates, order-line/order and payment reconciliation | Iceberg stack + optional Sling | Source updates replicate without full reloads and all replication modes coexist predictably | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Verified E2E on the glibc runtime image (#766): six Sling assets materialized through Dagster/WAP, deltas replicate without reload (1,450 distinct orders from 1,506 raw rows), snapshot history accumulates, all four dbt models and checks pass. Sling's Iceberg target is append-only for incremental mode upstream, so updated rows arrive as extra versions and the central dbt models deduplicate latest-version-wins. See the [case study](../../examples/lakehouses/ecommerce-replication/docs/ecommerce-replication-e2e.md). |
| 4 | IoT Telemetry | Complete | Pipeline-stage: `ingest`, `normalize`, `aggregate`, `quality`, `publish` | DLT; generated NDJSON, compressed hourly files, device registry DB, late events | Deduplication, late-event correction, hourly health and daily fleet summaries | Hourly partitions, sequence monotonicity, physical bounds, duplicate thresholds, missing devices, file-count pressure | Blessed Iceberg stack | Reprocessing repairs aggregates without duplicating raw events and exposes practical volume/maintenance limits | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Verified live E2E on the blessed stack: 11 assets promoted through WAP; raw append of a replayed day doubles rows (533 to 1,066) while distinct messages stay 528 through dedup and aggregates; corrections overlay verified (calibration offset and drift fix); out-of-bounds batch failed closed with the catalog unchanged; four stopped schedules registered with distinct cadences. |
| 5 | Market Data and FX | Planned | Domain-first: `markets/{prices,foreign_exchange,reference_data}` plus central dbt | DLT; equities API, FX API, security master CSV, trading calendar; live/replay modes | Currency and timezone normalization, returns, volatility, drawdown, exposure | OHLC relationships, numeric precision, FX tolerance checks, calendar-aware gaps, correction backfills | Blessed Iceberg stack | Fixture portfolios produce exact metrics; valid market closures pass while missing observations fail | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| 6 | Healthcare Claims | Planned | Bounded domains: `claims`, `eligibility`, `providers`, `shared/contracts`, central dbt | DLT; CSV claims, pipe-delimited eligibility, JSON providers, invalid claim fixtures | Code/array normalization, temporal eligibility joins, utilization and cost marts | Strict Pandera contracts, claim reconciliation, duplicate versions, temporal validity, curated-output privacy rules | Blessed Iceberg stack | Valid claims promote; invalid partitions remain isolated with useful but non-sensitive diagnostics | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| 7 | Logistics Control Tower | Planned | Hybrid with repeated Python transform folders: `orders/transforms`, `carriers/transforms`, `warehouses/transforms`, `control_tower/transforms` | Sling PostgreSQL orders; DLT carrier APIs and warehouse CSV scans | Domain-local Python normalization plus canonical shipment state, transit duration, exceptions, and SLA marts | Recursive discovery, explicit cross-folder dependencies, name collisions, event state ordering, carrier coverage, SLA calculations | Iceberg stack + optional Sling | Heterogeneous sources converge on known shipment states and contradictory events become visible failures | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| 8 | Customer 360 | Planned | Domain-colocated: `commerce`, `support`, and `marketing` each own `ingestion`, `transforms`, and `quality`; one central dbt project references multiple model paths | Sling commerce DB; DLT support API, contacts CSV, consent JSON events | Multiple domain-local SQL transform roots; identity resolution, type-2 customer dimension, consent-safe products | Multi-root dbt compilation/lineage, nonoverlapping validity, one current row, consent precedence, source reconciliation | Iceberg stack + optional Sling | One manifest includes every domain transform root; known identities converge and consent violations block publication | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | Tests the supported multiple-transform-folder pattern |
| 9 | Public Data Research | Planned | Source-oriented ingestion and subject-oriented models: `sources/{civic_api,weather_files,demographics}`, `research/{places,indicators}` | DLT; public API, ZIP/CSV bulk files, GeoJSON metadata, annual demographic files | Geographic normalization, unit conversion, mixed temporal grains, place/date indicators | Daily/monthly/annual partitions, schema drift, geographic coverage, rollup reconciliation, upstream revisions | Blessed Iceberg stack | Researchers can reproduce an old result with time travel and compare it with revised source data | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| 10 | WAP Failure and Recovery Lab | Planned | Runbook/scenario: `scenarios/{valid_publish,quality_failure,schema_change,retry_recovery,concurrent_runs}` | DLT; generated valid, null, duplicate, stale, and schema-changing batches | Minimal transforms so branch lifecycle and recovery remain the focus | Every built-in check family; blocking/warning behavior; branch creation, concurrent runs, promotion, retention, cleanup, retries | Blessed versioned Iceberg/Nessie stack | Passing runs promote atomically; failed runs leave `main` unchanged and retain reproducible evidence | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| 11 | Delta Portability | Planned | Conventional layout matching an Iceberg example to isolate the provider change | DLT plus small Sling PostgreSQL source; CSV and REST replay fixtures | Provider-neutral dbt models, schema evolution, time travel, maintenance inspection | Equivalent-value contract versus Iceberg, merge idempotency, explicit absence of WAP semantics | Preview Delta, non-versioned | Workflow code remains mostly neutral and provider-specific guarantees are documented precisely | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | Preview profile |
| 12 | ClickHouse Operational Analytics | Planned | Product/service domains: `platform_events`, `access_logs`, `accounts`, `operational_marts`, `quality` | DLT events/logs plus Sling PostgreSQL metadata | dbt-clickhouse error rate, latency, throughput, and tenant-usage marts | Deduplication, bounds, per-tenant freshness, count reconciliation, modest query-latency target | Preview ClickHouse as store, query engine, and publish target | One provider fills three data-plane roles and reveals assumptions coupled to Iceberg/Trino | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | Preview profile |
| 13 | Federated Domains | Planned | Multiple independent projects: `sales/transforms/dbt`, `finance/transforms/dbt`, `operations/transforms/dbt`, each with ingestion and quality | DLT and/or Sling sources owned independently by each domain | Separate dbt project, profile, manifest, selectors, and cross-project contracts per domain | Multiple-project discovery, asset collisions, runtime refs, cross-project lineage, coordinated WAP | Boundary probe on blessed stack | Expected initially to expose the current single-active-dbt-project limitation, then track the product work needed for safe federation | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | Do not mark Blocked until implementation verifies the boundary |

## Delivery checkpoint definitions

| Checkpoint | Complete when |
|---|---|
| Scaffold | The independent project installs into its own uv-managed `.venv`, imports packaged Phlo rather than repository source, validates its configuration, and Phlo discovers its workflow modules, assets, schedules, checks, and dependencies. |
| Data | Deterministic fixtures or generators exist; external sources have replay mode; intentional invalid cases are labeled. |
| Pipeline | Phlo materializes ingestion and transformation assets through the orchestrator and writes the documented tables with explicit dependencies and lineage. Direct helper scripts or direct provider commands are diagnostic paths, not completion evidence. |
| Quality | Schema, business, and operational checks cover both passing and intentional failing cases. |
| E2E | The documented representative `phlo materialize` and/or `phlo backfill` scenario has been executed against its intended profile; registered schedules and asset configuration are inspected; catalog data, checks, lineage, and applicable WAP evidence pass decisive assertions; or a verified capability gap is recorded. |
| Docs | The example README explains setup, architecture, commands, expected outputs, expected failures, and profile maturity. |

## Orchestration and asset-configuration coverage

Exact schedules may move to avoid collisions when the projects are implemented,
but each example must retain the behavioral difference described here. Asset
settings must be justified by source behavior rather than varied arbitrarily.

| # | Lakehouse | Scheduling and partition behavior | Asset-configuration focus |
|---:|---|---|---|
| 1 | Retail Files | Hourly inventory snapshots, nightly per-store sales after file arrival, weekly reference refresh; daily sales backfill | Append inventory history; merge transaction lines and products by stable keys; distinct freshness, retry, timeout, strict-validation, owner, consumer, and SLA settings |
| 2 | SaaS Product Analytics | Hourly cursor ingestion with a daily cohort rebuild | API retry/backoff and runtime limits, incremental merge, nested-schema evolution, hourly freshness, nonblocking drift warning versus blocking contract checks |
| 3 | E-commerce Replication | Frequent order/payment incrementals, nightly reference refresh, periodic customer snapshots | Sling incremental, full-refresh, and snapshot modes; update and primary keys; source-pressure-aware concurrency and freshness by stream |
| 4 | IoT Telemetry | Hourly partitions with rolling late-data repair and bounded parallel backfills | Append telemetry, merge correction aggregates, short freshness windows, higher retry budget, maintenance thresholds for file pressure |
| 5 | Market Data and FX | Trading-calendar-aware weekday runs plus historical correction backfills | Merge corrected observations, market-specific timeouts/freshness, strict numeric validation, warning tolerances separated from blocking reconciliation |
| 6 | Healthcare Claims | Daily claim/eligibility file arrival with ordered downstream execution | Strict validation and blocking publication, conservative retries, longer runtime, regulated ownership/consumer metadata, failure refs retained for review |
| 7 | Logistics Control Tower | Different carrier polling cadences, database incrementals, warehouse batch schedule, downstream SLA evaluation | Provider-specific retry/runtime choices, canonical dependencies across schedules, incremental replication plus API merge, late-event handling |
| 8 | Customer 360 | Independent commerce/support/marketing schedules followed by a coordinated product build | Domain owners/consumers/SLAs, type-2 merge behavior, consent checks blocking only affected publish products, one dbt manifest across model roots |
| 9 | Public Data Research | Daily, monthly, and annual partition definitions with large selective backfills | Long runtimes and retries for bulk downloads, merge upstream revisions, source-specific freshness, snapshot/time-travel metadata |
| 10 | WAP Failure and Recovery Lab | Mostly manual scenario launches plus promotion/cleanup sensors and concurrent scheduled runs | Deliberately varied blocking/warning checks, retry policies, WAP enabled/disabled comparison, branch retention and cleanup settings |
| 11 | Delta Portability | Same schedule and partition contract as its Iceberg comparison | Explicit `table_store: delta` routing, no versioned-catalog assumptions, equivalent merge/retry/freshness settings for portability comparison |
| 12 | ClickHouse Operational Analytics | Frequent micro-batches and hourly aggregate refresh | Explicit ClickHouse capability routing for store/query/publish roles, append versus replacing aggregates, short freshness and bounded runtime |
| 13 | Federated Domains | Independently owned domain schedules plus a coordinated cross-domain target | Separate project manifests/profiles, collision-safe asset keys, domain runtime refs and ownership, explicit behavior when cross-project coordination is unsupported |

## Suite-level completion criteria

- Every example is independent and does not rely on another example's runtime
  state.
- Every example uses its own uv-managed environment and imports version-pinned
  Phlo packages from that environment; repository development environments,
  editable repository dependencies, and source-path injection are prohibited.
- The suite covers files, APIs, databases, DLT, Sling, Python transforms, dbt,
  partitions, backfills, schema evolution, quality failures, lineage, WAP,
  publishing, and alternative table stores.
- Direct DLT, dbt, Sling, or helper execution may provide focused diagnostics,
  but only Phlo-launched asset materialization/backfill counts as end-to-end
  completion. Registered schedules and intentionally different asset settings
  must be verified as part of each completed example.
- At least one project uses multiple recursively discovered Python transform
  folders.
- At least one project uses one dbt project with multiple domain-local model
  paths.
- The federated example records the verified behavior of multiple independent
  dbt projects; unsupported behavior is never presented as supported.
- Each completed example has a deterministic CI path and a documented optional
  live path where applicable.

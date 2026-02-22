# Part 2: Build Your First Phlo Project

> Prerequisite: Read [Part 1](01-what-is-data-engineering.md).

## What You'll Learn

- How to initialize a project with `phlo init`
- How to start core services and validate runtime health
- How project structure maps to ingestion, schemas, and dbt
- How to run your first materialization command safely

## Prerequisites

- Docker running locally
- Python 3.11+
- `phlo` installed in your environment

## Initialize the Project

```bash
phlo init my-first-phlo-project
cd my-first-phlo-project
```

Expected output:

```text
Creates phlo.yaml, workflows/, tests/, and dbt scaffold under workflows/transforms/dbt.
```

## Understand the Generated Layout

```text
my-first-phlo-project/
  phlo.yaml
  workflows/
    ingestion/
    schemas/
    transforms/dbt/
  tests/
```


## Start the Infrastructure

```bash
phlo services init
phlo services start
```

Expected output:

```text
Compose files generated in .phlo/ and core services start in Docker.
```

Check runtime inventory:

```bash
phlo services list --json
```

Expected output:

```json
[
  {
    "name": "minio",
    "running": true
  },
  {
    "name": "dagster",
    "running": true
  }
]
```

## Verify Data-Platform Readiness

```bash
phlo status --services
```


## First Materialization Dry Run

Use dry-run first so you can verify command shape without mutating state.

```bash
phlo materialize dlt_glucose_entries --dry-run
```

Expected output:

```text
Prints docker exec dagster asset materialize command with selected asset.
```

## Why This Project Shape Matters

- `workflows/ingestion`: source-to-raw contracts
- `workflows/schemas`: Pandera models that define expected data
- `workflows/transforms/dbt`: SQL business logic and tests
- `tests/`: regression and pipeline checks

That layout gives you predictable boundaries as the project grows.

## Deep Dive: Why Bootstrapping Quality Matters More Than Speed

At project start, teams usually optimise for \"first success\". That is valid, but many teams accidentally encode weak defaults:

- No naming convention for assets
- No schema ownership
- No clear branch strategy
- No environment discipline

Those shortcuts are cheap in week one and expensive by month three.

A strong bootstrap is a force multiplier because every future feature inherits those choices.

Use this framing:

- Bootstrapping is not setup work.
- Bootstrapping is architecture work.

## Deep Dive: What `phlo init` Gives You Operationally

`phlo init` provides more than folders:

- A predictable root config (`phlo.yaml`)
- Standardized workflow locations
- dbt project location compatible with Phlo discovery (`workflows/transforms/dbt`)
- Test folder convention that supports asset-focused validation

That means engineers can move between projects without relearning structure.

Example first-day checklist:

```text
1. Confirm project root and naming.
2. Confirm .phlo directory and generated compose files.
3. Confirm service inventory from phlo services list.
4. Confirm at least one materialize dry-run works.
5. Confirm schema and workflow validation commands run.
```


## Guided Walkthrough: From Empty Directory to Ready Platform

Step 1: Initialize

```bash
phlo init my-first-phlo-project
cd my-first-phlo-project
```

Expected output:

```text
Project scaffold created with workflows, tests, and baseline config files.
```

Step 2: Inspect generated config

```bash
cat phlo.yaml
```


Step 3: Initialize service composition

```bash
phlo services init
```

Expected output:

```text
Creates .phlo/docker-compose.yml and related runtime config files.
```

Step 4: Start services

```bash
phlo services start
```


Step 5: Verify running state

```bash
phlo services status
phlo services list --json
```

Expected output:

```text
Service status table and JSON list including running/stopped flags.
```

Step 6: Validate workflow tooling

```bash
phlo workflow create --type ingestion --domain commerce --table orders --unique-key order_id --cron \"0 * * * *\"
```


Step 7: Validate generated workflow contract

```bash
phlo validate-workflow workflows/ingestion/commerce/orders.py
```

Expected output:

```text
Validation summary with contract and decorator diagnostics.
```

At this point, you have the minimum viable platform loop:

- project setup
- services
- workflow scaffold
- validation

That loop is your baseline for all future work.

## Naming Conventions That Save Time Later

Recommended choices from day one:

- Domains as stable business language: `commerce`, `billing`, `support`
- Table names in lowercase snake case: `orders`, `refund_events`
- Ingestion assets with `dlt_<table>`
- Schema classes prefixed by data zone intent: `RawOrders`, `SilverOrders`

Why this matters:

- Better grep/search ergonomics
- Fewer accidental collisions
- Easier lineage readability

## Environment Discipline: Local, Branch, and CI

Even in early stage projects, define environment behaviour clearly:

- Local:
  quick iteration, sample data, dry-runs encouraged.
- Branch:
  full workflow checks for changed assets.
- CI:
  gate on lint/type/test/docs and contract checks.

Simple rule:

- If a command is required before merge, document it near setup docs.

## Setup Anti-Patterns

Anti-pattern 1: \"One global project for everything\"

- Result: domain coupling, noisy ownership, conflicting changes.
- Better: one project per bounded business area when possible.

Anti-pattern 2: \"Skip validations until real data arrives\"

- Result: schema and workflow mistakes discovered too late.
- Better: run `phlo validate-workflow` at scaffold time.

Anti-pattern 3: \"Ad hoc service starts\"

- Result: inconsistent local states and confusing bug reports.
- Better: use standard `phlo services ...` commands and capture versions.

Anti-pattern 4: \"No startup health checklist\"

- Result: silent partial startup interpreted as success.
- Better: status + list checks every time.

## Team Onboarding Pattern

When a new engineer joins, give them this 30-minute flow:

1. Initialize a clean sample project.
2. Start services and verify status.
3. Scaffold one ingestion workflow.
4. Run one dry-run materialization command.
5. Explain each folder responsibility.

If they can do this unaided, they can usually ship meaningful features quickly.

## Mini Lab: Build and Validate a Realistic Domain Skeleton

Use a domain you care about, for example \"subscriptions\".

Run:

```bash
phlo workflow create --type ingestion --domain subscriptions --table invoices --unique-key invoice_id --cron \"0 */2 * * *\"
phlo validate-workflow workflows/ingestion/subscriptions/invoices.py
phlo schema list --domain subscriptions
```


Then answer:

1. What is the critical key?
2. What is acceptable data latency?
3. Which checks should block downstream?

This turns setup into platform thinking immediately.

## Production-minded Setup Checklist

Before you call setup complete, verify:

- Commands reproducible from clean checkout
- Service list output understandable to new team members
- One scaffolded workflow passes validation
- One documented \"golden path\" run exists
- Troubleshooting links are present in internal docs

This checklist is small and saves days of confusion over the life of the project.

## Extended Guide: Designing a Good Developer Experience

A strong local developer experience is one of the highest leverage investments you can make early.

Your target is simple:

- New engineer can start project reliably
- They can run one end-to-end path in under an hour
- Failure messages are actionable

Practical tactics:

1. Document startup order explicitly.
2. Keep command examples copy-paste ready.
3. Prefer deterministic paths over \"magic\" defaults.
4. Capture known gotchas close to setup docs.

Example startup runbook snippet:

```text
If services fail to start:
  1. Confirm Docker is running.
  2. Run phlo services status.
  3. Check port conflicts.
  4. Restart only impacted services.
```


You can also add a simple first-run script for local onboarding:

```bash
#!/usr/bin/env bash
set -euo pipefail

phlo services init
phlo services start
phlo services status
phlo services list --json
```

Expected output:

```text
Service stack initializes, starts, then reports current status and inventory.
```

When onboarding pain is low, platform adoption rises naturally.

## Extended Guide: Configuration Hygiene from Day One

Most long-term instability comes from drifting configuration, not missing features.

Use these guardrails:

- Keep project config in `phlo.yaml` and treat it as reviewed code.
- Avoid hidden one-off local tweaks that are never documented.
- Keep secret material out of tracked files.
- Prefer environment variable naming that is explicit and discoverable.

A clear config review question set:

1. Is this environment-specific or globally expected?
2. Is this value safe to commit?
3. What fails if this key is missing?
4. Should this change require a runbook update?

Configuration examples should include expected output in docs:

```yaml
services:
  dagster:
    enabled: true
  trino:
    enabled: true
```


If a setting changes runtime behaviour, write a one-line rationale near the change.

## Extended Guide: First-Week Project Milestones

Week-one milestones for a new Phlo project:

Day 1:

- Setup complete
- Services healthy
- One scaffolded workflow exists

Day 2:

- One ingestion asset materialized successfully
- One schema validated

Day 3:

- One dbt model runs and tests pass
- One quality check integrated

Day 4:

- Status/logs/metrics baseline captured
- One backfill dry-run validated

Day 5:

- Team runbook updated with known issues
- Ownership map documented

This pace is realistic for small teams and creates strong foundations.

## Extended Guide: How to Explain the Project to Stakeholders

Non-data stakeholders often ask, \"When can we trust the numbers?\"

A helpful answer:

- We trust numbers when ingestion, transformation, and quality checks all pass.
- We can prove this with status, logs, metrics, and lineage traces.
- We can safely replay data when source issues are fixed.

This framing shifts conversation from \"is pipeline done\" to \"is data product reliable.\"

## Extended Guide: Preparing for Scale Early

You do not need enterprise complexity on day one. But you do need choices that do not block growth.

Scale-friendly choices now:

- Stable naming conventions
- Partition-aware ingestion contracts
- Explicit quality checks
- Branch-based table change process
- Basic incident response template

These are small commitments with large long-term payoffs.

## Quick Self-Assessment

Score each item from 0 (not started) to 2 (solid):

- Setup reproducibility
- Service startup reliability
- Workflow scaffold quality
- Contract validation usage
- Team onboarding speed

Total score guide:

- 0-3: setup still fragile
- 4-7: functional but risky
- 8-10: strong baseline for feature development

Use this as a checkpoint before scaling the number of workflows.

## Mini Case Study: Setup Debt vs Setup Discipline

Two teams start the same quarter.

Team A treats setup as temporary and undocumented. Team B treats setup as an engineering artifact and writes clear startup checks.

After six weeks:

- Team A spends significant time on \"works on my machine\" failures.
- Team B onboards new engineers quickly and spends time on product features.

The codebases may look similar, but operational behaviour diverges heavily.

This is why setup quality is not optional polish. It is foundational throughput.

If you remember one principle from this post, use this:

make startup paths boring, deterministic, and documented. Boring setup is what lets the interesting platform work move fast.

That single discipline compounds across every new workflow, every onboarding session, and every incident you will handle later.
It is one of the few early habits that scales without rework.
Keep it deliberate and consistent across teams.

## Hands-On Exercise

1. Run `phlo workflow create` and scaffold one ingestion workflow.
2. Open generated schema and ingestion files.
3. Replace placeholder fields with your own domain fields.
4. Run `phlo validate-workflow <path-to-file>` on your new workflow.

## Common Issues

1. `phlo services start` fails because Docker daemon is not running.
2. `phlo services status --json` is attempted, but `services status` has no JSON mode.
3. `phlo materialize` fails because Dagster container is not up yet.
4. Project root confusion causes commands to run outside the initialized folder.
5. Missing package plugins lead to missing command groups.

Use [Troubleshooting](../../operations/troubleshooting.md) when service startup or command discovery fails.

## Summary

You now have a runnable Phlo project with infrastructure, standard folder boundaries, and a safe first-run workflow.

## Next Steps

1. Move to [Part 3](03-ingestion-foundations-with-dlt.md) and build ingestion contracts.
2. Keep your project running; you will reuse it in every post.

## See Also

- [Part 3: Ingestion Foundations with DLT](03-ingestion-foundations-with-dlt.md)
- [Part 5: Orchestration with Dagster Assets](05-orchestration-with-dagster-assets.md)
- [CLI Reference](../../reference/cli-reference.md)

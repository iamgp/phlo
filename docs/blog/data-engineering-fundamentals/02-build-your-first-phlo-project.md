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

For this series, use a real public demo source so orchestration commands are runnable end-to-end:

- API: `https://fakestoreapi.com`
- Resource path: `products`
- Primary key in raw schema: `id`

## Initialize the Project

```bash
phlo init my-first-phlo-project
cd my-first-phlo-project
```

If everything is wired correctly, you should see output along these lines:

```text
Project scaffold created with phlo.yaml, workflows/, and tests/.
```

## Understand the Generated Layout

```text
my-first-phlo-project/
  contracts/
  data/
  phlo.yaml
  plugins/
  workflows/
    ingestion/
    schemas/
    transforms/dbt/
  tests/
```


## Start the Infrastructure

```bash
phlo services init --force
phlo services start
phlo services list --json
```

On a healthy setup, you will see something similar:

```text
Generated service configuration under .phlo/.
Starting services...
```

Check runtime inventory:

```bash
phlo services list --json
```

The command should return something like this:

```text
[
  {"name": "minio", "category": "core", "default": true},
  {"name": "dagster", "category": "core", "default": true}
]
```

## Verify Data-Platform Readiness

```bash
phlo status --services
```

If Docker and the stack are up, you should see core services reported as healthy (for example Dagster, MinIO, Nessie, and Trino all reachable). If you see `Down` or `Timeout`, stop here and fix service startup before moving on.


## Create Your First Ingestion Asset

```bash
phlo workflow create --type ingestion --domain commerce --table orders --unique-key id --cron "0 * * * *" --api-base-url "https://fakestoreapi.com" --field id:int --field title:str --field price:float --field category:str
```

Your output should look roughly like this:

```text
Created ingestion workflow scaffold under workflows/ingestion/commerce/orders.py.
```

At this point, your first asset name is `dlt_orders` (Phlo prefixes ingestion assets as `dlt_<table>`).

The scaffold uses the table name as the default REST endpoint. For Fake Store, open `workflows/ingestion/commerce/orders.py` and replace the generated `resources=` argument in the `rest_api(...)` call:

```python
return rest_api(
    client={
        "base_url": base_url,
    },
    resources=[
        {
            "name": "products",
            "endpoint": {
                "path": "/products",
            },
        }
    ],
)
```

## First Materialization Dry Run

Use dry-run first so you can verify command shape without mutating state.

```bash
phlo materialize dlt_orders --dry-run
```

You should get output similar to this:

```text
Dry-run: would materialize dlt_orders (no state changes applied).
```

## Why This Project Shape Matters

- `workflows/ingestion`: source-to-raw contracts
- `workflows/schemas`: Pandera models that define expected data
- `workflows/transforms/dbt`: SQL business logic and tests
- `tests/`: regression and pipeline checks

That layout gives you predictable boundaries as the project grows.

## Deep Dive: Why Bootstrapping Quality Matters More Than Speed

At project start, teams usually optimise for "first success". That is valid, but many teams accidentally encode weak defaults:

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
5. Confirm the generated pytest file and materialization dry-run pass.
```

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

Anti-pattern 1: "One global project for everything"

- Result: domain coupling, noisy ownership, conflicting changes.
- Better: one project per bounded business area when possible.

Anti-pattern 2: "Skip validations until real data arrives"

- Result: schema and workflow mistakes discovered too late.
- Better: run the generated pytest file and a dry-run materialization before loading data.

Anti-pattern 3: "Ad hoc service starts"

- Result: inconsistent local states and confusing bug reports.
- Better: use standard `phlo services ...` commands and capture versions.

Anti-pattern 4: "No startup health checklist"

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

Use a domain you care about, for example "subscriptions".

Run:

```bash
phlo workflow create --type ingestion --domain subscriptions --table invoices --unique-key id --cron "0 */2 * * *" --api-base-url "https://fakestoreapi.com"
phlo schema list --format table
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
- One documented "golden path" run exists
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
3. Prefer deterministic paths over "magic" defaults.
4. Capture known gotchas close to setup docs.

Example startup runbook snippet:

```text
If services fail to start:
  1. Confirm Docker is running.
  2. Run phlo services list --json.
  3. Check port conflicts.
  4. Restart only impacted services.
```


You can also add a simple first-run script for local onboarding:

```bash
#!/usr/bin/env bash
set -euo pipefail

phlo services init --force
phlo services list --json
```

On a healthy setup, you will see something similar:

```text
Generated service configuration under .phlo/.
[{"name": "minio", "category": "core", "default": true}, ...]
```

When onboarding pain is low, platform adoption rises naturally.

## Hands-On Exercise

1. Run `phlo workflow create` and scaffold one ingestion workflow.
2. Open generated schema and ingestion files.
3. Replace placeholder fields with your own domain fields.
4. Run the generated pytest file and `phlo materialize <asset-name> --dry-run`.

## Common Issues

1. `phlo services list --json` fails because Docker daemon is not running.
2. `phlo services list --json` is attempted, but `services status` has no JSON mode.
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

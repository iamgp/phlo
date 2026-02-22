# Part 6: Transformations with dbt

> Prerequisite: Complete [Part 5](05-orchestration-with-dagster-assets.md).

## What You'll Learn

- Why dbt belongs between raw ingestion and serving layers
- How Phlo discovers dbt projects in `workflows/transforms/dbt`
- How to structure bronze, silver, and gold models
- How to scaffold publishing config for marts

## Prerequisites

- Ingestion assets landing data in Iceberg
- dbt project scaffold under `workflows/transforms/dbt`
- Trino service running

## Where dbt Fits

- Bronze: type cleanup and source normalization
- Silver: business rules and entity logic
- Gold: reporting-ready metrics and dimensions

Model flow:

```mermaid
graph LR
    A[raw.orders] --> B[bronze.stg_orders]
    B --> C[silver.fct_orders]
    C --> D[gold.mrt_revenue_daily]
```

Expected output:

```text
A rendered medallion-style model progression diagram.
```

## Example dbt Model

```sql
-- workflows/transforms/dbt/models/silver/fct_orders.sql
select
  order_id,
  customer_id,
  order_timestamp,
  total_amount,
  case
    when total_amount >= 1000 then 'enterprise'
    when total_amount >= 200 then 'mid_market'
    else 'self_serve'
  end as segment
from {{ ref('stg_orders') }}
```

Expected output:

```text
Template snippet prepared for direct use in your project.
```

## Run dbt from Services

```bash
docker exec dagster-webserver dbt compile
docker exec dagster-webserver dbt run --select fct_orders
docker exec dagster-webserver dbt test --select fct_orders
```

Expected output:

```text
dbt compile, model run, and test summaries with pass/fail counts.
```

## Phlo Publishing Scaffolding

The dbt plugin contributes a `publishing` command group.

```bash
phlo publishing scaffold --config workflows/transforms/dbt/publishing.yaml --select gold.*
```

Expected output:

```text
Creates or updates publishing config for selected dbt models.
```

## Engineering Guidelines

1. Keep raw data assumptions out of gold models.
2. Push type and null handling into bronze models.
3. Keep business logic centralized in silver.
4. Use explicit tests for keys, nullability, and relationships.

## Field Notes: Model Review Conversations That Save You Later

If you work with a team, most dbt pain shows up in review, not runtime.

A familiar example:

- one person prefers "quick model, ship now"
- another wants extra staging models for clarity
- both are trying to help

The easiest way to get stuck is arguing style. The better move is to ask:

1. Can someone new trace this model lineage in five minutes?
2. If this metric is wrong, can we isolate the layer quickly?
3. Would we trust this logic during an incident at 7 AM?

Those three questions usually settle debates fast.

Another practical tip: avoid hiding business logic in macros too early. Macros are powerful, but overuse makes debugging harder for analysts who are strongest in SQL, not Jinja internals.

I usually recommend this progression:

- Start explicit and readable.
- Extract repetition after patterns are stable.
- Keep critical business definitions visible in model SQL.

When teams follow this, handoffs get easier and production defects drop.

One more pattern that works well:

- every gold model PR includes one sentence on "what business question this model answers."

That sentence keeps modeling grounded in user value instead of internal style preferences.

## Hands-On Exercise

1. Create one bronze model and one silver model.
2. Add at least two dbt tests.
3. Run compile, run, and test commands.
4. Record test failures and fix root causes.

## Common Issues

1. dbt project placed outside `workflows/transforms/dbt` and not discovered.
2. Model names drift from downstream expectations.
3. Teams skip dbt tests and debug in dashboards.
4. Gold models mix transformation and serving concerns.
5. Publishing configs become stale after model rename.

For failed commands and environment drift, use [Troubleshooting](../../operations/troubleshooting.md).

## Summary

dbt gives a clean SQL boundary for transformation logic, while Phlo keeps discovery and operational wiring predictable.

## Next Steps

1. Continue to [Part 7](07-quality-checks-with-pandera-and-phlo-quality.md) to enforce contracts and checks.
2. Add model test coverage for every gold output used by stakeholders.

## See Also

- [Part 7: Quality Checks with Pandera and Phlo Quality](07-quality-checks-with-pandera-and-phlo-quality.md)
- [Part 11: Performance and Cost Optimization](11-performance-and-cost-optimization.md)
- [dbt Development Guide](../../guides/dbt-development.md)

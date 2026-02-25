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

The models below use an orders domain schema (`order_id`, `customer_id`, `total_amount`, `order_timestamp`) that is richer than the demo products data from Part 2. Adapt column names to match your own ingested data, or follow these examples as a standalone reference.

## Where dbt Fits

- Bronze: type cleanup and source normalisation
- Silver: business rules and entity logic
- Gold: reporting-ready metrics and dimensions

Model flow:

```mermaid
graph LR
    A[raw.orders] --> B[bronze.stg_orders]
    B --> C[silver.fct_orders]
    C --> D[gold.mrt_revenue_daily]
```


## Example dbt Model

Bronze model (type cleanup and source normalisation):

```sql
-- workflows/transforms/dbt/models/bronze/stg_orders.sql
select
  cast(order_id as varchar) as order_id,
  cast(customer_id as varchar) as customer_id,
  cast(order_timestamp as timestamp) as order_timestamp,
  cast(total_amount as double) as total_amount,
  cast(currency as varchar) as currency
from {{ source('raw', 'orders') }}
where order_id is not null
```

Silver model (business rules and entity logic):

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

Gold model (reporting-ready mart):

```sql
-- workflows/transforms/dbt/models/gold/mrt_revenue_daily.sql
select
  date_trunc('day', order_timestamp) as order_date,
  segment,
  count(*) as order_count,
  sum(total_amount) as total_revenue,
  avg(total_amount) as avg_order_value
from {{ ref('fct_orders') }}
group by 1, 2
```


## Run dbt from Services

```bash
docker exec my-first-phlo-project-dagster-1 dbt compile --project-dir /app/workflows/transforms/dbt
docker exec my-first-phlo-project-dagster-1 dbt run --select stg_orders fct_orders --project-dir /app/workflows/transforms/dbt
docker exec my-first-phlo-project-dagster-1 dbt test --select stg_orders fct_orders --project-dir /app/workflows/transforms/dbt
```

Expected output from `dbt compile`:

```text
Found 3 models, 4 tests, 1 source
Compiled successfully.
```

## Phlo Publishing Scaffolding

The dbt plugin contributes a `publishing` command group.

```bash
docker exec my-first-phlo-project-dagster-1 dbt run --select tag:publish --project-dir /app/workflows/transforms/dbt
```


## Engineering Guidelines

1. Keep raw data assumptions out of gold models.
2. Push type and null handling into bronze models.
3. Keep business logic centralized in silver.
4. Use explicit tests for keys, nullability, and relationships.

## Deep Dive: Incremental Models for Production Scale

Full-refresh models work early but become expensive. Incremental models process only new or changed data.

Example incremental pattern:

```sql
-- workflows/transforms/dbt/models/silver/fct_orders.sql
{{
  config(
    materialized='incremental',
    unique_key='order_id',
    incremental_strategy='merge'
  )
}}

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
{% if is_incremental() %}
where order_timestamp > (select max(order_timestamp) from {{ this }})
{% endif %}
```

When to use incremental:

- Source volume grows daily and full scans are slow
- Upstream data is append-only or has a reliable timestamp
- Reprocessing cost exceeds SLA margin

When to stay full-refresh:

- Small dimension tables
- Logic that requires full dataset context
- Early development when schema is still changing

## Deep Dive: dbt Testing Strategy

dbt tests are your transformation contract layer. Use them deliberately:

```yaml
# workflows/transforms/dbt/models/silver/schema.yml
models:
  - name: fct_orders
    columns:
      - name: order_id
        tests:
          - not_null
          - unique
      - name: total_amount
        tests:
          - not_null
      - name: segment
        tests:
          - accepted_values:
              values: ['enterprise', 'mid_market', 'self_serve']
```

Test tiers:

- **Always run**: primary key uniqueness, not-null on critical fields
- **Run on merge**: accepted values, referential integrity
- **Run weekly**: row count trends, freshness assertions

A practical pattern: run `dbt test` as part of every materialization. If tests fail, downstream assets should not proceed.

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

That sentence keeps modelling grounded in user value instead of internal style preferences.

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
- [Part 11: Performance and Cost Optimisation](11-performance-and-cost-optimization.md)
- [dbt Development Guide](../../guides/dbt-development.md)

# Part 11: Performance and Cost Optimisation

> Prerequisite: Complete [Part 10](10-incident-response-and-debugging.md).

## What You'll Learn

- Where performance bottlenecks usually appear in data platforms
- How partitioning and run strategy affect cost
- How to tune execution safely in Phlo workflows
- How to track optimisation impact with metrics

## Prerequisites

- Running ingestion + transform pipeline
- Baseline metrics from Part 9

## Optimisation Priority Order

1. Correctness first
2. Reliability second
3. Performance third
4. Cost fourth

If you reverse this order, you optimise the wrong thing.

## High-Leverage Levers

- Partition strategy: avoid over-wide daily scans where hourly partitioning is needed
- Backfill concurrency: match source and infra limits
- Model design: prevent repeated expensive joins
- Data movement: publish only what consumers need

## Example: Controlled Backfill Tuning

```bash
phlo backfill dlt_orders --start-date 2025-01-01 --end-date 2025-01-07 --parallel 1
phlo backfill dlt_orders --start-date 2025-01-01 --end-date 2025-01-07 --parallel 2
```

Compare durations to find the highest safe concurrency:

```text
Parallel 1:
Backfill Results
┌───────────┬────────────┐
│ Asset     │ dlt_orders │
│ Status    │ ✓ Success  │
│ Completed │ 7          │
│ Failed    │ 0          │
│ Total     │ 7          │
└───────────┴────────────┘

Parallel 2:
Backfill Results
┌───────────┬────────────┐
│ Asset     │ dlt_orders │
│ Status    │ ✓ Success  │
│ Completed │ 7          │
│ Failed    │ 0          │
│ Total     │ 7          │
└───────────┴────────────┘
```

## Track Performance Before and After

```bash
phlo metrics asset dlt_orders --runs 30
phlo metrics summary --period 7d
```


## Query-Layer Considerations

Keep transformation SQL intentional:

- Select only required columns
- Filter early in bronze/silver layers
- Push heavy joins to well-scoped models
- Reuse tested intermediate models

Example model snippet:

```sql
select
  order_date,
  sum(total_amount) as revenue
from {{ ref('fct_orders') }}
where order_date >= current_date - interval '30' day
group by 1
```


## Deep Dive: Partition Pruning and Scan Reduction

The largest performance gains usually come from reducing data scanned, not faster compute.

Iceberg partition pruning eliminates irrelevant files before query execution. To benefit:

1. Align partition keys with common query filters (usually date).
2. Keep partition granularity matched to query patterns.
3. Use `WHERE` clauses that reference partition columns directly.

Example — a query that benefits from pruning:

```sql
select sum(total_amount) as revenue
from silver.fct_orders
where order_date between date '2025-01-01' and date '2025-01-31'
```

If `fct_orders` is partitioned by `order_date`, Iceberg skips all files outside that range.

Measure scan reduction with:

```bash
phlo metrics asset fct_orders --runs 10
```

Compare row counts and durations before and after adding partition-aligned filters. A 10x scan reduction is common for well-partitioned tables with date filters.

## Cost-Aware Architecture Sketch

```mermaid
graph TD
    A[Source APIs] --> B[Ingestion partitions]
    B --> C[Iceberg snapshots]
    C --> D[dbt incremental models]
    D --> E[Targeted marts]
```


## Field Notes: Avoiding "Fast but Wrong" Optimisation

Performance work can feel addictive. You change one thing, runtime drops, and it feels like progress.

But in data systems, speed wins are only real if correctness stays intact.

A disciplined tuning loop:

1. Capture baseline metrics.
2. Change one variable.
3. Re-run the same workload.
4. Compare runtime, failure rate, and data quality outcomes.
5. Keep or revert.

The "change one variable" step is where most teams slip. They adjust partitioning, concurrency, and SQL in one batch, then cannot explain which change actually helped.

Cost tuning has the same trap. Lower compute cost is good, unless it increases late data or incident frequency. The invoice might improve while user trust gets worse.

A practical compromise:

- pick one monthly cost target and one reliability guardrail.

Example:

- cost target: reduce p95 compute minutes by 10%
- guardrail: no increase in failed critical runs

That keeps optimisation honest.

One more tip: share before/after metrics in pull requests. It forces clarity and builds a knowledge base for future tuning decisions.

## Hands-On Exercise

1. Pick one slow pipeline path.
2. Capture baseline metrics (duration, row counts, failure rate).
3. Apply one change only (for example: backfill parallelism or model filter pushdown).
4. Re-measure and document impact.

## Common Issues

1. Teams tune parallelism without measuring source/API limits.
2. Full-refresh behaviour is triggered accidentally in daily operations.
3. Cost spikes are discovered from bills, not metrics.
4. Teams optimise gold models while bronze quality remains unstable.
5. Performance changes are made with no rollback plan.

Reference for failures during tuning: [Troubleshooting](../../operations/troubleshooting.md)

## Summary

Performance work should be measured, incremental, and reversible. Good optimisation keeps correctness and reliability intact.

## Next Steps

1. Move to [Part 12](12-extending-phlo-with-plugins-and-observatory.md) for platform extension patterns.
2. Add a monthly performance review cadence using exported metrics.

## See Also

- [Part 9: Observability: Metrics, Logs, and Lineage](09-observability-metrics-logs-lineage.md)
- [Part 12: Extending Phlo with Plugins and Observatory](12-extending-phlo-with-plugins-and-observatory.md)
- [Operations Best Practices](../../operations/best-practices.md)

# Part 7: Quality Checks with Pandera and Phlo Quality

> Prerequisite: Complete [Part 6](06-transformations-with-dbt.md).

## What You'll Learn

- How Pandera schemas define enforceable contracts
- How `phlo.quality.pandera` generates asset checks
- When to block downstream runs vs warn
- How to validate schemas and workflow files from CLI

## Prerequisites

- One ingestion asset and one dbt model from prior posts
- Familiarity with basic Pandera schema patterns

## Contract-First Mindset

A schema is not documentation only. It is executable policy.

The examples here use the orders domain schema from Part 6. If you are following along with the demo products API, substitute your own field names.

Example Pandera model:

```python
import pandera as pa
from pandera.typing import Series
from phlo_pandera.schemas import PhloSchema

class RawOrders(PhloSchema):
    order_id: Series[str] = pa.Field(nullable=False)
    customer_id: Series[str] = pa.Field(nullable=False)
    total_amount: Series[float] = pa.Field(ge=0, nullable=False)
    order_timestamp: Series[str] = pa.Field(nullable=False)
```


## Add Declarative Quality Checks

```python
import phlo
from phlo.quality import NullCheck, RangeCheck, FreshnessCheck, CustomSQLCheck

@phlo.quality.pandera(
    table="silver.fct_orders",
    checks=[
        NullCheck(columns=["order_id", "customer_id", "total_amount"]),
        RangeCheck(column="total_amount", min_value=0, max_value=1_000_000),
        FreshnessCheck(timestamp_column="order_timestamp", max_age_hours=2),
        CustomSQLCheck(
            name_="positive_revenue",
            sql="SELECT (total_amount >= 0) AS is_valid FROM data",
        ),
    ],
    group="commerce",
    blocking=True,
)
def orders_quality_gate() -> None:
    pass
```


## Validate Before You Deploy

```bash
phlo schema list --format table
```

Your output should look roughly like this:

```text
Schema         Fields    Module
RawOrders      4         workflows.schemas.orders
```

## Quality Severity Strategy

Use this policy in early production:

- `blocking=True` for identity, key integrity, and contract checks
- warning-only for soft quality metrics during stabilisation
- explicit threshold tuning per domain

## Threshold Tuning and Freshness

Not every check needs zero tolerance. Use `allow_threshold` for soft quality gates:

```python
import phlo
from phlo.quality import NullCheck, RangeCheck, UniqueCheck, FreshnessCheck

@phlo.quality.pandera(
    table="bronze.customer_data",
    checks=[
        NullCheck(columns=["phone", "address"], allow_threshold=0.05),
        RangeCheck(column="age", min_value=0, max_value=150, allow_threshold=0.01),
        UniqueCheck(columns=["customer_id"], allow_threshold=0.005),
        FreshnessCheck(timestamp_column="updated_at", max_age_hours=24),
    ],
    group="crm",
    blocking=True,
)
def customer_quality() -> None:
    pass
```

Key parameters:

- `allow_threshold`: fraction of rows allowed to violate (0.05 = 5%)
- `timestamp_column`: column used by `FreshnessCheck` to measure data age
- `max_age_hours`: maximum acceptable age before check fails

Start strict on critical fields. Loosen thresholds only with evidence from production metrics.

## Signal Flow

```mermaid
graph TD
    A[Data loaded] --> B[Pandera contract check]
    B --> C[Phlo quality checks]
    C --> D[Pass or fail metadata]
    D --> E[Dagster status and logs]
```


## Field Notes: The 6 AM Quality Alert Moment

Quality strategy sounds abstract until the first early-morning failure.

Picture this:

- ingestion succeeded
- transformation succeeded
- then one contract check failed on a field your dashboard depends on

At that point, your policy matters more than your code style.

If the check was blocking, downstream consumers see delayed data but not wrong data.
If it was warning-only, consumers may see numbers that look normal but are now untrustworthy.

There is no universal correct answer. It depends on business risk.

What works in practice is assigning check tiers:

- Tier 1 (always blocking): keys, timestamp parseability, core measure validity
- Tier 2 (warning first, then promote): soft null thresholds, optional enrichments
- Tier 3 (monitoring only): exploratory signals

This gives teams room to improve quality without freezing delivery.

One mistake I see a lot is setting every check to blocking on day one. It looks strict, but it often leads teams to disable checks under pressure. A tiered rollout is more durable.

If you want one strong habit from this chapter, use this:

- every time a quality failure surprises the team, decide whether a new check, a stricter threshold, or better ownership would have caught it earlier.

That feedback loop turns quality from gatekeeping into learning.

## Hands-On Exercise

1. Add one Pandera schema for your ingestion table.
2. Add one `NullCheck`, one `FreshnessCheck`, and one `CustomSQLCheck`.
3. Force a failure with bad test data.
4. Confirm run is blocked and diagnostics are visible.

## Common Issues

1. Schema fields and ingestion output diverge after source API changes.
2. Quality checks query wrong table namespace.
3. Teams define checks but ignore severity strategy.
4. Warnings accumulate and become hidden production debt.
5. Contract checks are run manually, not in normal orchestration flow.

Recovery patterns: [Troubleshooting](../../operations/troubleshooting.md)

## Summary

Quality is strongest when contracts and checks are first-class runtime behaviour, not post-hoc reporting.

## Next Steps

1. Continue to [Part 8](08-schema-evolution-and-data-contracts.md) for safe schema change workflows.
2. Add quality ownership to each domain table.

## See Also

- [Part 8: Schema Evolution and Data Contracts](08-schema-evolution-and-data-contracts.md)
- [Part 9: Observability: Metrics, Logs, and Lineage](09-observability-metrics-logs-lineage.md)
- [Quality Checks Catalog](../../reference/quality-checks-catalog.md)

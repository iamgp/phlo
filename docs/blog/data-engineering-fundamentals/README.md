# Data Engineering Fundamentals with Phlo

A standalone series for learning data engineering from first principles using the
Phlo ecosystem. It starts with fundamentals, then moves into ingestion, storage,
transformation, quality, observability, and extension design.

## Who This Series Is For

- New data engineers who want practical foundations
- Analytics engineers moving into platform ownership
- Backend engineers building reliable datasets
- Teams standardising on open lakehouse patterns

## What You Will Build

By the end, you will be able to:

- Design a clean ingestion-to-serving data flow
- Use `phlo.ingest.dlt` for repeatable loads
- Run SQL transformations with dbt in `workflows/transforms/dbt`
- Validate quality with Pandera and `phlo.quality.pandera`
- Track pipeline health with status, logs, metrics, and lineage
- Debug incidents using a repeatable response checklist
- Extend the platform with plugins and Observatory extensions

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Basic SQL and Python familiarity
- Optional but helpful: read [Phlo Architecture Reference](../../reference/architecture.md)

## Series Setup

Run this once before following any command snippets:

```bash
uv venv
source .venv/bin/activate
uv pip install "phlo[defaults]" phlo-otel phlo-clickstack phlo-lineage pytest
```

Then run the blog commands from your working project directory (for example `/path/to/your/project`).

## Posts

| # | Title | Focus | Time |
| --- | --- | --- | --- |
| 1 | [What Data Engineering Really Is](01-what-is-data-engineering.md) | Core concepts, layers, responsibilities | 18 min |
| 2 | [Build Your First Phlo Project](02-build-your-first-phlo-project.md) | Project setup, services, first run | 22 min |
| 3 | [Ingestion Foundations with DLT](03-ingestion-foundations-with-dlt.md) | `phlo.ingest.dlt`, merge strategies, partitions | 24 min |
| 4 | [Iceberg and Nessie for Reliable Tables](04-iceberg-and-nessie-for-reliable-tables.md) | Table format, branching, catalog tooling | 22 min |
| 5 | [Orchestration with Dagster Assets](05-orchestration-with-dagster-assets.md) | Materialization, backfills, scheduling mindset | 24 min |
| 6 | [Transformations with dbt](06-transformations-with-dbt.md) | Medallion models, tests, publish configs | 24 min |
| 7 | [Quality Checks with Pandera and Phlo Quality](07-quality-checks-with-pandera-and-phlo-pandera.md) | Contracts, check suites, failure semantics | 24 min |
| 8 | [Schema Evolution and Data Contracts](08-schema-evolution-and-data-contracts.md) | Safe changes, rollout flow, compatibility | 20 min |
| 9 | [Observability: Metrics, Logs, and Lineage](09-observability-metrics-logs-lineage.md) | Operational visibility and feedback loops | 22 min |
| 10 | [Incident Response and Debugging](10-incident-response-and-debugging.md) | Triage playbooks, root cause, recovery | 24 min |
| 11 | [Performance and Cost Optimisation](11-performance-and-cost-optimization.md) | Runtime tuning, partition design, spend control | 20 min |
| 12 | [Extending Phlo with Plugins and Observatory](12-extending-phlo-with-plugins-and-observatory.md) | Plugin architecture, custom UI extension | 22 min |

## Learning Paths

### Path A: New to Data Engineering

1. Start with [Post 1](01-what-is-data-engineering.md)
2. Complete [Post 2](02-build-your-first-phlo-project.md)
3. Continue through [Post 7](07-quality-checks-with-pandera-and-phlo-pandera.md)
4. Use [Post 10](10-incident-response-and-debugging.md) as your runbook baseline

### Path B: Already Shipping Pipelines

1. Skim [Post 1](01-what-is-data-engineering.md)
2. Jump to [Post 4](04-iceberg-and-nessie-for-reliable-tables.md)
3. Deep dive [Post 9](09-observability-metrics-logs-lineage.md)
4. Finish with [Post 12](12-extending-phlo-with-plugins-and-observatory.md)

## Suggested Pace

- One post per day for two weeks
- Run every command in your own sandbox project
- Keep your own notes for "what broke" and "how fixed"

## Common Issues

1. Services fail to boot because local ports are occupied.
2. `phlo materialize` fails because core containers are not running.
3. dbt discovery fails because project files are outside `workflows/transforms/dbt`.
4. Quality checks fail because schema fields do not match ingestion output.
5. Lineage appears empty because assets were never materialized.

Troubleshooting guide: [Operations Troubleshooting](../../operations/troubleshooting.md)

## Summary

This track is a clean-room series built from scratch for learning data engineering with Phlo as the working platform.

## Next Steps

1. Open [Post 1](01-what-is-data-engineering.md).
2. Create a sandbox repo and run the setup in [Post 2](02-build-your-first-phlo-project.md).
3. Keep this index open as your progression checklist.

## See Also

- [Phlo Blog Index](../README.md)
- [Developer Guide](../../guides/developer-guide.md)
- [Architecture Reference](../../reference/architecture.md)

# Developer Workflow

This page is the day-to-day developer loop for Phlo.

## The Loop

```mermaid
flowchart LR
    install["Install and sync env"] --> start["Start services"]
    start --> author["Author ingestion, quality, and transforms"]
    author --> run["Materialize or run dbt"]
    run --> inspect["Inspect tables, logs, and metadata"]
    inspect --> test["Run tests and checks"]
    test --> refine["Refine config, schemas, and contracts"]
    refine --> author
```

## Typical Flow

### 1. Install

```bash
uv pip install -e .
```

### 2. Start the runtime

```bash
phlo services init
phlo services start
```

### 3. Build workflows

- define ingestion with package-backed decorators such as `phlo.ingest.dlt` or `phlo_sling.phlo_sling_replication`
- define validation with `phlo.quality.pandera` or the lazy `phlo.quality` public API when `phlo-pandera` is installed
- define transforms with dbt
- keep schemas under `workflows/schemas/`

For the full command-by-command authoring loop with `phlo workflow check`, see
[Workflow Development](workflow-development.md#authoring-loop).

### 4. Run the pipeline

```bash
phlo materialize <asset_name>
phlo dbt run
phlo dbt test
```

### 5. Inspect results

- Trino for data shape and query validation
- Dagster for orchestration state
- Observatory for Phlo-facing UI flows
- OpenMetadata, Hasura, or PostgREST when those surfaces are part of your stack

### 6. Verify

```bash
uv run pytest
uv run ruff check .
uv run ty check
```

## When To Leave This Lane

- package responsibilities: [Packages](../packages/index.md)
- platform topology and surfaces: [Platform Topology](../reference/platform-topology.md)
- setup of optional external systems: [Setup](../setup/index.md)
- production operation: [Operations](../operations/index.md)

## Reviewing vendor image updates

Renovate opens review-required pull requests for digest-pinned vendor images in
package source YAML. These updates change the tag and digest together and are
never automerged. Each changed reference is compared with its exact base using
the same pinned Trivy database snapshot; CRITICAL and HIGH raw occurrence counts
must not increase and at least one must decrease. Review the comparison, then
confirm the service contract and generated Compose behavior. The scheduled
non-blocking vulnerability view and raw Trivy artifacts are described in
[Container image security operations](../operations/container-image-security.md).

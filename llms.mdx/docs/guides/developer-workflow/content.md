# Developer Workflow (/docs/guides/developer-workflow)



The Loop [#the-loop]

<Mermaid
  chart="flowchart LR
    install[&#x22;Install and sync env&#x22;] --> start[&#x22;Start services&#x22;]
    start --> author[&#x22;Author ingestion, quality, and transforms&#x22;]
    author --> run[&#x22;Materialize or run dbt&#x22;]
    run --> inspect[&#x22;Inspect tables, logs, and metadata&#x22;]
    inspect --> test[&#x22;Run tests and checks&#x22;]
    test --> refine[&#x22;Refine config, schemas, and contracts&#x22;]
    refine --> author"
/>

Typical Flow [#typical-flow]

1\. Install [#1-install]

```bash
uv pip install -e .
```

2\. Start the runtime [#2-start-the-runtime]

```bash
phlo services init
phlo services start
```

3\. Build workflows [#3-build-workflows]

* define ingestion with `phlo.ingestion`
* define validation with `phlo.quality`
* define transforms with dbt
* keep schemas under `workflows/schemas/`

4\. Run the pipeline [#4-run-the-pipeline]

```bash
phlo materialize <asset_name>
docker exec dagster-webserver dbt run
docker exec dagster-webserver dbt test
```

5\. Inspect results [#5-inspect-results]

* Trino for data shape and query validation
* Dagster for orchestration state
* Observatory for Phlo-facing UI flows
* OpenMetadata, Hasura, or PostgREST when those surfaces are part of your stack

6\. Verify [#6-verify]

```bash
uv run pytest
uv run ruff check .
uv run ty check
```

When To Leave This Lane [#when-to-leave-this-lane]

* package responsibilities: [Packages](../packages/index.md)
* platform topology and surfaces: [Platform Topology](../reference/platform-topology.md)
* setup of optional external systems: [Setup](../setup/index.md)
* production operation: [Operations](../operations/index.md)

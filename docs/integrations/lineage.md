# Lineage Tooling Options

The current stack (Dagster + dbt + Airbyte + Marquez) already emits OpenLineage
events, but Marquez’s UI is intentionally lightweight. If you want a richer
lineage/catalog experience, here are the two main open-source platforms worth
considering and how they fit with the existing setup.

## Option 1: DataHub

**Why choose it**
- Full-featured data catalog with search, lineage graph, ownership, and governance features.
- Mature OpenLineage ingestion: a single source connector can ingest all events from Marquez.
- Native plugins for dbt, Airbyte, and Dagster (assets appear with metadata, tests, owners).
- Extensible UI (tags, glossary, column lineage visualizer) without much custom code.

**How it fits**
- Keep emitting OpenLineage events (as we already do). Deploy DataHub and configure the
  OpenLineage source to consume Marquez events.
- Optionally run DataHub’s dbt and Dagster ingest jobs for supplementary metadata (docs, tests, tags).
- Result: DataHub’s UI displays table lineage, column lineage, owners, glossary terms, and dashboards.

**Operational notes**
- DataHub deployment requires Kafka + Elastic (or their “Quickstart” containers for dev).
- Use Helm chart or Docker Compose for production deploys.

## Option 2: OpenMetadata

**Why choose it**
- All-in-one data catalog with lineage, governance, dashboards, and ML model registry.
- Native connectors for dbt (reads `manifest.json`/`catalog.json`), Airbyte, and
  Dagster (via ingest pipeline). It can ingest metadata directly without Marquez in the middle.
- Lineage graph includes column-level info, query logs, and usage analytics.
- Ships with workflows for data quality and governance tasks.

**How it fits**
- Replace Marquez with OpenMetadata’s ingestion pipelines:
  * dbt ingestion job loads models, columns, lineage.
  * Airbyte ingestion job loads connections, destinations.
  * Dagster connector links Dagster jobs/assets to datasets.
- Or, enable OpenLineage ingestion (OpenMetadata can read Marquez events too) if you prefer to keep the OL pipeline.

**Operational notes**
- OpenMetadata stack includes MySQL/Postgres, Elastic, Airflow, and the ingestion workflows.
- Docker Compose is available for dev; production typically uses Helm on Kubernetes.

## When to stick with Dagster + dbt docs

If the goal is simply to see how Dagster assets relate (staging → marts, Airbyte → raw), Dagit’s asset graph plus dbt docs already provide that insight without an additional platform. Marquez/OpenLineage is helpful when you want a neutral protocol that other tools (Airflow, Spark jobs, BI tools) can also emit, but Dagster alone can still meet small-team needs.

## Recommendation
- **Need a comprehensive catalog/governance platform?** DataHub is battle-tested in production; OpenMetadata offers similar breadth with a slightly lighter stack. Both integrate cleanly with the current pipeline; evaluate which governance features/UI resonate with the team.
- **Want to keep it simple?** Drop Marquez, rely on Dagster’s asset graph + dbt docs for lineage, and revisit DataHub/OpenMetadata when cross-platform lineage becomes a requirement.

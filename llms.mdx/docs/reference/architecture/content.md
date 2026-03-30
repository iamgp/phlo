# Architecture Overview (/docs/reference/architecture)



Phlo is built on modern lakehouse principles using Apache Iceberg as the table format and Project Nessie as a Git-like catalog. This architecture provides ACID transactions, schema evolution, time travel, and branch isolation for data engineering workflows.

Design Principles [#design-principles]

1\. Open Standards [#1-open-standards]

* Apache Iceberg for table format (open spec, multi-engine support)
* S3-compatible storage (portable across cloud providers)
* Standard SQL via Trino
* Open-source components throughout

2\. Stateless Services [#2-stateless-services]

* All state stored in volumes (MinIO, PostgreSQL)
* Services can be restarted without data loss
* Configuration via environment variables
* 12-factor app compliance

3\. Git-Like Workflows [#3-git-like-workflows]

* Branch isolation (dev/staging/prod)
* Atomic multi-table commits
* Time travel to any point in history
* Tag releases for reproducibility

4\. Asset-Based Orchestration [#4-asset-based-orchestration]

* Declarative data assets in Dagster
* Automatic lineage tracking
* Partition-aware dependencies
* Freshness policies for monitoring

System Architecture [#system-architecture]

High-Level Component Diagram [#high-level-component-diagram]

<Mermaid
  chart="graph TB
    subgraph ui[&#x22;User Interface&#x22;]
        OBS[Observatory UI]
        DAGUI[Dagster Web UI]
        SUPERSET[Superset Dashboards]
    end

    subgraph control[&#x22;Control Plane&#x22;]
        PAPI[phlo-api]
        HASURA[Hasura GraphQL]
        POSTGREST[PostgREST]
        SCHEDULES[Schedules & Sensors]
        DAGSTER[Dagster Assets]
    end

    subgraph ingest[&#x22;Ingestion&#x22;]
        NS[Nightscout API]
        FILES[CSV and Excel Files]
        EXTERNAL[External APIs]
        DLT[DLT Python]
        STAGE[S3 Staging Area]
        PYI[PyIceberg Writer]
    end

    subgraph storage[&#x22;Storage and Catalog&#x22;]
        MINIO[MinIO S3 Storage]
        NESSIE[Nessie Catalog]
        PG[PostgreSQL]
    end

    subgraph compute[&#x22;Compute&#x22;]
        TRINO[Trino Query Engine]
        DBT[dbt Transformations]
        DUCK[DuckDB Ad-hoc]
        MARTS[PostgreSQL Marts]
    end

    subgraph observability[&#x22;Observability&#x22;]
        OTEL[phlo-otel]
        CLICKSTACK[ClickStack]
    end

    NS --> DLT
    FILES --> DLT
    EXTERNAL --> DLT
    DLT --> STAGE --> PYI
    PYI --> MINIO
    PYI --> NESSIE

    MINIO --> TRINO
    NESSIE --> TRINO
    MINIO --> DUCK
    TRINO --> DBT --> MARTS
    TRINO --> MARTS

    SCHEDULES --> DAGSTER
    DAGSTER --> DLT
    DAGSTER --> DBT
    DAGSTER --> TRINO

    OBS --> PAPI
    DAGUI --> DAGSTER
    PAPI --> TRINO
    PAPI --> NESSIE
    PAPI --> DAGSTER
    PG --> PAPI
    PG --> HASURA
    PG --> POSTGREST
    MARTS --> SUPERSET

    DAGSTER --> OTEL --> CLICKSTACK"
/>

The high-level diagram keeps the main layers readable. The detailed views below preserve the
cross-system connections that would otherwise turn the overview into a wire bundle.

Interface and API Detail [#interface-and-api-detail]

<Mermaid
  chart="flowchart LR
    subgraph ui[&#x22;User Interface&#x22;]
        OBS[Observatory UI]
        DAGUI[Dagster Web UI]
        SUPERSET[Superset Dashboards]
    end

    subgraph api[&#x22;API Layer&#x22;]
        PAPI[phlo-api]
        HASURA[Hasura GraphQL]
        POSTGREST[PostgREST]
    end

    subgraph services[&#x22;Platform Services&#x22;]
        TRINO[Trino Query Engine]
        NESSIE[Nessie Catalog]
        MINIO[MinIO S3 Storage]
        DAGSTER[Dagster Assets]
        PG[PostgreSQL]
        MARTS[PostgreSQL Marts]
    end

    OBS --> PAPI
    DAGUI --> DAGSTER

    PAPI --> TRINO
    PAPI --> NESSIE
    PAPI --> MINIO
    PAPI --> DAGSTER

    PG --> PAPI
    PG --> HASURA
    PG --> POSTGREST
    PG --> NESSIE
    PG --> DAGSTER
    PG --> SUPERSET

    TRINO --> SUPERSET
    MARTS --> SUPERSET"
/>

Data and Orchestration Detail [#data-and-orchestration-detail]

<Mermaid
  chart="flowchart LR
    subgraph sources[&#x22;Data Sources&#x22;]
        NS[Nightscout API]
        FILES[CSV and Excel Files]
        EXTERNAL[External APIs]
    end

    subgraph ingest[&#x22;Ingestion&#x22;]
        DLT[DLT Python]
        STAGE[S3 Staging Area]
        PYI[PyIceberg Writer]
    end

    subgraph platform[&#x22;Platform Runtime&#x22;]
        SCHEDULES[Schedules and Sensors]
        DAGSTER[Dagster Assets]
        MINIO[MinIO S3 Storage]
        NESSIE[Nessie Catalog]
        TRINO[Trino Query Engine]
        DBT[dbt Transformations]
        DUCK[DuckDB Ad-hoc]
        MARTS[PostgreSQL Marts]
        OTEL[phlo-otel]
        CLICKSTACK[ClickStack]
    end

    NS --> DLT
    FILES --> DLT
    EXTERNAL --> DLT
    DLT --> STAGE --> PYI
    PYI --> MINIO
    PYI --> NESSIE

    SCHEDULES --> DAGSTER
    DAGSTER --> DLT
    DAGSTER --> DBT
    DAGSTER --> TRINO
    DAGSTER --> OTEL --> CLICKSTACK

    MINIO --> TRINO
    NESSIE --> TRINO
    MINIO --> DUCK
    TRINO --> DBT
    DBT --> MARTS
    TRINO --> MARTS"
/>

Key Components [#key-components]

User Interface Layer [#user-interface-layer]

* **Observatory**: Web-based UI for exploring data, viewing lineage, managing branches, and monitoring data quality. Provides a unified interface for all Phlo operations.
* **Dagster Web UI**: Native Dagster interface for asset materialization, run monitoring, and workflow debugging.

API Layer [#api-layer]

* **phlo-api**: Python FastAPI service exposing Phlo internals (plugins, services, configs) and providing data access endpoints for Observatory.
* **PostgREST** (optional): Auto-generated REST API from PostgreSQL schemas.
* **Hasura** (optional): GraphQL API with real-time subscriptions.

Storage Layer [#storage-layer]

* **MinIO**: S3-compatible object storage for data files and Iceberg metadata
* **Nessie**: Git-like catalog for table metadata and branching
* **PostgreSQL**: Relational database for operational metadata and analytics marts

Compute Layer [#compute-layer]

* **Trino**: Distributed SQL query engine for analytics
* **dbt**: Data transformation framework with SQL
* **DuckDB**: Embedded analytical database for ad-hoc queries

Orchestration [#orchestration]

* **Dagster**: Asset-based data orchestration platform
* **Schedules & Sensors**: Automated pipeline triggers

Analytics Layer [#analytics-layer]

* **PostgreSQL Marts**: Curated datasets for BI tools
* **Superset** (optional): Business intelligence and visualization

Data Flow [#data-flow]

1. **Ingestion**: Data sources → DLT → S3 staging → PyIceberg → Iceberg tables
2. **Transformation**: Iceberg tables → dbt → PostgreSQL marts
3. **Querying**: Multiple engines can query Iceberg tables directly
4. **Visualization**: BI tools connect to PostgreSQL marts or query engines

Plugin System Architecture [#plugin-system-architecture]

Phlo uses a unified plugin system for extending functionality:

Plugin Types [#plugin-types]

1. **Service Plugins**: Infrastructure services (Dagster, Postgres, Trino, etc.)
   * Distributed as Python packages (e.g., `phlo-dagster`, `phlo-trino`)
   * Contain Docker service definitions via `service.yaml`
   * Auto-discovered via `phlo.plugins.services` entry points

2. **Data Plugins**: Data processing extensions
   * **Source Connectors**: Fetch data from external systems
   * **Quality Checks**: Custom validation rules
   * **Transformations**: Reusable transformation logic

3. **Dagster Extension Plugins**: Extend Dagster functionality
   * Custom resources, sensors, schedules
   * Integration with external systems

4. **CLI Plugins**: Add custom CLI commands

Plugin Discovery [#plugin-discovery]

Plugins are automatically discovered using Python entry points:

<Mermaid
  chart="flowchart TB
    env[&#x22;Python Environment<br/>phlo<br/>phlo-dagster<br/>phlo-custom-source&#x22;]
    discovery[&#x22;Entry Point Discovery<br/>importlib.metadata&#x22;]
    registry[&#x22;Plugin Registry<br/>Installed plugins<br/>Available plugins (remote)&#x22;]

    env --> discovery --> registry"
/>

Plugin Registry [#plugin-registry]

* **registry/plugins.json**: Authoritative catalog of available plugins
* **Remote + Bundled**: Fetches from remote, falls back to bundled version offline
* **CLI Management**: `phlo plugin search/install/list` commands

For more details, see:

* [Data Engineering Fundamentals Part 12](../blog/data-engineering-fundamentals/12-extending-phlo-with-plugins-and-observatory.md)
* [ADR 0030: Unified Plugin System](../architecture/decisions/0030-unified-plugin-system-with-registry.md)
* [ADR 0046: Phlo Contracts for Migration Scaffolding](../architecture/decisions/0046-phlo-contracts-for-schema-migration-scaffolding.md)

Branching Strategy [#branching-strategy]

Phlo uses a Git-like branching model for data:

* **main**: Production data (read-only for most users)
* **dev**: Development workspace (read-write)
* **feature branches**: Isolated development environments

See the [Core Concepts guide](../getting-started/core-concepts.md) for branching patterns.

For More Details [#for-more-details]

See the [Plugin API](plugin-api.md) and [Extension Model](../guides/extension-model.md) for the public plugin system documentation.

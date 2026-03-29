# Public System Design

This page explains the public architecture of Phlo as a platform.

## System View

```mermaid
flowchart TB
    subgraph authoring["Authoring layer"]
        dev["Developer workflows"]
        cli["CLI"]
        observatory["Observatory"]
    end

    subgraph runtime["Runtime layer"]
        hooks["Hooks and plugins"]
        orchestration["Orchestrator adapter"]
        quality["Quality providers"]
        ingest["Ingestion providers"]
        transforms["Transformation providers"]
    end

    subgraph data["Data plane"]
        storage["Object storage"]
        format["Table format"]
        catalog["Catalog"]
        query["Query engine"]
        metadata["Metadata store"]
    end

    subgraph surfaces["Optional external surfaces"]
        phloapi["phlo-api"]
        hasura["Hasura"]
        postgrest["PostgREST"]
        openmetadata["OpenMetadata"]
    end

    subgraph observe["Observability"]
        otel["phlo-otel"]
        backend["Collectors and backends"]
    end

    authoring --> runtime
    runtime --> data
    runtime --> surfaces
    runtime --> observe
```

## Design Principles

- one platform, many optional surfaces
- stable higher-level concepts over direct vendor coupling
- package-level modularity with capability-based composition
- explicit data lifecycle from ingest to serving
- observability and governance as cross-cutting concerns, not add-ons bolted on later

## Main Boundaries

- authoring and workflow definition
- runtime composition and execution
- data storage, catalog, and query
- optional serving and metadata surfaces
- monitoring, tracing, and operational visibility

## Related Pages

- [Choosing Components](../guides/choosing-components.md)
- [Platform Topology](../reference/platform-topology.md)
- [Architecture Overview](../reference/architecture.md)

# Public System Design (/docs/architecture/public-system-design)



System View [#system-view]

<Mermaid
  chart="flowchart TB
    subgraph authoring[&#x22;Authoring layer&#x22;]
        dev[&#x22;Developer workflows&#x22;]
        cli[&#x22;CLI&#x22;]
        observatory[&#x22;Observatory&#x22;]
    end

    subgraph runtime[&#x22;Runtime layer&#x22;]
        hooks[&#x22;Hooks and plugins&#x22;]
        orchestration[&#x22;Orchestrator adapter&#x22;]
        quality[&#x22;Quality providers&#x22;]
        ingest[&#x22;Ingestion providers&#x22;]
        transforms[&#x22;Transformation providers&#x22;]
    end

    subgraph data[&#x22;Data plane&#x22;]
        storage[&#x22;Object storage&#x22;]
        format[&#x22;Table format&#x22;]
        catalog[&#x22;Catalog&#x22;]
        query[&#x22;Query engine&#x22;]
        metadata[&#x22;Metadata store&#x22;]
    end

    subgraph surfaces[&#x22;Optional external surfaces&#x22;]
        phloapi[&#x22;phlo-api&#x22;]
        hasura[&#x22;Hasura&#x22;]
        postgrest[&#x22;PostgREST&#x22;]
        openmetadata[&#x22;OpenMetadata&#x22;]
    end

    subgraph observe[&#x22;Observability&#x22;]
        otel[&#x22;phlo-otel&#x22;]
        backend[&#x22;Collectors and backends&#x22;]
    end

    authoring --> runtime
    runtime --> data
    runtime --> surfaces
    runtime --> observe"
/>

Design Principles [#design-principles]

* one platform, many optional surfaces
* stable higher-level concepts over direct vendor coupling
* package-level modularity with capability-based composition
* explicit data lifecycle from ingest to serving
* observability and governance as cross-cutting concerns, not add-ons bolted on later

Main Boundaries [#main-boundaries]

* authoring and workflow definition
* runtime composition and execution
* data storage, catalog, and query
* optional serving and metadata surfaces
* monitoring, tracing, and operational visibility

Related Pages [#related-pages]

* [Choosing Components](../guides/choosing-components.md)
* [Platform Topology](../reference/platform-topology.md)
* [Architecture Overview](../reference/architecture.md)

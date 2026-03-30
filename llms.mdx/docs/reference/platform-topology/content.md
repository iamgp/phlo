# Platform Topology (/docs/reference/platform-topology)



Topology [#topology]

<Mermaid
  chart="flowchart TB
    subgraph dev[&#x22;Developer-facing layer&#x22;]
        observatory[&#x22;Observatory&#x22;]
        dagsterui[&#x22;Dagster UI&#x22;]
        superset[&#x22;Superset&#x22;]
    end

    subgraph services[&#x22;External and operator-facing surfaces&#x22;]
        phloapi[&#x22;phlo-api&#x22;]
        hasura[&#x22;Hasura&#x22;]
        postgrest[&#x22;PostgREST&#x22;]
        openmetadata[&#x22;OpenMetadata&#x22;]
    end

    subgraph runtime[&#x22;Core runtime&#x22;]
        cli[&#x22;CLI + config&#x22;]
        hooks[&#x22;Hooks + plugins&#x22;]
        workflows[&#x22;Ingestion / quality / transforms&#x22;]
    end

    subgraph data[&#x22;Lakehouse data plane&#x22;]
        dagster[&#x22;Dagster&#x22;]
        dlt[&#x22;DLT&#x22;]
        dbt[&#x22;dbt&#x22;]
        trino[&#x22;Trino&#x22;]
        nessie[&#x22;Nessie&#x22;]
        format[&#x22;Iceberg / Delta&#x22;]
        storage[&#x22;MinIO / RustFS&#x22;]
        postgres[&#x22;Postgres&#x22;]
    end

    subgraph obs[&#x22;Observability&#x22;]
        otel[&#x22;phlo-otel&#x22;]
        alloy[&#x22;Alloy&#x22;]
        backend[&#x22;ClickStack or Prometheus/Loki/Grafana&#x22;]
    end

    dev --> services
    services --> runtime
    runtime --> data
    runtime --> obs
    obs --> backend"
/>

Reading This Topology [#reading-this-topology]

* core runtime: mandatory logic and workflow abstractions
* data plane: storage, catalogs, orchestration, transforms, and query
* external surfaces: optional serving, API, and metadata entry points
* observability: separate but cross-cutting layer

Related Pages [#related-pages]

* [Choosing Components](../guides/choosing-components.md)
* [Deployment Profiles](../guides/deployment-profiles.md)
* [API Surfaces](api-surfaces.md)

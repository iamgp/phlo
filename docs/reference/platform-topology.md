# Platform Topology

This page shows the major Phlo layers and where optional systems fit.

## Topology

```mermaid
flowchart TB
    subgraph dev["Developer-facing layer"]
        observatory["Observatory"]
        dagsterui["Dagster UI"]
        superset["Superset"]
    end

    subgraph services["External and operator-facing surfaces"]
        phloapi["phlo-api"]
        hasura["Hasura"]
        postgrest["PostgREST"]
        openmetadata["OpenMetadata"]
    end

    subgraph runtime["Core runtime"]
        cli["CLI + config"]
        hooks["Hooks + plugins"]
        workflows["Ingestion / quality / transforms"]
    end

    subgraph data["Lakehouse data plane"]
        dagster["Dagster"]
        dlt["DLT"]
        dbt["dbt"]
        trino["Trino"]
        nessie["Nessie"]
        format["Iceberg / Delta"]
        storage["MinIO / RustFS"]
        postgres["Postgres"]
    end

    subgraph obs["Observability"]
        otel["phlo-otel"]
        alloy["Alloy"]
        backend["ClickStack or Prometheus/Loki/Grafana"]
    end

    dev --> services
    services --> runtime
    runtime --> data
    runtime --> obs
    obs --> backend
```

## Reading This Topology

- core runtime: mandatory logic and workflow abstractions
- data plane: storage, catalogs, orchestration, transforms, and query
- external surfaces: optional serving, API, and metadata entry points
- observability: separate but cross-cutting layer

## Related Pages

- [Choosing Components](../guides/choosing-components.md)
- [Deployment Profiles](../guides/deployment-profiles.md)
- [API Surfaces](api-surfaces.md)

# Deployment Profiles (/docs/guides/deployment-profiles)



Profile Layers [#profile-layers]

<Mermaid
  chart="flowchart TB
    core[&#x22;Core lakehouse runtime&#x22;] --> developer[&#x22;Developer stack&#x22;]
    core --> operator[&#x22;Operator-facing surfaces&#x22;]
    core --> observe[&#x22;Observability&#x22;]
    operator --> apis[&#x22;Hasura / PostgREST / phlo-api&#x22;]
    operator --> catalog[&#x22;OpenMetadata&#x22;]"
/>

Suggested Profiles [#suggested-profiles]

Core developer profile [#core-developer-profile]

* orchestration: `phlo-dagster`
* metadata/state: `phlo-postgres`
* storage: `phlo-minio`
* catalog: `phlo-nessie`
* query: `phlo-trino`
* table format: `phlo-iceberg`
* workflow packages: `phlo-dlt`, `phlo-dbt`, `phlo-pandera`

External-surface profile [#external-surface-profile]

Add when other teams need direct access:

* `phlo-api`
* `phlo-postgrest`
* `phlo-hasura`
* `phlo-openmetadata`

Observability profile [#observability-profile]

* emission: `phlo-otel`
* collector/router: `phlo-alloy`
* backend: `phlo-clickstack` or `phlo-prometheus` + `phlo-loki` + `phlo-grafana`

Selection Guidance [#selection-guidance]

* local development: start with the core developer profile
* platform demos and self-service access: add external surfaces
* production diagnostics: add observability before adding more user-facing surfaces

Related Pages [#related-pages]

* [Choosing Components](choosing-components.md)
* [Integration Profiles](integration-profiles.md)
* [Production Readiness](../operations/production-readiness.md)

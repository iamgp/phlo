# Choosing Components (/docs/guides/choosing-components)



Decision Map [#decision-map]

<Mermaid
  chart="flowchart TD
    start[&#x22;Start with Phlo core&#x22;] --> format[&#x22;Table format&#x22;]
    format --> iceberg[&#x22;Iceberg&#x22;]
    format --> delta[&#x22;Delta&#x22;]
    start --> api[&#x22;External API surface&#x22;]
    api --> phloapi[&#x22;phlo-api&#x22;]
    api --> postgrest[&#x22;PostgREST&#x22;]
    api --> hasura[&#x22;Hasura&#x22;]
    start --> observe[&#x22;Observability&#x22;]
    observe --> clickstack[&#x22;ClickStack&#x22;]
    observe --> grafana[&#x22;Prometheus + Loki + Grafana&#x22;]
    start --> storage[&#x22;Object storage&#x22;]
    storage --> minio[&#x22;MinIO&#x22;]
    storage --> rustfs[&#x22;RustFS&#x22;]"
/>

Core Choices [#core-choices]

API surfaces [#api-surfaces]

* `phlo-api`: use for Phlo-native behavior, capability-backed endpoints, and Observatory backend needs.
* `PostgREST`: use when you want a database-native REST surface with minimal custom application code.
* `Hasura`: use when you want GraphQL, metadata-driven schema exposure, and subscriptions.

Table formats [#table-formats]

* `Iceberg`: default Phlo path. Best fit with Nessie, Trino, and the current Write-Audit-Publish story.
* `Delta`: use when your wider ecosystem already standardizes on Delta Lake or Delta-compatible tooling.

Object storage [#object-storage]

* `MinIO`: default local and general-purpose S3-compatible storage.
* `RustFS`: consider when you want a higher-performance S3-compatible alternative and accept a less common path.

Observability [#observability]

* `ClickStack`: preferred all-in-one backend. Best default when you want the fewest moving parts.
* `Prometheus + Loki + Grafana`: use when you want a more traditional split stack or need deeper compatibility with existing operator tooling.

Packaging Guidance [#packaging-guidance]

Recommended baseline [#recommended-baseline]

* `phlo`
* `phlo-dagster`
* `phlo-postgres`
* `phlo-trino`
* `phlo-minio`
* `phlo-nessie`
* `phlo-iceberg`
* `phlo-dlt`
* `phlo-dbt`
* `phlo-pandera`

Add by concern [#add-by-concern]

* external REST/GraphQL access: `phlo-api`, `phlo-postgrest`, `phlo-hasura`
* metadata/catalog: `phlo-openmetadata`
* observability: `phlo-otel`, `phlo-clickstack` or the split observability packages
* extension development: `phlo-testing`, `phlo-core-plugins`

Related Pages [#related-pages]

* [Integration Profiles](integration-profiles.md)
* [Service Packages](service-packages.md)
* [Setup](../setup/index.md)
* [Packages](../packages/index.md)

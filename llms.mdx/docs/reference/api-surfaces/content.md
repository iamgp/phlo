# API Surfaces (/docs/reference/api-surfaces)



Surface Map [#surface-map]

<Mermaid
  chart="flowchart LR
    phlo[&#x22;Phlo runtime and data plane&#x22;] --> phloapi[&#x22;phlo-api&#x22;]
    phlo --> postgrest[&#x22;PostgREST&#x22;]
    phlo --> hasura[&#x22;Hasura&#x22;]
    phlo --> openmetadata[&#x22;OpenMetadata API and UI&#x22;]"
/>

Surface Roles [#surface-roles]

`phlo-api` [#phlo-api]

* Phlo-native service
* capability-aware
* best fit for Observatory and Phlo-specific operational endpoints

`PostgREST` [#postgrest]

* database-native REST
* best fit for exposing relational read/write surfaces with minimal app code

`Hasura` [#hasura]

* metadata-driven GraphQL
* best fit for GraphQL clients, subscriptions, and schema-driven exposure

`OpenMetadata` [#openmetadata]

* metadata and governance surface
* not a serving API for marts, but a catalog and discovery surface for data users

Selection Guidance [#selection-guidance]

* Phlo-native control-plane behavior: start with `phlo-api`
* self-service relational REST: add `PostgREST`
* GraphQL and subscriptions: add `Hasura`
* discovery, lineage, and governance: add `OpenMetadata`

Related Pages [#related-pages]

* [Choosing Components](../guides/choosing-components.md)
* [Hasura Setup](../setup/hasura.md)
* [PostgREST Setup](../setup/postgrest.md)
* [OpenMetadata Setup](../setup/openmetadata.md)
* [phlo-api](phlo-api.md)

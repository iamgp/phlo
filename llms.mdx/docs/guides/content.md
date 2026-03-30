# Guides (/docs/guides)



Developer Story [#developer-story]

<Mermaid
  chart="flowchart TD
    model[&#x22;Model the data and contracts&#x22;]
    ingest[&#x22;Ingest and validate&#x22;]
    transform[&#x22;Transform and publish&#x22;]
    package[&#x22;Compose runtime services&#x22;]
    extend[&#x22;Extend with plugins and hooks&#x22;]
    operate[&#x22;Test and run in real environments&#x22;]

    model --> ingest --> transform
    transform --> package
    package --> extend
    extend --> operate"
/>

Recommended Reading Order [#recommended-reading-order]

1. [Developer Guide](developer-guide.md)
2. [Workflow Development](workflow-development.md)
3. [Data Modeling](data-modeling.md)
4. [Service Packages](service-packages.md)
5. [Integration Profiles](integration-profiles.md)
6. [Testing Strategy](testing-strategy.md)

Guide Categories [#guide-categories]

* Workflow authoring: [Developer Guide](developer-guide.md), [Workflow Development](workflow-development.md), [dbt Development](dbt-development.md)
* Platform composition: [Service Packages](service-packages.md), [Compose Generation](compose-generation.md), [Integration Profiles](integration-profiles.md)
* Extension points: [Plugin Development](plugin-development.md), [Capability Primitives](capability-primitives.md), [Hook Event Bus](hook-event-bus.md)
* Operations-aware design: [Testing Strategy](testing-strategy.md), [Logging](logging.md), [Operations Contracts](operations-contracts.md)

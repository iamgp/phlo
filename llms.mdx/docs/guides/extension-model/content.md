# Extension Model (/docs/guides/extension-model)



Extension Map [#extension-map]

<Mermaid
  chart="flowchart TD
    need[&#x22;Need to extend Phlo&#x22;] --> workflow[&#x22;Workflow behavior&#x22;]
    need --> runtime[&#x22;Runtime service or surface&#x22;]
    need --> platform[&#x22;Cross-cutting platform behavior&#x22;]

    workflow --> plugin[&#x22;Plugin type&#x22;]
    runtime --> service[&#x22;Service package&#x22;]
    platform --> hook[&#x22;Hook provider&#x22;]
    platform --> capability[&#x22;Capability implementation&#x22;]"
/>

Use The Right Mechanism [#use-the-right-mechanism]

* plugin type: when you are adding sources, quality checks, transformations, catalogs, asset providers, or CLI extensions
* service package: when you are shipping a runtime component with compose/config behavior
* hook provider: when you need event-driven reactions across the pipeline lifecycle
* capability implementation: when you are filling an abstract platform contract behind a stable interface

Where To Go Next [#where-to-go-next]

* [Plugin Development](plugin-development.md)
* [Plugin API](../reference/plugin-api.md)
* [Capability Primitives](capability-primitives.md)
* [Hook Event Bus](hook-event-bus.md)
* [Packages](../packages/index.md)

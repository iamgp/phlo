# Data Lifecycle (/docs/guides/data-lifecycle)



Lifecycle [#lifecycle]

<Mermaid
  chart="flowchart LR
    raw[&#x22;Raw intake&#x22;] --> bronze[&#x22;Bronze: landed and normalized&#x22;]
    bronze --> quality[&#x22;Quality checks&#x22;]
    quality --> silver[&#x22;Silver: refined domain tables&#x22;]
    silver --> gold[&#x22;Gold: curated business-ready models&#x22;]
    gold --> marts[&#x22;Marts and serving surfaces&#x22;]"
/>

How Phlo Maps To It [#how-phlo-maps-to-it]

* ingestion packages move source data into raw and bronze layers
* quality packages enforce contracts before promotion
* dbt transforms move data through silver, gold, and marts
* catalogs and metadata surfaces expose the resulting assets to humans and tools

Why This Matters [#why-this-matters]

* reproducibility: rebuild downstream from upstream layers
* debugability: isolate issues by stage
* governance: make promotion and quality gates explicit
* serving flexibility: expose marts through APIs and BI tools without conflating them with ingestion

Related Pages [#related-pages]

* [Core Concepts](../getting-started/core-concepts.md)
* [Data Modeling](data-modeling.md)
* [Operations Contracts](operations-contracts.md)

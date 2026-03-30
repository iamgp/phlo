# Reference (/docs/reference)



What Lives Here [#what-lives-here]

Reference pages answer stable questions:

* which command or flag does this?
* which setting wins when multiple sources define it?
* what is the supported plugin or capability contract?
* what is the architecture and where does a component sit?
* which API surface is considered part of the platform?

Reference Map [#reference-map]

<Mermaid
  chart="flowchart TD
    reference[&#x22;Reference&#x22;]
    reference --> commands[&#x22;CLI and operations surface&#x22;]
    reference --> config[&#x22;Configuration and precedence&#x22;]
    reference --> contracts[&#x22;Plugin and capability contracts&#x22;]
    reference --> architecture[&#x22;Architecture and system shape&#x22;]
    reference --> apis[&#x22;Platform API surfaces&#x22;]
    reference --> errors[&#x22;Errors and diagnostics&#x22;]"
/>

Current Reference Pages [#current-reference-pages]

* [CLI Reference](cli-reference.md): commands, flags, and examples.
* [Configuration Reference](configuration-reference.md): env vars, defaults, and precedence.
* [Architecture](architecture.md): system model and component boundaries.
* [Plugin API](plugin-api.md): extension contracts and base types.
* [phlo-api](phlo-api.md): Phlo's Python API service surface.
* [Quality Checks Catalog](quality-checks-catalog.md): built-in quality checks.
* [DuckDB Queries](duckdb-queries.md): local query reference.
* [Common Errors](common-errors.md): frequent failures and fixes.

Related Sections [#related-sections]

* Use [Guides](../guides/developer-guide.md) for how-to workflows.
* Use [Packages](../packages/index.md) for installable package responsibilities.
* Use [Setup](../setup/index.md) for external surfaces and environment-specific wiring.

Code And Docblock Reference [#code-and-docblock-reference]

The generated [Python Reference](../python-reference/index.mdx) covers symbols, signatures, and docstrings for the core runtime and workspace packages. It complements the hand-written reference pages:

* generated pages: symbols, signatures, docstrings, and source-level detail
* hand-written pages: platform behavior, contracts, commands, and architecture

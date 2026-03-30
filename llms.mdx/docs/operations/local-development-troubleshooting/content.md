# Local Development Troubleshooting (/docs/operations/local-development-troubleshooting)



By Symptom [#by-symptom]

Services will not start [#services-will-not-start]

* inspect `phlo services status`
* inspect container logs
* verify `.phlo/.env.local`
* verify port collisions

Dagster starts but assets fail [#dagster-starts-but-assets-fail]

* check ingestion source credentials
* check Pandera schema mismatches
* check dbt model/test failures
* inspect hook and telemetry output

Query layer is empty or wrong [#query-layer-is-empty-or-wrong]

* verify ingestion completed
* verify publish/promotion step
* inspect Trino, catalog, and table format configuration

APIs or UIs are unavailable [#apis-or-uis-are-unavailable]

* verify the relevant optional surface is actually enabled
* confirm internal versus host ports
* confirm startup order and health checks

Docs example commands do not work locally [#docs-example-commands-do-not-work-locally]

* verify package/profile assumptions
* verify the active orchestrator and service topology
* verify whether the command expects host execution or container execution

Related Pages [#related-pages]

* [Troubleshooting](troubleshooting.md)
* [Developer Workflow](../guides/developer-workflow.md)
* [Choosing Components](../guides/choosing-components.md)

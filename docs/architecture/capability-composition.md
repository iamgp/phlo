# Capability-Driven Composition

Phlo can run as a minimal core plus installed capability providers. This allows swapping components without changing core runtime code.

## Capability Model

Phlo capability registry now supports:

- `table_store`: writes and table lifecycle (examples: Iceberg, Delta)
- `catalog`: table/catalog metadata namespace operations
- `query_engine`: SQL execution provider
- `quality_backend`: quality-check execution backend
- `metadata_catalog`: governance/metadata sync target
- `lineage_sink`: lineage event destination

Capability providers register at startup through plugin discovery.

## Runtime Resolution

At runtime, components resolve providers by capability type and optional provider name:

- explicit resolution: `query_engine:trino`
- implicit resolution: capability with one installed provider
- unresolved or ambiguous: deterministic failure with guidance

This is implemented in `phlo.capabilities.resolver`.

## Plugin Requirements

Plugins can declare:

- `requires_capabilities`: hard requirements
- `optional_capabilities`: optional integrations

During plugin inspection and install flows, Phlo surfaces unmet capability requirements so users know what to install next.

## Example Stack Profiles

### Minimal stack

- core `phlo`
- one orchestrator adapter
- one query engine provider (optional depending on workflow)

### Lakehouse stack

- `table_store` provider
- `catalog` provider
- `query_engine` provider
- optional `metadata_catalog` and `lineage_sink`

## Migration Rule

New package integrations should depend on capability interfaces and resolver lookups. Avoid direct imports of another package runtime unless that dependency is truly mandatory.

# Observatory

Observatory is the developer- and operator-facing UI layer for Phlo.

## Role

Observatory is not the whole platform. It is one UI surface sitting on top of `phlo-api` and the wider runtime.

Observatory is capability-driven. The UI should decide which pages and actions to show from `phlo-api` read models such as `/api/observatory/capability-inventory`, not from hardcoded package assumptions.

## In The Bigger Picture

```mermaid
flowchart LR
    user["Developer or operator"] --> observatory["Observatory"]
    observatory --> phloapi["phlo-api"]
    phloapi --> runtime["Phlo runtime and capabilities"]
    runtime --> data["Data plane and metadata systems"]
```

## Current Docs

- [Extensions](extensions.md): how to extend the UI surface
- [Observatory Contracts](../reference/observatory-contracts.md): provider-neutral surfaces, read models, and guarded actions

## Related Pages

- [API Surfaces](../reference/api-surfaces.md)
- [phlo-observatory package](../packages/phlo-observatory.md)
- [phlo-api](../reference/phlo-api.md)

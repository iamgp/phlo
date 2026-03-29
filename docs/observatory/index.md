# Observatory

Observatory is the developer-facing UI layer for Phlo.

## Role

Observatory is not the whole platform. It is one UI surface sitting on top of `phlo-api` and the wider runtime.

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

## Related Pages

- [API Surfaces](../reference/api-surfaces.md)
- [phlo-observatory package](../packages/phlo-observatory.md)
- [phlo-api](../reference/phlo-api.md)

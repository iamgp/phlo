# Part 12: Extending Phlo with Plugins and Observatory

> Prerequisite: Complete [Part 11](11-performance-and-cost-optimization.md).

## What You'll Learn

- How Phlo plugin discovery works conceptually
- How CLI, service, and observatory plugins extend platform behaviour
- How Observatory extension manifests are structured
- A practical path to your first extension package

## Prerequisites

- Working Phlo installation
- Basic Python packaging knowledge
- Optional: TypeScript familiarity for Observatory UI modules

## Plugin Surfaces in Phlo

Phlo supports extension points for:

- CLI commands
- Services
- Sources, quality, transforms, hooks
- Observatory UI extensions

You can inspect installed plugins from CLI:

```bash
phlo plugin list
phlo plugin info dagster
```

Expected output:

```text
Plugin inventory and metadata including name, version, and capabilities.
```

## Observatory Extension Manifest Basics

Phlo Observatory defines extension manifest models for compatibility, navigation, slots, and settings.

Example structure:

```python
from phlo_observatory.manifest import (
    ObservatoryExtensionCompatibility,
    ObservatoryExtensionManifest,
    ObservatoryExtensionNavItem,
    ObservatoryExtensionUI,
)

manifest = ObservatoryExtensionManifest(
    name="lineage",
    version="0.1.0",
    compat=ObservatoryExtensionCompatibility(observatory_min="0.1.0"),
    ui=ObservatoryExtensionUI(
        nav=[ObservatoryExtensionNavItem(title="Lineage Graph", to="/graph")]
    ),
)
```

Expected output:

```text
Template snippet prepared for direct use in your project.
```

## Example Extension Class

```python
from importlib import resources
from phlo.plugins import PluginMetadata
from phlo_observatory import ObservatoryExtensionPlugin

class ExampleObservatoryExtension(ObservatoryExtensionPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="example", version="0.1.0", description="Example extension")

    @property
    def manifest(self):
        ...

    @property
    def asset_root(self):
        return resources.files("phlo_observatory_example").joinpath("observatory_assets")
```

Expected output:

```text
Template snippet prepared for direct use in your project.
```

## Extension Runtime Model

```mermaid
graph LR
    A[Python entry point] --> B[Plugin discovery]
    B --> C[Manifest validation]
    C --> D[UI route/nav/slot registration]
    D --> E[Rendered in Observatory]
```

Expected output:

```text
A rendered extension loading diagram from entry point to UI registration.
```

## Build Path for Your Team

1. Start with one small CLI or Observatory extension.
2. Keep manifest minimal and explicit.
3. Add compatibility bounds (`observatory_min`).
4. Ship with integration tests.

## Field Notes: First Plugin, Small Scope, Real Value

The first plugin a team builds often tries to solve too much at once.
That is understandable, but it usually leads to long build cycles and unclear ownership.

A better first plugin is almost boring:

- one clear pain point
- one clear user
- one small interface surface

For example:

- a CLI helper that standardizes a repeated diagnostics command set
- a tiny Observatory nav panel for one high-value signal

Ship that first. Learn from it. Then expand.

Another practical point: extension projects need product thinking too. Ask:

1. Who uses this extension weekly?
2. What workflow becomes faster?
3. How will we know it is useful after release?

Without those answers, plugins become side projects instead of platform improvements.

I also strongly recommend writing a "removal plan" for extensions. If usage is low or maintenance cost is high, retire cleanly. Healthy plugin ecosystems include deletion, not only addition.

When teams treat extensions as small products with owners, release notes, and success criteria, the platform stays flexible without turning chaotic.

## Hands-On Exercise

1. Scaffold a small plugin package in `packages/`.
2. Add one CLI command via a CLI plugin class.
3. Add one simple Observatory nav item and route.
4. Validate plugin appears in `phlo plugin list`.

## Common Issues

1. Entry point group names are misconfigured in package metadata.
2. Extension manifests omit compatibility constraints.
3. UI assets are not bundled into package distributions.
4. Plugin load failures are silent without proper logs.
5. Teams overbuild first extension instead of shipping a minimal slice.

Debug loading failures with [Troubleshooting](../../operations/troubleshooting.md).

## Summary

Extension points let you evolve Phlo into your platform, not just consume defaults. Start narrow, ship reliably, then expand.

## Next Steps

1. Revisit [Part 3](03-ingestion-foundations-with-dlt.md) through [Part 10](10-incident-response-and-debugging.md) and identify extension opportunities.
2. Create a team backlog item for one plugin that removes repeated manual work.

## See Also

- [Part 9: Observability: Metrics, Logs, and Lineage](09-observability-metrics-logs-lineage.md)
- [Part 10: Incident Response and Debugging](10-incident-response-and-debugging.md)
- [Plugin Development Guide](../../guides/plugin-development.md)

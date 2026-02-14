# Part 16: Building Custom Capability Packages

> Prerequisite: Review [Part 13: Capability Primitives](13-capability-primitives.md) and [Part 14: Extending Phlo with Plugins](14-plugin-system.md).

By now you have assets, checks, services, and orchestration in place. The next step is
packaging domain logic so teams can reuse it across projects without copy-paste. This post
shows how to build a custom package that provides assets and resources using capability
primitives and entry points.
For UI extensions that ship alongside packages, see [Part 15: Observatory Extensions](15-observatory-extensions.md).

## What You'll Learn

- How to structure a custom Phlo capability package
- How to implement AssetProviderPlugin and ResourceProviderPlugin
- How to wire entry points for discovery
- How to tie AssetSpec and ResourceSpec together
- How to verify your package is discovered by Phlo

## Prerequisites

- Review Part 13: Capability Primitives for AssetSpec and ResourceSpec
- Review Part 14: Extending Phlo with Plugins for entry point discovery
- Familiarity with Python packaging and editable installs

## When to Create a Custom Package

Create a capability package when you need:

- A reusable asset bundle for a domain (billing, marketing, security)
- Shared resources (clients, IO managers, config loaders)
- Versioned artifacts you can test, publish, and ship across repos

Think of each package as a modular capability pack: specs in, orchestrator adapter out.

## Package Anatomy

A minimal capability package looks like this:

```
phlo-analytics/
├── pyproject.toml
├── README.md
├── src/
│   └── phlo_analytics/
│       ├── __init__.py
│       ├── assets.py
│       ├── resources.py
│       └── plugin.py
```

- `assets.py` defines AssetSpec and AssetCheckSpec instances.
- `resources.py` builds clients and returns ResourceSpec definitions.
- `plugin.py` exposes provider plugins for discovery.

## Asset Provider Pattern

Asset providers emit AssetSpec objects. Keep asset execution logic in small functions and
wrap them with RunSpec.

```python
from collections.abc import Iterable

from phlo.capabilities.runtime import RuntimeContext
from phlo.capabilities.specs import AssetCheckSpec, AssetSpec, CheckResult, MaterializeResult
from phlo.capabilities.specs import RunSpec
from phlo.plugins import AssetProviderPlugin, PluginMetadata


def load_billing_events(context: RuntimeContext) -> Iterable[MaterializeResult]:
    context.logger.info("loading billing events")
    yield MaterializeResult(metadata={"rows": 4200}, status="success")


def check_rows_present(context: RuntimeContext) -> CheckResult:
    return CheckResult(
        check_name="billing_rows_present",
        asset_key="billing.events",
        passed=True,
    )


class BillingAssetProvider(AssetProviderPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="billing_assets",
            version="0.1.0",
            description="Billing domain asset specs",
        )

    def get_assets(self) -> Iterable[AssetSpec]:
        return [
            AssetSpec(
                key="billing.events",
                group="bronze",
                description="Raw billing events",
                run=RunSpec(fn=load_billing_events),
                checks=[
                    AssetCheckSpec(
                        name="billing_rows_present",
                        asset_key="billing.events",
                        fn=check_rows_present,
                    )
                ],
            )
        ]
```

Notes:

- `key` should align with your naming conventions (snake case, domain prefix).
- `run` is optional for static assets, required for executable ones.
- `checks` can live alongside assets for end-to-end contracts.

## Resource Provider Pattern

Resource providers return ResourceSpec objects. These are shared clients, IO managers, or
configuration factories used by your assets.

```python
from phlo.capabilities.specs import ResourceSpec
from phlo.plugins import PluginMetadata, ResourceProviderPlugin

from phlo_analytics.resources import build_billing_client


class BillingResourceProvider(ResourceProviderPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="billing_resources",
            version="0.1.0",
            description="Shared billing clients and helpers",
        )

    def get_resources(self) -> list[ResourceSpec]:
        return [ResourceSpec(name="billing_client", resource=build_billing_client())]
```

Assets that need the resource can declare it in their AssetSpec:

```python
billing_asset = AssetSpec(
    key="billing.events",
    group="bronze",
    resources={"billing_client"},
    run=RunSpec(fn=load_billing_events),
)
```

## Entry Points and Discovery

Add entry points in `pyproject.toml` so Phlo can discover the package:

```toml
[project.entry-points."phlo.plugins.assets"]
billing_assets = "phlo_analytics.plugin:BillingAssetProvider"

[project.entry-points."phlo.plugins.resources"]
billing_resources = "phlo_analytics.plugin:BillingResourceProvider"
```

Then install the package in your environment:

```bash
uv pip install -e .
```


Verify discovery:

```bash
phlo plugin list --type assets
phlo plugin list --type resources
```


## Complete Example: plugin.py

Keep providers close together so users can find the entry points quickly:

```python
from collections.abc import Iterable

from phlo.capabilities.specs import AssetSpec, ResourceSpec
from phlo.plugins import AssetProviderPlugin, PluginMetadata, ResourceProviderPlugin

from phlo_analytics.assets import build_billing_assets
from phlo_analytics.resources import build_billing_resources


class AnalyticsAssets(AssetProviderPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="analytics_assets",
            version="0.1.0",
            description="Analytics domain asset specs",
        )

    def get_assets(self) -> Iterable[AssetSpec]:
        return build_billing_assets()


class AnalyticsResources(ResourceProviderPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="analytics_resources",
            version="0.1.0",
            description="Analytics domain resources",
        )

    def get_resources(self) -> Iterable[ResourceSpec]:
        return build_billing_resources()
```

This pattern keeps the actual asset/resource code in dedicated modules while the plugin
class remains a thin wrapper for discovery.

## Hands-On Exercise: Scaffold a Package

1. Create a new package directory with `pyproject.toml`.
2. Add an `AssetProviderPlugin` implementation.
3. Register entry points under `phlo.plugins.assets` and `phlo.plugins.resources`.
4. Run `phlo plugin list` to confirm discovery.

## Common Issues

- **Package not installed in the environment**

```bash
uv pip show phlo-analytics
```


Fix: reinstall with `uv pip install -e .` from the package root.

- **Entry points not detected**

```bash
uv run python -c "import importlib.metadata as m; print(m.entry_points(group='phlo.plugins.assets'))"
```


Fix: confirm `pyproject.toml` entry points and reinstall the package.

- **Assets not visible in Phlo**

```bash
phlo plugin list --type assets
```


Fix: restart the runtime and confirm the plugin metadata.

See [Troubleshooting Guide](../operations/troubleshooting.md) for deeper diagnostics.

## See Also

See also: [Part 13: Capability Primitives](13-capability-primitives.md), [Part 14: Extending Phlo with Plugins](14-plugin-system.md), [Part 15: Observatory Extensions](15-observatory-extensions.md). Reference: [Phlo API Reference](../reference/phlo-api.md).

## Summary

Custom capability packages let teams ship reusable assets and resources with clear
entry points and versioned releases. Use AssetProviderPlugin and ResourceProviderPlugin
to keep domain logic centralised and discoverable across projects.


## Next Steps

- Package your first domain module and publish internally
- Add tests that validate specs returned by your providers
- Wire your assets into an orchestrator adapter (Dagster or custom)

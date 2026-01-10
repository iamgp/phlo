# Observatory Extensions

Observatory extensions are Python packages that expose a manifest and optional UI assets. The
Phlo API filters extensions that do not meet the `compat.observatory_min` requirement.

## Manifest

```yaml
name: string
version: string
compat:
  observatory_min: string
settings:
  schema: JSONSchema
  defaults: object
  scope: global | extension
ui:
  routes:
    - path: /extensions/<name>/...
      module: <asset_url>
      export: registerRoutes
  nav:
    - title: string
      to: /extensions/<name>/...
  slots:
    - slot_id: string
      module: <asset_url>
      export: registerSlot
  settings:
    - module: <asset_url>
      export: registerSettings
```

## Runtime hooks

- `registerRoutes(ctx)` returns TanStack routes.
- `registerSlot(registry)` registers a component for the slot entry being loaded.
- `registerSettings(registry)` registers settings panels with `{id,title,description,component,order}`.
  Use `registry.loadSettings()` and `registry.saveSettings(next)` to read/write settings.
  `scope: global` stores settings that other extensions can access via the same endpoint.

## Slot IDs

- `dashboard.after-cards`
- `hub.after-stats`

## Example

See `packages/phlo-observatory-example` for a minimal extension package:

- Plugin entry point: `phlo_observatory_example.observatory_plugin:ExampleObservatoryExtension`
- Asset bundle: `packages/phlo-observatory-example/src/phlo_observatory_example/observatory_assets/example.js`

## Verification

```bash
phlo plugin list --type observatory
curl http://localhost:4000/api/observatory/extensions
curl http://localhost:4000/api/observatory/extensions/example/settings
```

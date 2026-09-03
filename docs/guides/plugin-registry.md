# Plugin Registry

The plugin registry is a centralized catalog of available Phlo plugins. It provides
search, caching, and offline fallback so CLI commands like `phlo plugin search` work
without network access.

## Registry data format

The canonical registry lives at `registry/plugins.json`. Top-level structure:

```json
{
  "$schema": "https://registry.phlohouse.com/schema/v1.json",
  "version": "1.0.0",
  "updated_at": "2025-12-22T00:00:00Z",
  "plugins": {
    "dagster": { ... },
    "postgres": { ... }
  }
}
```

Each plugin entry:

```json
{
  "type": "service",
  "package": "phlo-dagster",
  "version": "0.1.0",
  "description": "Data orchestration platform",
  "author": "Phlo Team",
  "homepage": "https://github.com/...",
  "tags": ["orchestration", "core"],
  "verified": true,
  "core": true
}
```

## RegistryPlugin dataclass

**Module:** `phlo.plugins.registry_client`

```python
@dataclass(frozen=True)
class RegistryPlugin:
    name: str          # plugin identifier (registry key)
    type: str          # source | quality | transform | service | hooks | ...
    package: str       # pip-installable package name
    version: str       # latest published version
    description: str   # human-readable summary
    author: str        # maintainer
    homepage: str | None  # project URL
    tags: list[str]    # search/filter tags
    verified: bool     # verified by Phlo team
    core: bool         # ships with core install
```

## API

### fetch_registry

```python
def fetch_registry(force_refresh: bool = False) -> dict[str, Any]:
```

Returns the raw registry payload with caching. Pass `force_refresh=True` to bypass
the cache TTL.

### list_registry_plugins

```python
def list_registry_plugins() -> list[RegistryPlugin]:
```

Returns all plugins as normalized `RegistryPlugin` entries.

### search_plugins

```python
def search_plugins(
    query: str | None = None,
    plugin_type: str | None = None,
    tags: list[str] | None = None,
) -> list[RegistryPlugin]:
```

Filter plugins by:

- `query` — substring match against name, description, package, and tags.
- `plugin_type` — exact match on `type` field (`"service"`, `"source"`, etc.).
- `tags` — all provided tags must be present (case-insensitive subset match).

Filters are applied in order: type → tags → query.

### get_plugin

```python
def get_plugin(name: str) -> RegistryPlugin | None:
```

Returns a single plugin by registry key, or `None`.

## Caching

The registry client caches the fetched payload in-memory. The cache is valid for
`plugin_registry_cache_ttl_seconds` (default: 3600s / 1 hour).

```python
def clear_registry_cache() -> None:
```

Resets the cache — useful in tests or after manual registry updates.

## Fallback chain

When `fetch_registry()` is called:

1. **Remote URL** — fetches from `plugin_registry_url` with `plugin_registry_timeout_seconds`
   timeout. Validates the payload contains a `plugins` section.
2. **Bundled package data** — loads `phlo/plugins/registry_data.json` from the installed
   package via `importlib.resources`.
3. **Repo file** — walks parent directories to find `registry/plugins.json`.

If step 1 fails (network error, timeout, invalid payload), falls back to step 2.
If step 2 fails (file not found in package), falls back to step 3.
Raises `FileNotFoundError` if all sources are exhausted.

## Configuration

Settings in `phlo.config.settings`:

| Setting                             | Default                                          | Description              |
|-------------------------------------|--------------------------------------------------|--------------------------|
| `plugin_registry_url`               | `https://registry.phlohouse.com/plugins.json`    | Remote registry URL      |
| `plugin_registry_cache_ttl_seconds` | `3600`                                           | Cache lifetime (seconds) |
| `plugin_registry_timeout_seconds`   | `10`                                             | HTTP fetch timeout       |

Override via `.phlo/.env` or environment variables.

## Registry schema

The registry is validated against a JSON Schema at `registry/schema/v1.json`.

Required top-level fields: `$schema`, `version`, `updated_at`, `plugins`.

Each plugin entry requires: `type`, `package`, `version`, `description`, `author`,
`tags`, `verified`. The `type` field is constrained to:
`source`, `quality`, `transform`, `service`, `hooks`, `assets`, `resources`,
`orchestrators`, `catalogs`.

Optional fields: `homepage`, `core`.

## See also

- [Plugin Development](plugin-development.md) — creating and publishing plugins
- [Configuration Reference](../reference/configuration-reference.md) — all settings

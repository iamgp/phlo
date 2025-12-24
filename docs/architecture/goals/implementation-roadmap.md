# Plugin DX Implementation Roadmap

This document outlines what changes are needed to achieve the [DX goals](./plugin-dx.md).

## Status (as of 2025-12-24)

- **Phase 0**: COMPLETED - Package-first services, core is glue-only
- **Phase 1**: COMPLETED - Unified discovery flow
- **Phase 2**: COMPLETED - Naming cleanup
- **Phase 3**: COMPLETED - User service overrides
- **Phase 4**: COMPLETED - Enable/disable services
- **Phase 5**: COMPLETED - Inline custom services (with test coverage)
- **Phase 6**: COMPLETED - Enhanced CLI discoverability (runtime status, ports, disabled services)
- **Phase 7**: COMPLETED - Documentation updated, phlo-fastapi removed from registry

## Key Architectural Changes

1. **Observatory as package** - Remains a service plugin (not core)
2. **phlo-api backend** - Service plugin exposing phlo internals
3. **Unified discovery** - Single flow for plugins and services
4. **User service overrides** - Enable `phlo.yaml` customization
5. **Remove phlo-fastapi** - Superseded by postgrest and phlo-api

---

## Phase 0: Package-First Services

The most significant change is keeping **Observatory and phlo-api as packages** while phlo core stays glue-only.

### Current State

```
pip install phlo                  # Core only
pip install phlo-observatory      # Separate package
```

Observatory is a Python package wrapper around a TanStack Start app, registered via entry points.

### Target State

```
pip install phlo                  # Core glue only
pip install phlo-observatory      # UI package
pip install phlo-api              # Backend for Observatory
```

Observatory and phlo-api ship as packages, discovered via service plugins.

### Changes Required

#### 1. Keep Observatory as a Service Package

Maintain Observatory in `packages/phlo-observatory` with its own `service.yaml` and plugin entry point:

```
packages/phlo-observatory/
└── src/phlo_observatory/service.yaml
```

#### 2. Update Service Discovery

Modify `src/phlo/services/discovery.py` to load **only package services** from plugins.

#### 3. Create phlo-api Backend Package

Implement the FastAPI service in `packages/phlo-api/src/phlo_api/` and expose service metadata via the service plugin.

#### 4. Keep Plugin Wrapper for Observatory

Observatory remains a plugin package with a `service.yaml` and entry point registration.

#### 5. Optional Defaults Extra

```toml
[project.optional-dependencies]
defaults = [
    "phlo-dagster",
    "phlo-postgres",
    "phlo-trino",
    "phlo-nessie",
    "phlo-minio",
]
```

#### 6. Remove phlo-fastapi Package

Delete `packages/phlo-fastapi/` - superseded by:

- **postgrest** for auto-generated REST APIs
- **phlo-api** for phlo-specific internal APIs

**Effort**: ~2-3 days

---

## Phase 1: Unified Discovery Flow

### Current Problem

Two separate discovery systems:

- `src/phlo/plugins/discovery.py` - discovers **plugins** via entry points
- `src/phlo/services/discovery.py` - discovers **services** from plugins

Confusing naming and duplicated logic.

### Solution

Consolidate into a single flow:

```
src/phlo/discovery/
├── __init__.py
├── plugins.py       # Entry point discovery for all plugin types
├── services.py      # ServiceDefinition loading (from core + plugins)
└── registry.py      # Remote registry search
```

**Key changes:**

- Rename `plugins/discovery.py` → `discovery/plugins.py`
- Rename `services/discovery.py` → `discovery/services.py`
- Single import: `from phlo.discovery import discover_plugins, discover_services`

**Effort**: ~1 day

---

## Phase 2: Naming Cleanup

### "Cascade" → "Phlo"

Several files still reference "Cascade":

- `src/phlo/cli/plugin.py` docstring: "CLI commands for managing Cascade plugins"
- Possibly other locations

**Action**: Global search/replace and verify.

**Effort**: ~0.5 days

---

## Phase 3: User Service Overrides

### Current Behavior

Users cannot customize installed service configs via `phlo.yaml`.

### Proposed Solution

```yaml
# phlo.yaml
name: my-lakehouse

services:
  dagster:
    ports:
      - "3005:3000"
    environment:
      CUSTOM_FLAG: "enabled"
    enabled: false # Disable

  observatory:
    port: 8080
```

### Implementation Changes

**1. Update `config_schema.py`**

Add `ServiceOverride` model:

```python
class ServiceOverride(BaseModel):
    enabled: bool = True
    ports: list[str] | None = None
    environment: dict[str, str] | None = None
    volumes: list[str] | None = None
    depends_on: list[str] | None = None
    command: list[str] | str | None = None
```

**2. Update `composer.py`**

Apply user overrides in `_build_service_config()`:

```python
def _apply_user_overrides(self, config, overrides):
    if overrides.ports:
        config["ports"] = overrides.ports
    if overrides.environment:
        config.setdefault("environment", {})
        config["environment"].update(overrides.environment)
    # etc.
```

**3. Update `services.py` CLI**

Load and pass overrides to composer.

**Effort**: ~2 days

---

## Phase 4: Enable/Disable Services

### Solution

```yaml
services:
  superset:
    enabled: false
```

### Implementation

In `ServiceDiscovery.get_default_services()`:

```python
def get_default_services(self, disabled_services=None):
    disabled = set(disabled_services or [])
    return [
        s for s in self._services.values()
        if s.default and s.name not in disabled
    ]
```

**Effort**: ~0.5 days

---

## Phase 5: Inline Custom Services

### Solution

```yaml
services:
  custom-api:
    type: inline
    image: my-registry/api:latest
    ports:
      - "4000:4000"
    depends_on:
      - trino
```

### Implementation

Add `ServiceDefinition.from_inline()` and detect in CLI.

**Effort**: ~1 day

---

## Phase 6: Enhanced Discoverability

### Proposed CLI Output

```
$ phlo services list

Package Services (installed):
  ✓ observatory      Running    :3001   Phlo UI
  ✓ phlo-api         Running    :4000   Phlo API backend
  ✓ dagster          Running    :3000   Orchestration
  ✓ postgres         Running    :5432   Database
  ✗ superset         Disabled           (disabled in phlo.yaml)

Custom Services (phlo.yaml):
  ✓ custom-api       Running    :4000   (inline)
```

**Effort**: ~1 day

---

## Phase 7: Documentation & Cleanup

1. Update `docs/guides/service-packages.md`
2. Update README examples
3. Add examples to `examples/github-stats/phlo.yaml`
4. Remove `packages/phlo-fastapi/`
5. Build/release strategy for Observatory (Docker image in CI)

**Effort**: ~1 day

---

## Summary

| Phase | Description                     | Effort         |
| ----- | ------------------------------- | -------------- |
| **0** | Package-first Observatory + phlo-api | 2-3 days   |
| **1** | Unified discovery flow          | 1 day          |
| **2** | Naming cleanup (Cascade → Phlo) | 0.5 days       |
| **3** | User service overrides          | 2 days         |
| **4** | Enable/disable services         | 0.5 days       |
| **5** | Inline custom services          | 1 day          |
| **6** | Enhanced discoverability        | 1 day          |
| **7** | Documentation & cleanup         | 1 day          |
|       | **Total**                       | **~9-10 days** |

---

## Registry Clarification

The two registries serve different purposes:

| Source                            | Purpose                                                                 |
| --------------------------------- | ----------------------------------------------------------------------- |
| `registry/plugins.json`           | **Complete offerings** - all available plugins for `phlo plugin search` |
| Entry points (installed packages) | **What's actually installed** - for service discovery                   |

This is correct and intentional. The JSON registry enables discoverability of uninstalled plugins.

---

## Testing Strategy

### Unit Tests

- `test_service_discovery_plugins_only()` - Service discovery via plugins only
- `test_service_override_merge()` - Verify config merging
- `test_enabled_false_excludes_service()` - Verify disable logic
- `test_inline_service_creation()` - Verify inline parsing

### Integration Tests

- Start services with override in phlo.yaml
- Verify disabled service doesn't start
- Verify inline service starts correctly
- Verify Observatory can reach phlo-api

### E2E Tests

- Full workflow: install packages → override → start → verify
- Observatory shows installed plugins via phlo-api

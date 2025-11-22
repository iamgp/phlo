# Cascade Installable Package Plan (Updated)

**Date:** 2025-11-22
**Status:** In Progress - Plugin system already implemented!

---

## Executive Summary

Transform Cascade into an installable Python package where users can:
1. ✅ Install Cascade via `pip install cascade` (packaging ready)
2. ✅ Extend with plugins via entry points (plugin system exists)
3. ⬜ Create minimal project directories with workflow files (need workflow discovery)
4. ⬜ Use enhanced CLI for project initialization (partially exists)
5. ⬜ Run Dagster with custom workflows (need definitions integration)

---

## What Already Exists ✅

### 1. Plugin System (Complete)

**Location:** `src/cascade/plugins/`

**Components:**
- `base.py` - Base classes for all plugin types
  - `Plugin` - Abstract base
  - `SourceConnectorPlugin` - Data source connectors
  - `QualityCheckPlugin` - Quality validation checks
  - `TransformationPlugin` - Data transformations
  - `PluginMetadata` - Standardized metadata

- `discovery.py` - Entry point-based plugin discovery
  - Auto-discovers plugins on import
  - Three plugin types supported
  - Validates plugin interfaces

- `registry.py` - Global plugin registry
  - Thread-safe registration
  - Type-safe retrieval
  - List/search operations

- `examples.py` - Example plugins for reference

**Entry Points Defined:** `pyproject.toml:41-50`
```toml
[project.entry-points."cascade.plugins.sources"]
# Example: my_source = "my_package.my_module:MySourceConnector"

[project.entry-points."cascade.plugins.quality"]
# Example: my_check = "my_package.my_module:MyQualityCheck"

[project.entry-points."cascade.plugins.transforms"]
# Example: my_transform = "my_package.my_module:MyTransform"
```

### 2. Quality Check System (Complete)

**Location:** `src/cascade/quality/`

**Components:**
- `decorator.py` - `@cascade_quality` decorator
- `checks.py` - Built-in quality checks
- `examples.py` - Example quality workflows

### 3. CLI Scaffolding (Partial)

**Location:** `src/cascade/cli/`

**Existing:**
- `main.py` - CLI entry point
- `scaffold.py` - Workflow scaffolding logic
- `create_workflow.py` - Workflow creation (from previous version)

**What works:**
- Can scaffold ingestion workflows
- Generates schema, asset, and test files

**What's missing:**
- `cascade init` - Project initialization
- `cascade dev` - Development server
- Workflow discovery for user projects

### 4. Package Configuration (Ready)

**`pyproject.toml` is well-configured:**
- ✅ Modern build system (hatchling)
- ✅ Entry point: `cascade` CLI
- ✅ Plugin entry points defined
- ✅ Dependencies specified
- ✅ Dynamic versioning (uv-dynamic-versioning)

---

## What's Missing ⬜

### 1. User Workflow Discovery System

**Problem:** Plugin system loads *installable packages*, not *local workflow files*.

**Need:** System to discover and load user workflow files from `workflows/` directory.

**Implementation:**
```python
# cascade/framework/discovery.py (NEW)
def discover_user_workflows(workflows_path: Path) -> Definitions:
    """
    Discover workflow files in user project.

    Scans workflows/ directory for:
    - Ingestion assets (decorated with @cascade_ingestion)
    - Quality checks (decorated with @cascade_quality)
    - Schemas (Pandera models)

    Returns merged Dagster Definitions.
    """
    # Add workflows to Python path
    sys.path.insert(0, str(workflows_path.parent))

    # Import all .py files (triggers decorator registration)
    workflow_modules = []
    for py_file in workflows_path.rglob("*.py"):
        if py_file.name.startswith("_"):
            continue
        module = import_user_module(py_file)
        workflow_modules.append(module)

    # Collect registered assets/jobs/schedules
    return merge_workflow_definitions(workflow_modules)
```

### 2. Definitions Entry Point for User Projects

**Problem:** `cascade/definitions.py` currently loads in-package workflows.

**Need:** New entry point that discovers external workflows.

**Implementation:**
```python
# cascade/framework/definitions.py (NEW)
from cascade.config import get_settings
from cascade.framework.discovery import discover_user_workflows
from cascade.framework.resources import build_resources

def build_definitions() -> Definitions:
    """
    Build Dagster definitions by merging:
    1. Core Cascade framework resources
    2. User workflows from external directory
    3. Installed plugins
    """
    settings = get_settings()

    # Load user workflows
    user_workflows = discover_user_workflows(
        workflows_path=Path(settings.workflows_path)
    )

    # Build core resources
    core_resources = Definitions(
        resources=build_resources(settings)
    )

    # Discover and load plugins
    plugin_defs = discover_plugin_definitions()

    # Merge all definitions
    return Definitions.merge(
        core_resources,
        user_workflows,
        plugin_defs,
    )

# Export for Dagster
defs = build_definitions()
```

### 3. CLI Enhancements

**Need these new commands:**

#### `cascade init`
```bash
# Initialize new project
$ cascade init my-data-project

# Creates:
my-data-project/
├── pyproject.toml        # Minimal: dependencies = ["cascade"]
├── .env
├── workflows/
│   ├── __init__.py
│   ├── ingestion/
│   └── schemas/
├── transforms/dbt/       # Optional
├── tests/
└── workspace.yaml        # Dagster config
```

#### `cascade dev`
```bash
# Start Dagster with user workflows
$ cascade dev

# Auto-discovers workflows in ./workflows/
# Launches Dagster UI at http://localhost:3000
```

#### `cascade services` (optional)
```bash
# Manage infrastructure services
$ cascade services start    # Start Docker services
$ cascade services stop     # Stop services
$ cascade services status   # Show status
```

### 4. Configuration Updates

**Add to `cascade/config.py`:**
```python
class Settings(BaseSettings):
    # ... existing fields ...

    # NEW: User project paths
    workflows_path: Path = Field(
        default=Path("workflows"),
        description="Path to user workflows directory"
    )

    # ENHANCED: Make dbt_project_dir configurable
    dbt_project_dir_override: Optional[str] = Field(
        default=None,
        description="Override dbt project directory path"
    )

    @computed_field
    @property
    def dbt_project_dir(self) -> str:
        """dbt project directory - configurable via override."""
        if self.dbt_project_dir_override:
            return self.dbt_project_dir_override

        if os.path.exists("/dbt"):  # Container environment
            return "/dbt"
        else:  # Local development
            return "transforms/dbt"
```

### 5. Package vs User Code Separation

**Move to separate repo or mark as examples:**
```
# Current (in package):
src/cascade/defs/ingestion/nightscout/
src/cascade/defs/ingestion/github/
src/cascade/schemas/glucose.py
src/cascade/schemas/github.py

# Should be:
cascade-examples/ (separate repo)
└── examples/
    ├── nightscout/
    │   ├── workflows/
    │   └── transforms/
    └── github/
        ├── workflows/
        └── transforms/
```

---

## Architecture: Two Discovery Systems

Cascade needs **both** plugin discovery (exists) and workflow discovery (need):

### Plugin Discovery (Exists ✅)
**Purpose:** Load installable extensions
**Mechanism:** Python entry points
**Use case:** Third-party connectors, reusable quality checks

**Example:**
```bash
# Install a community plugin
pip install cascade-plugin-salesforce

# Automatically discovered and available
from cascade.plugins import get_source_connector
salesforce = get_source_connector("salesforce")
```

**Plugin package structure:**
```python
# cascade-plugin-salesforce/setup.py
setup(
    name="cascade-plugin-salesforce",
    entry_points={
        "cascade.plugins.sources": [
            "salesforce = cascade_salesforce:SalesforceConnector"
        ]
    }
)
```

### Workflow Discovery (Need ⬜)
**Purpose:** Load user's project-specific workflows
**Mechanism:** File system import from `workflows/`
**Use case:** User's custom ingestion workflows, schemas, quality checks

**Example:**
```python
# my-project/workflows/ingestion/weather/observations.py
from cascade.ingestion import cascade_ingestion
from workflows.schemas.weather import WeatherObservations

@cascade_ingestion(
    table_name="weather_observations",
    unique_key="id",
    validation_schema=WeatherObservations,
)
def weather_observations(partition_date: str):
    # User's custom ingestion logic
    ...
```

### Combined Architecture

```
┌─────────────────────────────────────────────────┐
│  CASCADE PACKAGE (pip install cascade)          │
│                                                  │
│  Plugin Discovery        Workflow Discovery     │
│  (exists ✅)             (need ⬜)               │
│  ↓                       ↓                       │
│  Entry points            File imports            │
└─────────────────────────────────────────────────┘
         ▼                        ▼
   ┌─────────────┐        ┌──────────────┐
   │   PLUGINS   │        │ USER PROJECT │
   │             │        │              │
   │ pip install │        │ workflows/   │
   │ cascade-    │        │ transforms/  │
   │ plugin-xyz  │        │ schemas/     │
   └─────────────┘        └──────────────┘
         │                        │
         └────────┬───────────────┘
                  ▼
         ┌─────────────────┐
         │ DAGSTER RUNTIME │
         │                 │
         │ Merged          │
         │ Definitions     │
         └─────────────────┘
```

---

## Updated Implementation Phases

### Phase 1: Workflow Discovery System ⬜ (2 weeks)
**Goal:** Enable loading workflows from external directories

Tasks:
- [ ] Create `cascade/framework/discovery.py`
- [ ] Implement `discover_user_workflows()`
- [ ] Add workflow path to Settings
- [ ] Test with example user project
- [ ] Handle import errors gracefully

**Acceptance:**
- Can load workflows from `workflows/` directory
- Decorators register assets correctly
- Error messages are clear and helpful

### Phase 2: Enhanced CLI ⬜ (1 week)
**Goal:** Make it easy to create and run user projects

Tasks:
- [ ] Implement `cascade init` command
- [ ] Implement `cascade dev` command
- [ ] Update `cascade create-workflow` for user projects
- [ ] Add project templates to package data
- [ ] Test end-to-end workflow

**Acceptance:**
- Can create new project with `cascade init`
- Can scaffold workflows in user project
- Can run Dagster with `cascade dev`

### Phase 3: Definitions Integration ⬜ (1 week)
**Goal:** Merge user workflows with framework resources

Tasks:
- [ ] Create `cascade/framework/definitions.py`
- [ ] Integrate workflow discovery
- [ ] Integrate plugin discovery
- [ ] Update workspace.yaml template
- [ ] Test with multiple user workflows

**Acceptance:**
- User workflows appear in Dagster UI
- Can materialize user assets
- Plugins and workflows work together

### Phase 4: Documentation & Examples ⬜ (1 week)
**Goal:** Clear documentation and migration guide

Tasks:
- [ ] Write "Getting Started" guide
- [ ] Create migration guide for existing users
- [ ] Document plugin development
- [ ] Create example user projects
- [ ] Video tutorial (optional)

**Acceptance:**
- New user can get started in < 5 minutes
- Existing users can migrate smoothly
- Plugin developers have clear guide

### Phase 5: Package Cleanup ⬜ (1 week)
**Goal:** Separate examples from core package

Tasks:
- [ ] Move examples to separate repo
- [ ] Keep only framework code in package
- [ ] Update imports and tests
- [ ] Create `cascade-examples` repository
- [ ] Link examples in documentation

**Acceptance:**
- Package size reduced
- Clear separation of concerns
- Examples still accessible

### Phase 6: Publishing & Distribution ⬜ (1 week)
**Goal:** Publish to PyPI

Tasks:
- [ ] Set up PyPI account/credentials
- [ ] Configure CI/CD for releases
- [ ] Test installation from TestPyPI
- [ ] Publish v1.0.0 to PyPI
- [ ] Verify installation works

**Acceptance:**
- `pip install cascade` works
- All features functional
- Documentation deployed

---

## Transform Location Question

### Do transforms have to be in a separate folder?

**Answer: No, but it's recommended.**

### Current Behavior

The `dbt_project_dir` is already **configurable** in `cascade/config.py`:

```python
@computed_field
@property
def dbt_project_dir(self) -> str:
    """dbt project directory - /dbt in container, transforms/dbt locally."""
    if os.path.exists("/dbt"):  # Container environment
        return "/dbt"
    else:  # Local development
        return "transforms/dbt"
```

### Recommended Structure

**Option 1: Separate (Recommended)**
```
my-project/
├── workflows/          # Python workflows
│   ├── ingestion/
│   └── schemas/
└── transforms/         # dbt transformations
    └── dbt/
        ├── dbt_project.yml
        └── models/
```

**Pros:**
- ✅ Clear separation of concerns
- ✅ Respects dbt project conventions
- ✅ Easier to run dbt independently
- ✅ Standard practice in data platforms

**Option 2: Under workflows**
```
my-project/
└── workflows/
    ├── ingestion/
    ├── schemas/
    └── transforms/
        └── dbt/
            ├── dbt_project.yml
            └── models/
```

**Pros:**
- ✅ Everything in one place
- ✅ Simpler top-level structure

**Cons:**
- ⚠️ Mixes Python and dbt conventions
- ⚠️ Less clear what's what

### Configuration

Users can configure via `cascade_config.py`:

```python
CASCADE_CONFIG = {
    # Option 1: Separate
    "dbt_project_dir": "transforms/dbt",

    # Option 2: Under workflows
    "dbt_project_dir": "workflows/transforms/dbt",

    # Option 3: Custom location
    "dbt_project_dir": "../shared-dbt",
}
```

### Recommendation

**Keep separate** because:
1. dbt has its own project structure and conventions
2. Clear separation between ingestion (Python) and transformation (SQL)
3. Easier for teams to understand and maintain
4. Standard practice across data platforms (dbt Cloud, Astronomer, etc.)
5. Can run `dbt` commands independently

---

## Updated Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| **Plugin System** | - | ✅ Complete |
| **Quality System** | - | ✅ Complete |
| **CLI Scaffolding** | - | 🟡 Partial |
| 1. Workflow Discovery | 2 weeks | ⬜ To Do |
| 2. Enhanced CLI | 1 week | ⬜ To Do |
| 3. Definitions Integration | 1 week | ⬜ To Do |
| 4. Documentation | 1 week | ⬜ To Do |
| 5. Package Cleanup | 1 week | ⬜ To Do |
| 6. Publishing | 1 week | ⬜ To Do |

**Total remaining:** ~7 weeks (down from 8!)

---

## Next Steps (Priority Order)

1. **Implement workflow discovery** - Core functionality
2. **Create `cascade init` command** - User experience
3. **Build user project template** - Testing
4. **Integrate with definitions** - Make it work end-to-end
5. **Write migration guide** - Help existing users
6. **Publish to PyPI** - Make it real!

---

## Questions Resolved

### 1. Do transforms have to be separate?
**Answer:** No, but recommended for clarity. Already configurable via `dbt_project_dir`.

### 2. What about the plugin system in the plan?
**Answer:** Already implemented! Use it for installable extensions. Still need workflow discovery for local files.

### 3. Should we keep both systems?
**Answer:** Yes! They serve different purposes:
- **Plugins:** Reusable, installable components (pip install)
- **Workflows:** User-specific, project-local definitions (file imports)

---

## Success Metrics

### Developer Experience
- ✅ Install via pip
- ✅ New project in < 5 minutes
- ✅ No core package modifications
- ✅ Plugins and workflows work together

### Technical Quality
- ✅ Clean architecture (plugin + workflow discovery)
- ✅ Proper dependency management
- ✅ Comprehensive testing
- ✅ Clear error messages

### Community Growth
- ✅ Lower barrier to entry
- ✅ Ecosystem of plugins
- ✅ Easy to share workflows
- ✅ Better team collaboration

---

**This updated plan builds on the excellent plugin system already in place and focuses on the remaining work needed to make Cascade a complete installable package.**

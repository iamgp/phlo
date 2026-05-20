# Plugin System Architecture

This document describes Phlo's plugin system, all plugin types, which packages provide them, and how they connect.

## Overview

Phlo uses Python entry points for plugin discovery. Packages declare plugins in their `pyproject.toml`, and Phlo discovers and registers them at runtime.

## Plugin Types

### Provider Plugins (Core Primitives)

Provider plugins supply the core primitives that other packages depend on:

| Plugin Type | Entry Point | Purpose | Package |
|-------------|-------------|---------|---------|
| `orchestrators` | `phlo.plugins.orchestrators` | Orchestration runtime (Dagster) | phlo-dagster |
| `quality_providers` | `phlo.plugins.quality_providers` | Quality primitives (phlo.quality.pandera(...), checks) | phlo-pandera |
| `ingestion_providers` | `phlo.plugins.ingestion_providers` | Ingestion primitives (phlo.ingest.dlt(...)) | phlo-dlt |
| `transformation_providers` | `phlo.plugins.transformation_providers` | Transformation primitives (dbt assets) | phlo-dbt |
| `resource_providers` | `phlo.plugins.resources` | Infrastructure resources (DB, storage) | phlo-trino, phlo-postgres, phlo-iceberg, phlo-delta |
| `asset_providers` | `phlo.plugins.assets` | Asset spec generation | phlo-dbt, phlo-dlt |
| `catalogs` | `phlo.plugins.catalogs` | Table catalog (Iceberg, Nessie) | phlo-iceberg |

### Implementation Plugins (Individual Implementations)

These provide individual implementations of specific capabilities:

| Plugin Type | Entry Point | Purpose | Package |
|-------------|-------------|---------|---------|
| `quality_checks` | `phlo.plugins.quality` | Individual quality checks | phlo-core-plugins |
| `source_connectors` | `phlo.plugins.sources` | Data source connectors | phlo-core-plugins |
| `transformations` | `phlo.plugins.transforms` | Data transformations | phlo-core-plugins |
| `services` | `phlo.plugins.services` | Runtime services | Various |
| `cli_commands` | `phlo.plugins.cli` | CLI commands | Various |
| `hooks` | `phlo.plugins.hooks` | Event hooks | Various |

## How Discovery Works

1. Package declares entry points in `pyproject.toml`:

```toml
[project.entry-points."phlo.plugins.quality_providers"]
pandera = "phlo_pandera.plugin:PanderaQualityProvider"
```

2. On `import phlo` or `discover_plugins()`, Phlo scans entry points

3. Plugins are validated and registered in `PluginRegistry`

4. Packages access plugins via getters:
   - `get_quality_provider("pandera")`
   - `get_ingestion_provider("dlt")`
   - `get_transformation_provider("dbt")`

## Data Flow

```mermaid
flowchart TB
    subgraph Packages["Installed Packages"]
        DLT["phlo-dlt<br/>Ingestion Provider"]
        DBT["phlo-dbt<br/>Transformation Provider"]
        PANDERA["phlo-pandera<br/>Quality Provider"]
        TRINO["phlo-trino<br/>Resource Provider"]
        DAGSTER["phlo-dagster<br/>Orchestrator"]
        ICEBERG["phlo-iceberg<br/>Catalog"]
    end

    subgraph Discovery["Plugin Discovery"]
        EP["Entry Points<br/>pyproject.toml"]
        DISC["discover_plugins()"]
        REG["PluginRegistry"]
        VALID["validate_plugin_interface()"]
    end

    subgraph Providers["Provider Layer"]
        QI["quality_providers<br/>PanderaQualityProvider"]
        II["ingestion_providers<br/>DLTIngestionProvider"]
        TI["transformation_providers<br/>DbtTransformationProvider"]
        OI["orchestrators<br/>DagsterOrchestrator"]
        RI["resource_providers<br/>TrinoResourceProvider"]
        AI["asset_providers<br/>DbtAssetProvider"]
        CI["catalogs<br/>IcebergCatalog"]
    end

    subgraph Specs["Capability Specs Layer"]
        AS["AssetSpec"]
        RS["ResourceSpec"]
        CS["CheckSpec"]
        CAT["CatalogSpec"]
    end

    subgraph Adapter["Orchestrator Adapter"]
        BUILD["build_definitions()"]
        WIRE["Wire specs to<br/>Dagster definitions"]
    end

    subgraph Runtime["Runtime"]
        DAGTASK["Dagster<br/>Daemon"]
        DLT_RUN["dlt Pipeline"]
        DBT_RUN["dbt Models"]
        TRINO_Q["Trino Query"]
    end

    Packages --> EP
    EP --> DISC
    DISC --> REG
    REG --> VALID

    QI -.->|get_decorator| PANDERA
    II -.->|get_asset_retriever| DLT
    TI -.->|get_asset_retriever| DBT
    OI --> DAGSTER
    RI --> TRINO
    CI --> ICEBERG

    DLT -->|provides| AS
    DBT -->|provides| AS
    PANDERA -->|provides| CS
    TRINO -->|provides| RS
    ICEBERG -->|provides| CAT

    AS --> BUILD
    CS --> BUILD
    RS --> BUILD
    CAT --> BUILD

    BUILD --> WIRE
    WIRE --> DAGTASK

    DAGTASK -->|runs| DLT_RUN
    DAGTASK -->|runs| DBT_RUN
    DAGTASK -->|queries| TRINO_Q
```

## End-to-End Example

A complete flow from code to execution:

```mermaid
sequenceDiagram
    participant D as Developer
    participant P as phlo CLI
    participant DIS as discover_plugins()
    participant REG as PluginRegistry
    participant QP as QualityProvider
    participant IP as IngestionProvider
    participant TP as TransformationProvider
    participant DA as DagsterAdapter
    participant DAGT as Dagster

    D->>P: phlo services start
    P->>DIS: discover_plugins()
    DIS->>REG: register all plugins
    REG->>QP: PanderaQualityProvider
    REG->>IP: DLTIngestionProvider
    REG->>TP: DbtTransformationProvider

    D->>P: import phlo
    P->>IP: get_decorator()
    IP-->>P: phlo.ingest.dlt(...)

    D->>P: phlo.ingest.dlt(...)<br/>def load_users(): ...
    P->>DA: build_definitions()
    DA-->>P: Dagster Assets

    P->>DAGT: dagster-webserver
    DAGT->>DA: fetch definitions
    DA-->>DAGT: Assets[load_users, dbt_model, quality_check]

    D->>P: phlo materialize load_users
    P->>DAGT: trigger materialization
    DAGT->>DAGT: execute load_users<br/>dbt run<br/>quality check
```

## Provider Pattern

The "provider" plugins (`quality_providers`, `ingestion_providers`, `transformation_providers`) follow a consistent pattern:

```python
class QualityProviderPlugin(Plugin, ABC):
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Plugin name, version, description."""

    @abstractmethod
    def get_decorator(self) -> Callable:
        """Returns phlo.quality.pandera(...) or equivalent."""

    @abstractmethod
    def get_check_classes(self) -> dict[str, type]:
        """Returns {name: CheckClass} mapping."""

    def get_schema_extractor(self) -> Any | None:
        """Optional: schema extraction."""

    def get_reconciliation_checks(self) -> dict[str, type] | None:
        """Optional: reconciliation checks."""
```

This allows `phlo.quality` to work without hardcoded imports:

```python
# phlo/quality.py
from phlo.plugins.discovery import discover_plugins, get_quality_provider

discover_plugins()
provider = get_quality_provider("pandera")
pandera = provider.get_decorator()
```

## Related Documentation

- [Capability Primitives](../guides/capability-primitives.md) - Spec types and interfaces
- [Plugin API](plugin-api.md) - Base classes for building plugins
- [Package Documentation](../packages/index.md) - Individual package docs

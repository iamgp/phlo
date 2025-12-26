# Phlo Core Analysis - What's Missing for Lakehouse Management

## What Phlo Core IS

Based on `/home/ubuntu/phlo/phlo/src/phlo/`:

**Core = Framework + Plugin System + CLI Infrastructure**

### Current Core Capabilities:

1. **Plugin System** (`/home/ubuntu/phlo/phlo/src/phlo/plugins/base.py`):
   - `Plugin` (base class)
   - `DagsterExtensionPlugin` - Extend Dagster with assets/resources
   - `CliCommandPlugin` - Add CLI commands
   - `SourceConnectorPlugin` - Data source integrations
   - `QualityCheckPlugin` - Custom quality checks
   - `TransformationPlugin` - Data transformations
   - `ServicePlugin` - Infrastructure services

2. **CLI Infrastructure** (`/home/ubuntu/phlo/phlo/src/phlo/cli/`):
   - `main.py` - Entry point, dynamically loads plugin commands
   - `services.py` - Docker compose service management
   - `config.py` - Configuration commands
   - `plugin.py` - Plugin installation/management
   - `create_workflow.py` - Workflow scaffolding
   - `scaffold.py` - Project initialization

3. **Framework** (`/home/ubuntu/phlo/phlo/src/phlo/framework/`):
   - Workflow discovery
   - Dagster definitions building
   - Resource management

4. **Service Management** (`/home/ubuntu/phlo/phlo/src/phlo/services/`):
   - Docker compose orchestration
   - Multi-project infrastructure

5. **Discovery System** (`/home/ubuntu/phlo/phlo/src/phlo/discovery/`):
   - Plugin discovery
   - Entry point scanning
   - Registry management

## What's Missing in CORE for Lakehouse Management

### 1. NO Core Lakehouse Resource Abstraction

**Problem**: Plugins (phlo-iceberg, phlo-nessie) directly use PyIceberg/Nessie clients. Core provides no lakehouse-specific abstractions.

**Missing**:
```python
# /home/ubuntu/phlo/phlo/src/phlo/framework/lakehouse.py (DOESN'T EXIST)

class LakehouseResource(ABC):
    """Base resource for lakehouse operations"""
    @abstractmethod
    def get_table(self, name: str, ref: str = "main") -> Table: ...

    @abstractmethod
    def list_tables(self, namespace: str | None = None) -> list[str]: ...

    @abstractmethod
    def optimize_table(self, name: str, **kwargs) -> OptimizeResult: ...

class IcebergLakehouse(LakehouseResource):
    """Iceberg implementation"""
    ...
```

**Impact**: Every plugin reimplements table access. No unified API.

### 2. NO Core CLI Command Base Classes

**Problem**: Plugin CLI commands are raw Click commands. No base class for common lakehouse operations.

**Missing**:
```python
# /home/ubuntu/phlo/phlo/src/phlo/cli/lakehouse_command.py (DOESN'T EXIST)

class LakehouseCommand:
    """Base for commands that operate on lakehouse tables"""

    def __init__(self):
        self.catalog = self.get_catalog()

    @abstractmethod
    def get_catalog(self): ...

    def with_table(self, table_name: str, ref: str = "main"):
        """Decorator for table operations"""
        ...

    def with_dry_run(self, operation: Callable):
        """Add dry-run support"""
        ...
```

**Impact**: Every plugin command reimplements catalog access, dry-run logic, progress bars.

### 3. NO Core Table Operation Framework

**Problem**: No framework for common table operations (optimize, vacuum, snapshot management).

**Missing**:
```python
# /home/ubuntu/phlo/phlo/src/phlo/framework/table_operations.py (DOESN'T EXIST)

class TableOperation(ABC):
    """Base class for table maintenance operations"""

    @abstractmethod
    def plan(self, table: Table) -> OperationPlan: ...

    @abstractmethod
    def execute(self, table: Table, plan: OperationPlan) -> OperationResult: ...

    def dry_run(self, table: Table) -> OperationPlan:
        return self.plan(table)

class OptimizeOperation(TableOperation):
    def __init__(self, target_file_size: int): ...

class VacuumOperation(TableOperation):
    def __init__(self, retention_period: timedelta): ...
```

**Impact**: Table maintenance operations live in plugins, not reusable across catalog types.

### 4. NO Core Metadata/Stats Framework

**Problem**: No unified way to collect/report table statistics.

**Missing**:
```python
# /home/ubuntu/phlo/phlo/src/phlo/framework/metadata.py (DOESN'T EXIST)

class TableMetadata:
    """Unified metadata interface"""
    size_bytes: int
    row_count: int
    file_count: int
    partition_count: int
    last_modified: datetime

class MetadataCollector(ABC):
    @abstractmethod
    def collect(self, table: Table) -> TableMetadata: ...
```

**Impact**: Each plugin implements its own stats collection.

### 5. NO Core Access Control Framework

**Problem**: No built-in support for permissions, policies, audit logging.

**Missing**:
```python
# /home/ubuntu/phlo/phlo/src/phlo/framework/access_control.py (DOESN'T EXIST)

class AccessPolicy:
    """RBAC policy definition"""
    principal: str  # user or group
    resource: str   # catalog.schema.table
    permissions: set[Permission]

class AccessControlProvider(ABC):
    @abstractmethod
    def check_permission(self, principal: str, resource: str, permission: Permission) -> bool: ...

    @abstractmethod
    def grant(self, policy: AccessPolicy): ...

    @abstractmethod
    def revoke(self, principal: str, resource: str): ...

class AuditLogger(ABC):
    @abstractmethod
    def log_access(self, principal: str, resource: str, operation: str, result: str): ...
```

**Impact**: No way to add access control without creating a separate plugin.

### 6. NO Core Migration Framework

**Problem**: No abstraction for migrating from external catalogs.

**Missing**:
```python
# /home/ubuntu/phlo/phlo/src/phlo/framework/migration.py (DOESN'T EXIST)

class CatalogMigration(ABC):
    """Base for catalog migrations"""

    @abstractmethod
    def discover_tables(self) -> list[TableMetadata]: ...

    @abstractmethod
    def migrate_table(self, source_table: Any, target_catalog: Catalog): ...

    @abstractmethod
    def validate_migration(self, source: Any, target: Table) -> MigrationResult: ...

class HiveMigration(CatalogMigration): ...
class GlueMigration(CatalogMigration): ...
```

**Impact**: Migration tools must be built as standalone plugins.

### 7. NO Core Transaction/Snapshot Management

**Problem**: No core API for working with snapshots, time-travel, rollback.

**Missing**:
```python
# /home/ubuntu/phlo/phlo/src/phlo/framework/snapshots.py (DOESN'T EXIST)

class SnapshotManager:
    """Manage table snapshots"""

    def list_snapshots(self, table: Table) -> list[Snapshot]: ...
    def get_snapshot(self, table: Table, snapshot_id: int) -> Snapshot: ...
    def expire_snapshots(self, table: Table, older_than: timedelta): ...
    def rollback_to_snapshot(self, table: Table, snapshot_id: int): ...
    def create_tag(self, table: Table, tag_name: str, snapshot_id: int): ...
```

**Impact**: Snapshot operations implemented in plugins.

### 8. NO Core Schema Management Framework

**Problem**: No abstraction for schema evolution, validation, export.

**Missing**:
```python
# /home/ubuntu/phlo/phlo/src/phlo/framework/schema.py (DOESN'T EXIST)

class SchemaManager:
    """Schema evolution and management"""

    def evolve_schema(
        self,
        table: Table,
        add_columns: list[Column] = [],
        drop_columns: list[str] = [],
        rename_columns: dict[str, str] = {}
    ): ...

    def export_schema(self, table: Table, format: str) -> str:
        """Export to markdown, SQL DDL, Python, etc."""
        ...

    def diff_schemas(self, schema1: Schema, schema2: Schema) -> SchemaDiff: ...

    def validate_evolution(self, old: Schema, new: Schema) -> list[str]:
        """Return list of breaking changes"""
        ...
```

**Impact**: Schema operations scattered across plugins.

### 9. NO Core Observability Hooks

**Problem**: No built-in hooks for metrics, logging, tracing lakehouse operations.

**Missing**:
```python
# /home/ubuntu/phlo/phlo/src/phlo/framework/observability.py (DOESN'T EXIST)

class ObservabilityProvider(ABC):
    @abstractmethod
    def record_operation(
        self,
        operation: str,
        table: str,
        duration_ms: float,
        metadata: dict
    ): ...

    @abstractmethod
    def increment_counter(self, metric: str, value: int): ...

class OperationTracer:
    """Context manager for tracing operations"""
    def __enter__(self): ...
    def __exit__(self, *args):
        # Record to Prometheus, Grafana, etc.
        ...
```

**Impact**: Each plugin implements its own metrics.

### 10. NO Core CLI Testing Framework

**Problem**: No framework for testing CLI commands.

**Missing**:
```python
# /home/ubuntu/phlo/phlo/src/phlo/testing/cli.py (DOESN'T EXIST)

class CLITestCase:
    """Base for testing CLI commands"""

    def invoke_command(self, cmd: str, *args, **kwargs) -> Result: ...
    def assert_success(self, result: Result): ...
    def assert_output_contains(self, result: Result, text: str): ...

    @contextmanager
    def mock_catalog(self, tables: list[MockTable]):
        """Mock catalog for testing"""
        ...
```

**Impact**: Plugin tests duplicate CLI testing infrastructure.

---

## Summary: What CORE Needs

### Tier 1 (Critical - Framework Abstractions):
1. **LakehouseResource** - Unified catalog/table access
2. **TableOperation** - Framework for maintenance operations
3. **SchemaManager** - Schema evolution abstraction
4. **SnapshotManager** - Transaction/snapshot management

### Tier 2 (Important - Developer Experience):
5. **LakehouseCommand** - Base class for CLI commands
6. **MetadataCollector** - Unified stats collection
7. **ObservabilityProvider** - Built-in metrics/logging

### Tier 3 (Nice to Have - Advanced Features):
8. **AccessControlProvider** - RBAC framework
9. **CatalogMigration** - Migration abstraction
10. **CLITestCase** - CLI testing framework

---

## Recommendation

**DON'T** add lakehouse-specific operations to Core (that's what plugins are for).

**DO** add framework abstractions that:
- Reduce plugin boilerplate (like `@phlo_ingestion` did)
- Provide consistent APIs across plugins
- Enable reusable lakehouse patterns

**Example**: Add `LakehouseResource` to Core so plugins can focus on implementation, not reimplementing catalog access patterns.

# Feature Plan: Complete Phlo's Lakehouse Management CLI

## Executive Summary

Phlo Core has strong lakehouse capabilities but is missing critical **table maintenance operations** that are standard in Delta Lake, Iceberg, and Hudi. This plan adds the missing CLI commands to make Phlo a fully-fledged lakehouse management tool.

**What Phlo Already Has** ✅:
- Branch management (Git-like data versioning)
- Catalog operations (list, describe, history)
- Quality checks (8 types via `@phlo_quality`)
- Asset orchestration (materialize, backfill, status)
- Lineage & observability
- Schema validation

**What's Missing** ❌:
- Table maintenance (OPTIMIZE, VACUUM, compaction)
- Schema evolution CLI (add/drop/rename columns)
- Access control (RBAC, audit logs)
- Migration tools (Hive→Iceberg, Glue→Nessie)

---

## Problem Statement

### Gap 1: Table Maintenance Operations (CRITICAL)

**Problem**: Phlo has NO commands for maintaining table files. Over time:
- Small files accumulate ("small file problem"), degrading query performance
- Old snapshots consume storage indefinitely
- Orphaned files from failed operations waste storage

**Industry Standard**:
- **Delta Lake**: `OPTIMIZE`, `VACUUM`, `Z-ORDER`
- **Iceberg**: `expire_snapshots`, `rewrite_data_files`, `remove_orphan_files`
- **Hudi**: `compaction`, `clean`

**Impact**: Users cannot maintain production tables → performance degradation → storage bloat

### Gap 2: Schema Evolution CLI (IMPORTANT)

**Problem**: PyIceberg supports schema evolution programmatically, but Phlo has no CLI for it.

**Needed**:
- `phlo schema evolve` - Add/drop/rename columns
- `phlo schema export` - Export to docs, DDL, Python
- `phlo schema diff` - Compare schemas

**Impact**: Schema changes require Python code instead of simple CLI commands

### Gap 3: Access Control (IMPORTANT)

**Problem**: No permission management or audit logging

**Needed**:
- `phlo access grant/revoke` - Manage permissions
- `phlo access audit-log` - Query access events

**Impact**: Cannot enforce data governance policies

### Gap 4: Migration Tools (NICE-TO-HAVE)

**Problem**: No way to migrate from legacy catalogs

**Needed**:
- `phlo migrate from-hive` - Import from Hive metastore
- `phlo migrate from-glue` - Import from AWS Glue
- `phlo migrate convert` - Convert Parquet/Avro to Iceberg

**Impact**: High barrier to Phlo adoption for teams with existing data

---

## Proposed Solution

Add **4 new CLI command groups** to `phlo-iceberg` and new packages:

### 1. Table Maintenance (`phlo table`)

```bash
phlo table optimize <table> [--target-file-size 128MB] [--dry-run] [--ref main]
phlo table vacuum <table> [--older-than 7d] [--dry-run]
phlo table expire-snapshots <table> [--older-than 7d] [--keep-last N]
phlo table stats <table> [--metric size|rows|files|all]
```

**Implementation**:
- File: `/home/ubuntu/phlo/phlo/packages/phlo-iceberg/src/phlo_iceberg/cli_table.py`
- Uses PyIceberg's `table.rewrite_data_files()`, snapshot operations
- Dry-run shows what would be done without executing
- Progress bars for long operations (Rich library)

### 2. Schema Management (`phlo schema`)

```bash
phlo schema evolve <table> --add-column name:type [--drop-column name] [--rename old:new]
phlo schema export <table> [--format markdown|sql|python]
phlo schema diff <table1> <table2> [--ref main]
```

**Implementation**:
- File: `/home/ubuntu/phlo/phlo/packages/phlo-iceberg/src/phlo_iceberg/cli_schema.py`
- Uses PyIceberg's `table.update_schema()`
- Export to markdown for docs, SQL DDL for migrations, Python dataclasses

### 3. Access Control (`phlo access`)

```bash
phlo access grant --user <user> --role read|write|admin <resource>
phlo access revoke --user <user> <resource>
phlo access list [--resource <pattern>]
phlo access audit-log [--user <user>] [--start-time <time>]
```

**Implementation**:
- New package: `/home/ubuntu/phlo/phlo/packages/phlo-security/`
- Policy storage in PostgreSQL
- Hooks into catalog operations to enforce permissions
- Audit log table for compliance

### 4. Migration Tools (`phlo migrate`)

```bash
phlo migrate from-hive --uri thrift://host:9083 --database <db> --target <namespace>
phlo migrate from-glue --database <db> --region <region> --target <namespace>
phlo migrate convert <path> --format parquet|avro --table <name>
```

**Implementation**:
- New package: `/home/ubuntu/phlo/phlo/packages/phlo-migration/`
- Uses PyIceberg to create tables
- Validates data after migration
- Provides rollback on failure

---

## Implementation Plan

### Phase 1: Table Maintenance (Week 1-2) - CRITICAL

**Commands**:
- [ ] `phlo table optimize` - Compact small files
- [ ] `phlo table vacuum` - Remove old snapshots/orphans
- [ ] `phlo table expire-snapshots` - Clean old metadata
- [ ] `phlo table stats` - Table statistics

**Files**:
- Create: `/home/ubuntu/phlo/phlo/packages/phlo-iceberg/src/phlo_iceberg/cli_table.py`
- Update: `/home/ubuntu/phlo/phlo/packages/phlo-iceberg/src/phlo_iceberg/cli_plugin.py` (register commands)
- Tests: `/home/ubuntu/phlo/phlo/packages/phlo-iceberg/tests/test_cli_table.py`
- Docs: `/home/ubuntu/phlo/phlo/docs/reference/cli-reference.md` (add table commands section)

**Success Criteria**:
- Can compact 1000 small files into optimal sizes (100MB-1GB)
- Can expire snapshots with configurable retention
- Dry-run accurately predicts operations
- All operations work across branches (via `--ref`)

### Phase 2: Schema Management (Week 3) - IMPORTANT

**Commands**:
- [ ] `phlo schema evolve` - Add/drop/rename columns
- [ ] `phlo schema export` - Export to markdown/SQL/Python
- [ ] `phlo schema diff` - Compare schemas

**Files**:
- Create: `/home/ubuntu/phlo/phlo/packages/phlo-iceberg/src/phlo_iceberg/cli_schema.py`
- Tests: `/home/ubuntu/phlo/phlo/packages/phlo-iceberg/tests/test_cli_schema.py`

**Success Criteria**:
- Can evolve schemas without breaking queries
- Export generates usable documentation
- Diff highlights breaking changes

### Phase 3: Access Control (Week 4) - IMPORTANT

**Commands**:
- [ ] `phlo access grant/revoke`
- [ ] `phlo access list`
- [ ] `phlo access audit-log`

**Files**:
- Create: `/home/ubuntu/phlo/phlo/packages/phlo-security/` (new package)
- Files: `cli_access.py`, `rbac.py`, `audit.py`
- Schema: PostgreSQL tables for policies and audit log

**Success Criteria**:
- Can grant/revoke permissions at catalog/schema/table levels
- Audit log captures all operations
- Unauthorized operations blocked

### Phase 4: Migration Tools (Week 5) - NICE-TO-HAVE

**Commands**:
- [ ] `phlo migrate from-hive`
- [ ] `phlo migrate from-glue`
- [ ] `phlo migrate convert`

**Files**:
- Create: `/home/ubuntu/phlo/phlo/packages/phlo-migration/` (new package)

**Success Criteria**:
- Can migrate tables from Hive/Glue preserving metadata
- Can convert Parquet/Avro data to Iceberg
- Validation ensures completeness

---

## Technical Details

### Example: Table Optimize Command

```python
# /home/ubuntu/phlo/phlo/packages/phlo-iceberg/src/phlo_iceberg/cli_table.py

import click
from rich.console import Console
from rich.progress import Progress
from phlo_iceberg.catalog import get_catalog

console = Console()

@click.group(name="table")
def table_group():
    """Table maintenance operations"""
    pass

@table_group.command()
@click.argument('table_name')
@click.option('--target-file-size', default='128MB', help='Target file size after compaction')
@click.option('--dry-run', is_flag=True, help='Show what would be done')
@click.option('--ref', default='main', help='Branch reference')
def optimize(table_name: str, target_file_size: str, dry_run: bool, ref: str):
    """Compact small files to improve query performance"""
    catalog = get_catalog(ref=ref)
    table = catalog.load_table(table_name)

    # Parse target size (e.g., "128MB" → bytes)
    target_bytes = parse_size(target_file_size)

    # Find files to compact
    files = list(table.scan().plan_files())
    small_files = [f for f in files if f.file_size_in_bytes < target_bytes]

    if dry_run:
        console.print(f"[yellow]DRY RUN: Would compact {len(small_files)} files[/yellow]")
        console.print(f"Total size: {format_bytes(sum(f.file_size_in_bytes for f in small_files))}")
        return

    # Execute compaction
    with Progress() as progress:
        task = progress.add_task(f"Optimizing {table_name}", total=len(small_files))

        result = table.rewrite_data_files(
            target_file_size_bytes=target_bytes
        )

        progress.update(task, completed=len(small_files))

    console.print(f"[green]✓[/green] Compacted {result.rewritten_data_files_count} files")
    console.print(f"Reduced from {result.rewritten_bytes_count} to {result.added_bytes_count} bytes")


def parse_size(size_str: str) -> int:
    """Parse size string like '128MB' to bytes"""
    import re
    match = re.match(r'(\d+(?:\.\d+)?)(MB|GB|TB)?', size_str, re.IGNORECASE)
    if not match:
        raise ValueError(f"Invalid size: {size_str}")

    value = float(match.group(1))
    unit = (match.group(2) or 'MB').upper()

    multipliers = {'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
    return int(value * multipliers[unit])


def format_bytes(bytes_val: int) -> str:
    """Format bytes as human-readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.2f} PB"
```

### Plugin Registration

```python
# /home/ubuntu/phlo/phlo/packages/phlo-iceberg/src/phlo_iceberg/cli_plugin.py

from phlo_iceberg.cli_table import table_group
from phlo_iceberg.cli_schema import schema_group

class IcebergCLIPlugin(CLICommandPlugin):
    def get_cli_commands(self) -> list:
        return [table_group, schema_group]
```

---

## Alternative Approaches Considered

### 1. Use Spark for Table Maintenance

**Rejected**: Requires JVM, heavy dependency, not aligned with Python-first Phlo stack

### 2. Integrate with Existing CLIs (Delta CLI, Iceberg CLI)

**Rejected**: Inconsistent UX, doesn't work with Nessie catalog, vendor lock-in

### 3. Only Provide Python APIs (no CLI)

**Rejected**: Users want simple CLI commands for operations tasks, not writing Python scripts

---

## Acceptance Criteria

### Table Maintenance
- [ ] Can optimize 1000+ small files in <5 minutes
- [ ] Dry-run accurately predicts file counts and sizes
- [ ] Vacuum removes only files older than retention period
- [ ] All operations support `--ref` for branch-aware execution
- [ ] Progress indicators for long-running operations

### Schema Management
- [ ] Can add/drop/rename columns without downtime
- [ ] Export to markdown generates usable documentation
- [ ] Diff highlights breaking vs compatible changes
- [ ] Works across all Iceberg data types

### Access Control
- [ ] Can grant/revoke at catalog, schema, table levels
- [ ] Unauthorized operations blocked with clear error
- [ ] Audit log query able via CLI and SQL
- [ ] Policies persist across service restarts

### Migration Tools
- [ ] Hive/Glue migrations preserve all metadata
- [ ] Data validation ensures row count matches
- [ ] Rollback works if migration fails
- [ ] Progress tracking for large migrations

---

## Success Metrics

**Adoption**:
- 80% of teams use table maintenance monthly
- Average 30% reduction in table size after optimize
- 20% reduction in storage costs from vacuum

**Performance**:
- Query latency improves 40% after optimize
- Maintenance operations complete in <10 minutes for typical tables

**Reliability**:
- Zero data loss from maintenance operations
- 100% rollback success rate on migration failures

---

## Timeline & Resources

**Total Duration**: 5 weeks

**Team**:
- 1 Senior Engineer (Phases 1-2): 3 weeks
- 1 Mid-Level Engineer (Phases 3-4): 2 weeks

**Deliverables by Week**:
- Week 2: Table maintenance commands (optimize, vacuum)
- Week 3: Schema management commands
- Week 4: Access control package
- Week 5: Migration tools package

---

## References

### Current Phlo Capabilities
- CLI Reference: `/home/ubuntu/phlo/phlo/docs/reference/cli-reference.md`
- Branch Management: `/home/ubuntu/phlo/phlo/packages/phlo-nessie/src/phlo_nessie/cli_branch.py`
- Catalog Operations: `/home/ubuntu/phlo/phlo/packages/phlo-nessie/src/phlo_nessie/cli_catalog.py`
- Quality Package: `/home/ubuntu/phlo/phlo/packages/phlo-quality/src/phlo_quality/checks.py`

### PyIceberg APIs
- Table Operations: [https://py.iceberg.apache.org/api/](https://py.iceberg.apache.org/api/)
- Schema Evolution: [https://py.iceberg.apache.org/reference/pyiceberg/table/](https://py.iceberg.apache.org/reference/pyiceberg/table/)

### Industry References
- Delta Lake Best Practices: [https://docs.delta.io/latest/best-practices.html](https://docs.delta.io/latest/best-practices.html)
- Iceberg Maintenance: [https://iceberg.apache.org/docs/latest/maintenance/](https://iceberg.apache.org/docs/latest/maintenance/)
- Hudi CLI: [https://hudi.apache.org/docs/cli/](https://hudi.apache.org/docs/cli/)

---

**Plan Created**: 2025-12-26
**Status**: Ready for review
**Priority**: Phase 1 (Table Maintenance) is CRITICAL for production use

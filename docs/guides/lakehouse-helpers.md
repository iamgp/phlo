# Lakehouse Helper Utilities

Phlo includes a public `phlo.helpers` package for small workflow-building utilities. These helpers sit below decorators and services: they are meant for the day-to-day code users write inside ingestion, validation, transformation, publishing, and operations workflows.

They are dependency-light, importable in unit tests, and designed to compose with Phlo capabilities when a live provider is available.

## When To Use Helpers

Use helpers when a workflow needs small pieces of lakehouse logic but does not need a new plugin:

| Need | Helper examples |
| --- | --- |
| Resolve and safely display connection details | `connection_from_url`, `resolve_database`, `redact_connection_config`, `as_sling_connection`, `as_dbt_profile` |
| Work with partitions and windows | `partition_range`, `partition_scope`, `partition_where_clause`, `expected_partitions`, `build_backfill_plan` |
| Build safe read queries | `validate_read_only_sql`, `table_ref_sql`, `render_partition_predicate`, `safe_query`, `read_table` |
| Manage table writes | `ensure_lakehouse_table`, `append_parquet`, `merge_batch`, `overwrite_table` |
| Compare schemas | `normalized_schema`, `schema_from_dataframe`, `compare_schemas`, `assert_schema_compatible` |
| Add quality and reconciliation checks | `required_field_null_rules`, `unique_key_rule`, `reconcile_counts`, `reconcile_checksums`, `reconcile_key_sets` |
| Track incrementals | `resolve_watermark`, `watermark_where_clause`, `changed_keys_since` |
| Map cross-system identifiers | `build_crosswalk`, `detect_crosswalk_collisions`, `unmapped_source_ids`, `crosswalk_coverage_report` |
| Work with operational events | `event_record`, `latest_event_per_key`, `state_transition_counts`, `event_sequence_gaps` |
| Join effective-dated reference data | `reference_snapshot`, `effective_join`, `assert_no_reference_gap` |
| Handle corrections and latest views | `latest_records`, `correction_chain`, `invalidated_record_filter` |
| Track files and artifacts | `manifest_from_paths`, `verify_manifest_checksums`, `manifest_summary`, `artifact_manifest_to_table_rows` |
| Build bitemporal predicates | `BitemporalScope`, `valid_at_predicate`, `bitemporal_predicate`, `as_of_query_scope` |
| Validate state transitions | `StateTransitionRule`, `invalid_transitions`, `terminal_state_filter` |
| Validate reference contracts | `ReferenceContract`, `assert_reference_unique`, `missing_reference_keys`, `reference_coverage_report` |
| Summarize publish evidence | `collect_workflow_evidence`, `evidence_passed`, `render_evidence_table`, `publish_eligibility_report` |
| Work safely with WAP branches | `branch_for_run`, `ensure_branch`, `publish_if_checks_pass`, `write_audit_publish` |
| Emit lineage and operations metadata | `lineage_context`, `emit_input_output_lineage`, `run_timer`, `record_rows_processed` |
| Test workflow functions | `FakeRuntimeContext`, `assert_materialize_result` |

## Example: Incremental Replication Window

```python
from phlo.helpers import partition_scope, partition_where_clause
from phlo_sling import build_replication_plan

scope = partition_scope(
    start="2026-05-01",
    end="2026-05-02",
    partition_column="updated_at",
)

plan = build_replication_plan(
    ["lims.sample_results", "lims.plate_reads"],
    source_conn="LIMS",
    target_conn="PHLO_ICEBERG",
    update_key="updated_at",
    where=partition_where_clause(scope).removeprefix("WHERE "),
)
```

## Example: Schema And Write Summary

```python
from phlo.helpers import compare_schemas, merge_batch, normalized_schema

current = normalized_schema({"sample_id": "string", "ct": "float64"})
desired = normalized_schema(
    {"sample_id": "string", "ct": "float64", "assay_version": "string"}
)

plan = compare_schemas(current, desired, table_name="raw.qpcr_results")
if not plan.requires_approval:
    summary = merge_batch(
        "raw.qpcr_results",
        "/tmp/phlo/qpcr/results.parquet",
        unique_key="sample_id",
    )
```

## Package-Specific Helpers

Several packages expose helpers close to their domain:

| Package | Helpers |
| --- | --- |
| `phlo-dbt` | selector normalization, model selection from manifest, manifest table extraction, partition vars, `ensure_compiled` |
| `phlo-sling` | partition where clauses, stream-to-table names, replication plans, connection summaries |
| `phlo-iceberg` | table existence/schema loading, partition spec builders, maintenance recommendations |
| `phlo-delta` | table existence/schema loading, identity partitions, maintenance recommendations |
| `phlo-pandera` | checks from schemas, unique keys, SLA freshness, accepted values, contract-derived checks |

## Design Principles

- Helpers should be small and composable.
- Imports should not open network connections or require optional providers.
- Capability-backed helpers should use duck typing where possible.
- Helper results should be easy to put into logs, telemetry, and `MaterializeResult` metadata.
- Provider-specific helpers belong in provider packages when they need provider-native behavior.

See [Helper API](../reference/helper-api.md) for module-level reference.

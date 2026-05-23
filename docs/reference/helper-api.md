# Helper API

The helper API is a hand-written map of the public helper surface. The generated Python reference provides signatures and docstrings; this page explains where each helper family lives and which problems it solves.

## Core Module Map

| Module | Purpose | Representative symbols |
| --- | --- | --- |
| `phlo.helpers.connections` | Normalize, redact, and export database/object connection configs | `ConnectionConfig`, `connection_from_url`, `resolve_database`, `as_sling_connection`, `as_dbt_profile`, `redacted_url` |
| `phlo.helpers.partitions` | Build daily partition keys and partition scopes | `PartitionScope`, `partition_range`, `partition_scope`, `previous_partition`, `expected_partitions` |
| `phlo.helpers.sql` | Build small, safe SQL fragments | `validate_read_only_sql`, `table_ref_sql`, `quote_identifier`, `render_partition_predicate`, `partition_where_clause` |
| `phlo.helpers.tables` | Work through table-store capabilities | `parse_table_name`, `ensure_lakehouse_table`, `table_exists`, `load_table_schema`, `append_parquet`, `merge_batch` |
| `phlo.helpers.schema` | Build and compare normalized schemas | `normalized_schema`, `schema_from_dataframe`, `schema_from_arrow`, `compare_schemas`, `assert_schema_compatible` |
| `phlo.helpers.io` | Read safely and write simple parquet batches | `safe_query`, `read_table`, `read_partition`, `query_scalar`, `write_parquet_batch` |
| `phlo.helpers.storage` | Build object-store paths and local staging dirs | `ObjectStoreLayout`, `object_store_url`, `stage_path_for_run`, `temporary_staging_path` |
| `phlo.helpers.maintenance` | Represent maintenance policy and recommend actions | `MaintenancePolicy`, `maintenance_policy`, `maintenance_recommendations`, `optimize_table` |
| `phlo.helpers.quality` | Provider-neutral quality rule descriptors | `QualityRule`, `required_field_null_rules`, `unique_key_rule`, `freshness_rule_from_sla` |
| `phlo.helpers.reconciliation` | Compare counts, aggregates, checksums, key sets, and partitions | `ReconciliationResult`, `reconcile_counts`, `reconcile_aggregates`, `reconcile_checksums`, `reconcile_key_sets` |
| `phlo.helpers.incremental` | Resolve watermarks and changed entity keys | `Watermark`, `resolve_watermark`, `watermark_where_clause`, `changed_keys_since` |
| `phlo.helpers.backfills` | Build partition backfill plans | `BackfillPlan`, `build_backfill_plan`, `dry_run_backfill`, `rerun_failed_partitions` |
| `phlo.helpers.wap` | Branch naming and simple WAP orchestration | `branch_for_run`, `ensure_branch`, `publish_branch`, `publish_if_checks_pass` |
| `phlo.helpers.crosswalks` | Map source-system identifiers to canonical identifiers | `CrosswalkEntry`, `build_crosswalk`, `detect_crosswalk_collisions`, `unmapped_source_ids`, `crosswalk_coverage_report` |
| `phlo.helpers.events` | Normalize append-only operational events and state histories | `EventRecord`, `event_record`, `latest_event_per_key`, `state_transition_counts`, `event_sequence_gaps` |
| `phlo.helpers.effective` | Work with effective-dated reference data | `reference_snapshot`, `effective_join`, `assert_no_reference_gap` |
| `phlo.helpers.supersession` | Handle corrections, invalidations, and latest-record views | `supersession_key`, `latest_records`, `correction_chain` |
| `phlo.helpers.artifacts` | Build artifact/file manifests with checksums and table-ready rows | `ArtifactManifest`, `manifest_from_paths`, `verify_manifest_checksums`, `artifact_manifest_to_table_rows` |
| `phlo.helpers.bitemporal` | Build valid-time, observed-time, and as-of query predicates | `BitemporalScope`, `valid_at_predicate`, `bitemporal_predicate`, `as_of_query_scope` |
| `phlo.helpers.states` | Validate generic state transitions and terminal states | `StateTransitionRule`, `invalid_transitions`, `terminal_state_filter` |
| `phlo.helpers.references` | Describe and validate reference-data contracts | `ReferenceContract`, `assert_reference_unique`, `missing_reference_keys`, `reference_coverage_report` |
| `phlo.helpers.evidence` | Summarize workflow inputs, outputs, checks, lineage, artifacts, and decisions | `EvidenceSummary`, `collect_workflow_evidence`, `render_evidence_table` |
| `phlo.helpers.lineage` | Collect and emit input/output lineage | `LineageCollector`, `lineage_context`, `emit_input_output_lineage`, `row_id_columns` |
| `phlo.helpers.observability` | Emit metrics, logs, and timing events | `run_timer`, `emit_metric`, `record_rows_processed`, `alert_on_failure` |
| `phlo.helpers.ingestion` | Flatten records, paginate APIs, and assemble CSV batches | `PaginationState`, `api_paginated_source`, `flatten_json_records`, `records_to_dataframe` |
| `phlo.helpers.publishing` | Publish lakehouse tables, gate publishes on governance readiness, and summarize publish eligibility | `publish_table`, `publish_many`, `create_api_view`, `governance_publish_readiness`, `require_governance_ready`, `publish_eligibility_report` |
| `phlo.helpers.governance` | Build policy, masking, and audit descriptors | `classify_columns`, `mask_columns`, `policy_check`, `audit_event` |
| `phlo.helpers.errors` | Classify and wrap workflow errors | `classify_exception`, `failure_hint`, `with_phlo_errors`, `retry_transient` |
| `phlo.helpers.testing` | Minimal test context and assertions | `FakeRuntimeContext`, `assert_materialize_result` |

## Provider Package Helper Map

| Package | Module | Representative symbols |
| --- | --- | --- |
| `phlo-dbt` | `phlo_dbt.helpers` | `normalize_selectors`, `select_manifest_models`, `extract_manifest_tables`, `build_partition_vars`, `ensure_compiled` |
| `phlo-sling` | `phlo_sling.helpers` | `build_partition_where`, `table_name_from_stream`, `build_replication_plan`, `summarize_connections` |
| `phlo-iceberg` | `phlo_iceberg.helpers` | `table_exists`, `load_table_schema`, `identity_partition`, `temporal_partition`, `maintenance_recommendations` |
| `phlo-delta` | `phlo_delta.helpers` | `table_exists`, `load_table_schema`, `identity_partition`, `maintenance_recommendations` |
| `phlo-pandera` | `phlo_pandera.helpers` | `required_field_null_checks`, `unique_key_check`, `freshness_check_from_sla`, `checks_from_contract` |

## Stability Notes

Helpers are public workflow-authoring APIs. They should remain small and predictable:

- avoid import-time network calls
- avoid mandatory provider imports from core helpers
- preserve secret redaction in logs and summaries
- return serializable summaries where practical
- raise structured Phlo errors when user action can fix the issue

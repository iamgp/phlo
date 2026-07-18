-- SQLite form of the canonical report-resource identity migration.
ALTER TABLE run_event ADD COLUMN resource_identity TEXT;
ALTER TABLE run_stage ADD COLUMN resource_identity TEXT;
ALTER TABLE run_resource ADD COLUMN resource_identity TEXT;
ALTER TABLE run_lineage_edge ADD COLUMN source_resource_identity TEXT;
ALTER TABLE run_lineage_edge ADD COLUMN target_resource_identity TEXT;
ALTER TABLE run_quality_result ADD COLUMN resource_identity TEXT;
ALTER TABLE run_catalog_change ADD COLUMN resource_identity TEXT;
ALTER TABLE run_artifact ADD COLUMN resource_identity TEXT;
INSERT OR IGNORE INTO run_evidence_schema_version(version) VALUES (4);

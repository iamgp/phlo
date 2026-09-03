-- SQLite form of the additive run-evidence instrumentation migration.
ALTER TABLE run_resource ADD COLUMN schema_hash_before TEXT;
ALTER TABLE run_resource ADD COLUMN schema_hash_after TEXT;
ALTER TABLE run_resource ADD COLUMN metadata TEXT NOT NULL DEFAULT '{}';
ALTER TABLE run_catalog_change ADD COLUMN quality_decision_id TEXT;
ALTER TABLE run_lineage_edge ADD COLUMN attempt INTEGER NOT NULL DEFAULT 1 CHECK (attempt > 0);
CREATE INDEX IF NOT EXISTS idx_run_lineage_edge_project_run_attempt
    ON run_lineage_edge(project_id, run_id, attempt);
INSERT OR IGNORE INTO run_evidence_schema_version(version) VALUES (3);

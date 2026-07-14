-- Run-evidence instrumentation migration after reconciliation schema version 2 (migration 003).
ALTER TABLE phlo.run_resource ADD COLUMN IF NOT EXISTS schema_hash_before TEXT;
ALTER TABLE phlo.run_resource ADD COLUMN IF NOT EXISTS schema_hash_after TEXT;
ALTER TABLE phlo.run_resource
    ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE phlo.run_catalog_change ADD COLUMN IF NOT EXISTS quality_decision_id TEXT;
ALTER TABLE phlo.run_lineage_edge
    ADD COLUMN IF NOT EXISTS attempt INTEGER NOT NULL DEFAULT 1 CHECK (attempt > 0);

CREATE INDEX IF NOT EXISTS idx_run_lineage_edge_project_run_attempt
    ON phlo.run_lineage_edge(project_id, run_id, attempt);

INSERT INTO phlo.run_evidence_schema_version(version) VALUES (3)
ON CONFLICT (version) DO NOTHING;

-- Canonical authorization identities for report children (migration 005).
-- NULL means a historical or incomplete record; projections must never infer it.
ALTER TABLE phlo.run_event ADD COLUMN IF NOT EXISTS resource_identity JSONB;
ALTER TABLE phlo.run_stage ADD COLUMN IF NOT EXISTS resource_identity JSONB;
ALTER TABLE phlo.run_resource ADD COLUMN IF NOT EXISTS resource_identity JSONB;
ALTER TABLE phlo.run_lineage_edge ADD COLUMN IF NOT EXISTS source_resource_identity JSONB;
ALTER TABLE phlo.run_lineage_edge ADD COLUMN IF NOT EXISTS target_resource_identity JSONB;
ALTER TABLE phlo.run_quality_result ADD COLUMN IF NOT EXISTS resource_identity JSONB;
ALTER TABLE phlo.run_catalog_change ADD COLUMN IF NOT EXISTS resource_identity JSONB;
ALTER TABLE phlo.run_artifact ADD COLUMN IF NOT EXISTS resource_identity JSONB;

INSERT INTO phlo.run_evidence_schema_version(version) VALUES (4)
ON CONFLICT (version) DO NOTHING;

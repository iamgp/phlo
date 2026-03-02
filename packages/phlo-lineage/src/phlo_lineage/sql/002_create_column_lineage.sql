-- Column-level lineage tracking
CREATE TABLE IF NOT EXISTS phlo.column_lineage (
    source_asset TEXT NOT NULL,
    source_column TEXT NOT NULL,
    target_asset TEXT NOT NULL,
    target_column TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'dbt_heuristic',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (source_asset, source_column, target_asset, target_column)
);

CREATE INDEX IF NOT EXISTS idx_column_lineage_target
    ON phlo.column_lineage (target_asset, target_column);
CREATE INDEX IF NOT EXISTS idx_column_lineage_source
    ON phlo.column_lineage (source_asset, source_column);

COMMENT ON TABLE phlo.column_lineage IS 'Tracks column-level lineage between assets';

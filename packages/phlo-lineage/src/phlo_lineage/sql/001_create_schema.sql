-- Phlo Row Lineage Schema
-- Tracks row-level provenance across the data pipeline

CREATE SCHEMA IF NOT EXISTS phlo;

-- Row lineage table: stores each row's identity and parent relationships
CREATE TABLE IF NOT EXISTS phlo.row_lineage (
    row_id TEXT PRIMARY KEY,              -- ULID: unique, sortable ID
    table_name TEXT NOT NULL,             -- e.g., "bronze.dlt_user_events"
    source_type TEXT NOT NULL,            -- "dlt", "dbt", "external"
    parent_row_ids TEXT[],                -- Array of parent ULIDs (for aggregations)
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB                        -- Source info, run_id, partition, etc.
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_lineage_table ON phlo.row_lineage (table_name);
CREATE INDEX IF NOT EXISTS idx_lineage_created ON phlo.row_lineage (created_at);
CREATE INDEX IF NOT EXISTS idx_lineage_parents ON phlo.row_lineage USING GIN (parent_row_ids);

-- Row snapshot table: captures row values at ingestion time (optional, for debugging)
-- Kept separate to avoid bloating the lineage table
CREATE TABLE IF NOT EXISTS phlo.row_snapshots (
    row_id TEXT PRIMARY KEY REFERENCES phlo.row_lineage(row_id),
    snapshot JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE phlo.row_lineage IS 'Tracks row-level provenance across the Phlo pipeline';
COMMENT ON COLUMN phlo.row_lineage.row_id IS 'ULID: Universally Unique Lexicographically Sortable Identifier';
COMMENT ON COLUMN phlo.row_lineage.parent_row_ids IS 'For aggregations, contains all parent row IDs';

-- Asset lineage nodes: tracks assets seen in lineage events
CREATE TABLE IF NOT EXISTS phlo.asset_lineage_nodes (
    asset_key TEXT PRIMARY KEY,
    asset_type TEXT,
    status TEXT,
    description TEXT,
    metadata JSONB,
    tags JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Asset lineage edges: directed edges between assets (source -> target)
CREATE TABLE IF NOT EXISTS phlo.asset_lineage_edges (
    source_asset TEXT NOT NULL,
    target_asset TEXT NOT NULL,
    metadata JSONB,
    tags JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (source_asset, target_asset)
);

CREATE INDEX IF NOT EXISTS idx_asset_lineage_source
    ON phlo.asset_lineage_edges (source_asset);
CREATE INDEX IF NOT EXISTS idx_asset_lineage_target
    ON phlo.asset_lineage_edges (target_asset);

COMMENT ON TABLE phlo.asset_lineage_nodes IS 'Tracks assets observed in lineage events';
COMMENT ON TABLE phlo.asset_lineage_edges IS 'Tracks asset-level lineage edges (source -> target)';

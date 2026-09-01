# cli-surface proof

- RUN_ID: 20260901T230737Z-4270
- phlo --help lists core groups from src/phlo/cli/main.py plus plugin roots
- plugin check --json: invalid=[] valid nonempty (exit 0)
- support status --json parsed (exit 1; 1 is expected when extra packages are unexpected)
- audit tail --json empty items (exit 0)
- governance check --json (exit 0)
- plugin list --type cli --json has 17 workspace CLI plugins
- Docker: not used

## plugin-check.json (truncated)

```json
{
  "invalid": [],
  "valid_count": 76,
  "valid_head": [
    "source_connector:rest_api",
    "quality_check:freshness_check",
    "quality_check:null_check",
    "quality_check:schema_check",
    "quality_check:uniqueness_check",
    "quality_provider:pandera",
    "ingestion_provider:dlt",
    "ingestion_provider:sling"
  ]
}
```

## support.json (truncated)

```json
{
  "compatible": false,
  "production_ready": false,
  "gates": {
    "golden_path": "planned",
    "maintenance": "planned",
    "run_evidence": "planned",
    "security": "blocked",
    "upgrade_restore": "planned"
  },
  "item_count": 35
}
```

## plugin list --type cli names

```
alerts
clickhouse
clickstack
dagster
dbt
dlt
hasura
lineage
mcp
minio
nessie
openmetadata
postgres
postgrest
quality
sling
trino
```

# Feature map

Index of user-facing Phlo surfaces this skill can drive. Inventory is from `src/phlo/cli/main.py` plus `cli_command` plugins discovered in this workspace (`phlo plugin list --type cli --json`: 17 plugins). Observatory is secondary. Do not invent command names.

Default CLI-only proofs: **project-init** (`scripts/prove-project-init.sh`) and **cli-surface** (`scripts/prove-cli-surface.sh`).

## Core CLI (registered in `src/phlo/cli/main.py`)

| File | Surface | Docker? |
| --- | --- | --- |
| [cli-identity.md](cli-identity.md) | `phlo --help` / `--version` | No |
| [project-init.md](project-init.md) | `phlo init` | No |
| [doctor.md](doctor.md) | `phlo doctor` | Probes Docker; CLI runs |
| [support.md](support.md) | `phlo support status` | No |
| [test.md](test.md) | `phlo test` | `--local` avoids Docker |
| [audit.md](audit.md) | `phlo audit` | No |
| [plugin-check.md](plugin-check.md) | `phlo plugin` | `--containers` only |
| [workflow.md](workflow.md) | `phlo workflow` | No |
| [schema-migrate.md](schema-migrate.md) | `phlo schema-migrate` | Storage/migrator; often stack |
| [migrate.md](migrate.md) | `phlo migrate` | Specs local; `run` may need DB |
| [metrics.md](metrics.md) | `phlo metrics` | No for empty collector |
| [contracts.md](contracts.md) | `phlo contracts` | Needs registry DB URL |
| [config.md](config.md) | `phlo config` | No |
| [env.md](env.md) | `phlo env export` | No (writes dotenv) |
| [authz.md](authz.md) | `phlo authz` | Sync needs backends |
| [compliance.md](compliance.md) | `phlo compliance` | No for verify; pack needs inputs |
| [governance.md](governance.md) | `phlo governance` | No |
| [services-generate.md](services-generate.md) | `phlo services init` / list / add / remove / ports | Generate: no |
| [services-run.md](services-run.md) | `phlo services start` / status / stop / logs / exec / restart / reset; root `phlo logs` | **Yes** |

## Plugin CLI (`phlo.plugins.cli` in this workspace)

| File | Plugin name (`plugin list --type cli`) | Root commands | Docker? |
| --- | --- | --- | --- |
| [materialize.md](materialize.md) | `dagster` | `materialize`, `backfill`, `status`, `dev` (`logs` skipped: core already owns `phlo logs`) | Live run: **yes**. `--dry-run` on materialize/backfill: CLI |
| [catalog.md](catalog.md) | `nessie` | `catalog`, `branch` | **Yes** (Nessie) |
| [lineage.md](lineage.md) | `lineage` | `lineage` | Usually **yes** |
| [schema.md](schema.md) | `quality` | `schema`, `validate-schema`, `validate-workflow` | No for file validate |
| [dbt.md](dbt.md) | `dbt` | `dbt` | Default container; `--local` CLI |
| [sling.md](sling.md) | `sling` | `sling` | Connections often need stack |
| [mcp.md](mcp.md) | `mcp` | `mcp` | `tools`/`config`/`prompts`: no. `serve` is a process |
| [alerts.md](alerts.md) | `alerts` | `alerts` | Destinations may be external |
| [query-shells.md](query-shells.md) | `minio`, `postgres`, `trino`, `clickhouse`, `clickstack` | `minio`, `postgres`, `trino`, `clickhouse`, `clickstack` | **Yes** |
| [serving.md](serving.md) | `hasura`, `postgrest` | `hasura`, `postgrest` | **Yes** |
| [openmetadata.md](openmetadata.md) | `openmetadata` | `openmetadata` | **Yes** |
| [workflow.md](workflow.md) | `dlt` also registers `workflow` | skipped when core `workflow` already exists | — |

## Authoring and secondary UI

| File | Surface | Docker? |
| --- | --- | --- |
| [python-authoring.md](python-authoring.md) | `@phlo.ingestion` / `phlo.ingest`, `phlo.quality`, `phlo.transform.sql`, flow decorators | No to write files |
| [observatory.md](observatory.md) | Observatory UI + `phlo-api` after generated services | **Yes** |

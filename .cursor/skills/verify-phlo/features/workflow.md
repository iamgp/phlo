# Workflows

A user scaffolds and checks ingestion workflow files. Core group `phlo workflow` (`create`, `check`). The dlt plugin also registers `workflow`, but discovery **skips** it because the name is already taken.

## Sub-features

- `workflow-create` — `--type ingestion` (only choice); `--domain`, `--table`, `--unique-key` (prompted if omitted); `--cron` default `0 */1 * * *`; `--api-base-url`; `--field` repeatable; `--provider`; `--source-kind rest-api|partitioned-sql`; `--json` envelope.
- `workflow-check` — `check WORKFLOW_FILE --json` validates the file and inferred `workflows/schemas/<domain>.py`.

## How to get to it (user POV)

- From a Phlo project: `phlo workflow create --domain csv --table events --unique-key event_id --json`
- `phlo workflow check workflows/ingestion/csv/events.py --json`
- csv-batch already ships those files from `phlo init --template csv-batch`.

## Driving it with CLI

Preconditions:

- Isolated project with `phlo.yaml`. `phlo-dlt` / authoring provider installed for create.
- Drive create in `/tmp/phlo-verify-$RUN_ID`, not this repo.

- Help: `uv run --locked phlo workflow --help` → Commands `check`, `create`.
- Create JSON: `uv run --locked phlo workflow create --domain demo --table events --unique-key id --json` from the project → exit 0; envelope `data` includes created `files` and next steps; human mode prints `Created files:` and `Next steps:`.
- Check: `uv run --locked phlo workflow check workflows/ingestion/csv/events.py` on a csv-batch project → exit 0 when the decorator/schema parse; missing file → `workflow file not found`.
- Missing `workflow_validation` capability → error telling you to `uv pip install "phlo-pandera"`.

## Gotchas

- `--type` is only `ingestion`.
- Create without `--json` **prompts** for domain/table/unique-key; use flags in agents.
- `phlo validate-workflow` is the Pandera plugin command (asset file decorator check), not `workflow check`.

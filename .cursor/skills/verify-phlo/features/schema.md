# Schema and workflow validation

A user manages Pandera schemas and validates schema/workflow files. Workspace plugin `quality` (`phlo-pandera`) registers `schema`, `validate-schema`, and `validate-workflow`.

## Sub-features

- `schema-list` — `schema list --domain --format`
- `schema-show` — `schema show NAME --iceberg`
- `schema-diff` — `schema diff NAME --old --format`
- `schema-generate` — `schema generate --from --dry-run --domain --table --class --partition-date --max-records --out --update --overwrite`
- `schema-validate` — `schema validate PATH`
- `validate-schema` — root `validate-schema FILE --check-constraints --check-descriptions`
- `validate-workflow` — root `validate-workflow FILE --fix`

## How to get to it (user POV)

- From csv-batch: `phlo schema list`
- `phlo schema validate workflows/schemas/csv.py`
- `phlo validate-schema workflows/schemas/csv.py`
- `phlo validate-workflow workflows/ingestion/csv/events.py`
- `phlo schema generate --from data/events.csv --domain csv --table events --dry-run`

## Driving it with CLI

Preconditions:

- Isolated csv-batch project. `phlo-pandera` installed (workspace sync). File validation is CLI-only.

- Help: `uv run --locked phlo schema --help` → `diff`, `generate`, `list`, `show`, `validate`.
- Validate schema file: from csv-batch cwd, `uv run --locked phlo validate-schema workflows/schemas/csv.py` → exit 0 on the generated `EventsSchema`.
- Validate workflow file: `uv run --locked phlo validate-workflow workflows/ingestion/csv/events.py` → exit 0 when `@phlo.ingestion(` usage is valid.
- Generate `--dry-run` prints proposed schema without writing; omit `--out`/`--update` and confirm files unchanged.

## Gotchas

- `phlo workflow check` is the core workflow+schema pair check; these plugin commands are Pandera-oriented.
- `--fix` on `validate-workflow` mutates the asset file—only in `/tmp`.

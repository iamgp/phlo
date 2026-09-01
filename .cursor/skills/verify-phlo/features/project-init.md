# Project init

A user creates a new Phlo project directory from a named template. The CLI writes `phlo.yaml`, `pyproject.toml`, workflow packages, and template-specific starter files so the next documented steps (`uv pip install -e .`, `phlo services init`) have a real tree to work in.

## Sub-features

- `list-templates` — show installed templates (`minimal`, `csv-batch`, and provider templates).
- `init-minimal` — empty project with `phlo.yaml` and `workflows/`.
- `init-csv-batch` — documented starter: CSV events, Pandera schema, dlt ingestion asset.
- `init-json` — machine-readable envelope with `project_dir`, `template`, `generated_paths`, `next_steps`.

## How to get to it (user POV)

- `phlo init --list-templates` or `phlo init --list-templates --json`.
- `phlo init my-lakehouse` (default template `minimal`).
- `phlo init my-lakehouse --template csv-batch` (README quickstart).
- `phlo init . --force` in an existing empty-or-forced directory.
- `phlo init PATH --json` for the agent envelope.

## Driving it with CLI

Preconditions:

- Launch complete; `phlo-dlt` and `phlo-pandera` importable for `csv-batch` (true after `uv sync --locked` in this workspace).
- Disposable dir `/tmp/phlo-verify-$RUN_ID` that does not already contain a project (or pass `--force`).
- Do not run against the Phlo checkout itself.

- List templates: `uv run --locked phlo init --list-templates --json` → exit 0; JSON envelope `errors` is `[]`; `data.items` includes objects with `name` `minimal` and `csv-batch`.
- Create the documented starter: `uv run --locked phlo init "$PROJECT/my-lakehouse" --template csv-batch --json` → exit 0; `data.template` is `csv-batch`; `data.project_dir` is the absolute path; stdout is JSON only.
- Confirm onboarding files: `$PROJECT/my-lakehouse/phlo.yaml` exists and contains `name:`; `pyproject.toml` lists `phlo`, `phlo-dlt`, `phlo-pandera`; `data/events.csv` exists; `workflows/ingestion/csv/events.py` contains `@phlo.ingestion(`; `workflows/schemas/csv.py` exists.
- Human-readable path (optional second project): `uv run --locked phlo init "$PROJECT/human" --template csv-batch` → stdout includes `Successfully initialized Phlo project` and next steps `uv pip install -e .`, `phlo services init`.

Helper: `.cursor/skills/verify-phlo/scripts/prove-project-init.sh`

## Gotchas

- Unknown `--template` exits nonzero with `Unknown template` and lists available names.
- Non-empty target without `--force` exits 1 (`Directory … is not empty`).
- `csv-batch` fails if `phlo-dlt` / `phlo-pandera` are not importable (`Template 'csv-batch' requires missing package(s)`).
- Init is a mutation; authorization wrappers apply if an auth backend is configured. Default local verify has none.
- Generated `.phlo/` is **not** created by `phlo init`; that is `phlo services init`.

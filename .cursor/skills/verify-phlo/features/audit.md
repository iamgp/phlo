# Audit log

A user inspects local mutation audit records under `.phlo/audit/operations.jsonl`. Commands are read-only. Missing file yields an empty list, not a crash.

## Sub-features

- `audit-tail` — last `--limit` records (default 20, must be > 0); `--since` ISO-8601 or `15m`/`1h`/`7d`; `--json` envelope.
- `audit-query` — filter `--operation`; `--since`; `--json`.

## How to get to it (user POV)

- `phlo audit --help`
- `phlo audit tail --limit 20 --json`
- `phlo audit query --operation init --json`
- From a project cwd (path is relative `.phlo/audit/operations.jsonl`).

## Driving it with CLI

Preconditions:

- Launch complete. Isolated project cwd preferred; repo root also works (empty log).

- Tail JSON: `uv run --locked phlo audit tail --json --limit 1` → exit 0; envelope `errors: []`; `data.items` is a list (`[]` when no log); `data.since` may be null.
- Human tail: one JSON object per line.
- Bad `--since`: ClickException `--since must be ISO-8601 or a relative duration like 15m, 1h, or 7d`.
- `--limit 0` on tail: BadParameter greater than 0.

## Gotchas

- Malformed log lines are kept as `{"malformed": "<line>"}`; they are not dropped.
- This is local JSONL, not Observatory UI audit.
- Mutations (init, services, plugin install) may append records when audit is wired; do not assume a record without checking the file.
